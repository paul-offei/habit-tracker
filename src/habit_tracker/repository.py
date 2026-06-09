"""
Persistence abstraction layer.

The repository isolates all SQL/ORM logic from the rest of the application.
It accepts and returns pure domain models (Pydantic), acting as a translation layer.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from habit_tracker.habit import Habit, HabitCompletion
from habit_tracker.orm import HabitORM, CompletionORM 
from habit_tracker.period import Periodicity
from habit_tracker.status import HabitStatus


class HabitRepository:
    """
    Handles database operations for the Habit domain entity.
    """
    
    def __init__(self, session: Session):
        """
        Injects the database session to allow for easy testing and transaction management.
        """
        self.session = session

    def _to_domain(self, orm_model: HabitORM) -> Habit:
        """Helper to convert a SQLAlchemy ORM model back to a pure Pydantic Domain model."""
        
        aware_created_at = orm_model.created_at  # type: ignore
        if aware_created_at.tzinfo is None:
            aware_created_at = aware_created_at.replace(tzinfo=timezone.utc)

        return Habit(
            id=uuid.UUID(orm_model.id),                     # type: ignore
            name=orm_model.name,                            # type: ignore
            description=orm_model.description,              # type: ignore
            periodicity=Periodicity(orm_model.periodicity), # type: ignore
            status=HabitStatus(orm_model.status),           # type: ignore
            created_at=aware_created_at                     # type: ignore
        )

    def save(self, habit: Habit) -> Habit:
        """
        Persists a Habit. Performs an explicit "Upsert" (Update if exists, Insert if new)
        to completely avoid UNIQUE constraint violations across all SQL dialects.
        """
        existing_db_habit = self.session.query(HabitORM).filter(HabitORM.id == str(habit.id)).first()
        
        if existing_db_habit:
            # UPDATE PATH: Safely bypass mypy Column type checking
            existing_db_habit.name = habit.name                      # type: ignore
            existing_db_habit.description = habit.description        # type: ignore
            existing_db_habit.periodicity = habit.periodicity.value  # type: ignore
            existing_db_habit.status = habit.status.value            # type: ignore
        else:
            # INSERT PATH
            new_db_habit = HabitORM(
                id=str(habit.id),
                name=habit.name,
                description=habit.description,
                periodicity=habit.periodicity.value,
                status=habit.status.value,
                created_at=habit.created_at
            )
            self.session.add(new_db_habit)
            
        self.session.commit()
        return habit

    def get_by_id(self, habit_id: uuid.UUID) -> Optional[Habit]:
        """
        Retrieves a Habit by its unique identifier.
        """
        db_habit = self.session.query(HabitORM).filter(HabitORM.id == str(habit_id)).first()
        if not db_habit:
            return None
            
        return self._to_domain(db_habit)

    def list_all(self) -> List[Habit]:
        """
        Retrieves all habits from the database.
        """
        db_habits = self.session.query(HabitORM).all()
        return [self._to_domain(h) for h in db_habits]
    
    def record_completion(self, habit_id: uuid.UUID, completed_at: Optional[datetime] = None) -> HabitCompletion:
        """
        Records a completion event for a habit, strictly enforcing that
        only ACTIVE habits can be checked off.
        """
        habit = self.get_by_id(habit_id)
        if not habit:
            raise ValueError(f"Habit with ID {habit_id} does not exist.")

        if habit.status != HabitStatus.ACTIVE:
            raise ValueError(
                f"Cannot complete habit '{habit.name}'. Current status is '{habit.status.value}', "
                f"but must be '{HabitStatus.ACTIVE.value}'."
            )

        event_time = completed_at or datetime.now(timezone.utc)
        completion = HabitCompletion(habit_id=habit_id, completed_at=event_time)

        db_completion = CompletionORM(
            id=str(completion.id),
            habit_id=str(completion.habit_id),
            completed_at=completion.completed_at
        )
        self.session.add(db_completion)
        self.session.commit()

        return completion

    def get_completions(self, habit_id: uuid.UUID) -> List[HabitCompletion]:
        """Retrieves all completion history for a specific habit."""
        db_completions = (
            self.session.query(CompletionORM)
            .filter(CompletionORM.habit_id == str(habit_id))
            .order_by(CompletionORM.completed_at.desc())
            .all()
        )
        
        results = []
        for db_comp in db_completions:
            aware_time = db_comp.completed_at  # type: ignore
            if aware_time.tzinfo is None:
                aware_time = aware_time.replace(tzinfo=timezone.utc)
                
            results.append(HabitCompletion(
                id=uuid.UUID(db_comp.id),              # type: ignore
                habit_id=uuid.UUID(db_comp.habit_id),  # type: ignore
                completed_at=aware_time                # type: ignore
            ))
        return results
    
    def update_habit(
        self, 
        habit_id: uuid.UUID, 
        name: Optional[str] = None, 
        description: Optional[str] = None, 
        status: Optional[HabitStatus] = None
    ) -> Habit:
        """
        Updates an existing habit's properties. 
        Enforces functional immutability by creating a new entity state.
        """
        habit = self.get_by_id(habit_id)
        if not habit:
            raise ValueError(f"Habit with ID {habit_id} does not exist.")

        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if status is not None:
            updates["status"] = status

        if not updates:
            return habit

        updated_habit = habit.model_copy(update=updates)
        return self.save(updated_habit)

    def delete_habit(self, habit_id: uuid.UUID) -> Habit:
        """
        Smart Deletion Strategy:
        - If the habit has NO completions, it is marked as DELETED.
        - If the habit HAS completions, it is marked as ARCHIVED to preserve history.
        """
        habit = self.get_by_id(habit_id)
        if not habit:
            raise ValueError(f"Habit with ID {habit_id} does not exist.")

        history = self.get_completions(habit_id)
        
        if len(history) > 0:
            new_status = HabitStatus.ARCHIVED
        else:
            new_status = HabitStatus.DELETED

        deleted_habit = habit.model_copy(update={"status": new_status})
        return self.save(deleted_habit)

    def get_all_completions_with_habits(self) -> list[tuple[HabitCompletion, Habit]]:
        """
        Retrieves a master log of all completions across the entire database, 
        joined with their parent Habit to avoid N+1 query performance issues.
        Sorted newest-first.
        """
        results = (
            self.session.query(CompletionORM, HabitORM)
            .join(HabitORM, CompletionORM.habit_id == HabitORM.id)
            .order_by(CompletionORM.completed_at.desc())
            .all()
        )

        mapped_results = []
        for db_comp, db_habit in results:
            habit = self._to_domain(db_habit)
            
            aware_time = db_comp.completed_at  # type: ignore
            if aware_time.tzinfo is None:
                aware_time = aware_time.replace(tzinfo=timezone.utc)
                
            completion = HabitCompletion(
                id=uuid.UUID(db_comp.id),             # type: ignore
                habit_id=uuid.UUID(db_comp.habit_id), # type: ignore
                completed_at=aware_time               
            )
            
            mapped_results.append((completion, habit))
            
        return mapped_results