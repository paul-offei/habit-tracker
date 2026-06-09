"""
Integration tests for the HabitRepository.

Utilizes an in-memory SQLite database to ensure the repository logic
correctly maps pure domain entities to SQL tables and back.
"""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from habit_tracker.database import Base
from habit_tracker.habit import Habit, HabitCompletion
from habit_tracker.period import Periodicity
from habit_tracker.status import HabitStatus
from habit_tracker.repository import HabitRepository


@pytest.fixture
def db_session():
    """
    Creates a fresh, isolated in-memory SQLite database for every test.
    """
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def repository(db_session):
    """Provides an instance of the repository with the injected test session."""
    return HabitRepository(session=db_session)


def test_save_and_retrieve_habit(repository: HabitRepository):
    """
    Tests the full lifecycle of translating a domain model to the DB and back.
    """
    # 1. Create a pure domain model
    original_habit = Habit(
        name="Learn SQLAlchemy",
        description="Study the ORM layer",
        periodicity=Periodicity.DAILY
    )

    # 2. Save it via repository
    repository.save(original_habit)

    # 3. Retrieve it
    fetched_habit = repository.get_by_id(original_habit.id)

    # 4. Assert domain rules and state survived the round trip
    assert fetched_habit is not None
    assert fetched_habit.id == original_habit.id
    assert fetched_habit.name == "Learn SQLAlchemy"
    assert fetched_habit.description == "Study the ORM layer"
    assert fetched_habit.periodicity == Periodicity.DAILY
    assert fetched_habit.created_at == original_habit.created_at


def test_get_nonexistent_habit(repository: HabitRepository):
    """
    Ensures the repository safely returns None for missing records.
    """
    import uuid
    fake_id = uuid.uuid4()
    assert repository.get_by_id(fake_id) is None


def test_list_all_habits(repository: HabitRepository):
    """
    Tests bulk retrieval of domain models.
    """
    habit1 = Habit(name="Drink Water", periodicity=Periodicity.HOURLY)
    habit2 = Habit(name="Read Book", periodicity=Periodicity.DAILY)

    repository.save(habit1)
    repository.save(habit2)

    all_habits = repository.list_all()

    assert len(all_habits) == 2
    names = [h.name for h in all_habits]
    assert "Drink Water" in names
    assert "Read Book" in names


def test_record_successful_completion(repository: HabitRepository):
    """Verifies that an active habit can be completed and retrieved."""
    # Setup: Create and save an active habit
    habit = Habit(name="Workout", periodicity=Periodicity.DAILY)
    repository.save(habit)

    # Action: Complete the habit
    completion = repository.record_completion(habit.id)

    # Assert: Ensure completion exists and is mapped correctly
    assert isinstance(completion, HabitCompletion)
    assert completion.habit_id == habit.id
    
    # Verify retrieval
    history = repository.get_completions(habit.id)
    assert len(history) == 1
    assert history[0].id == completion.id

def test_cannot_complete_inactive_habit(repository: HabitRepository):
    """
    Domain Rule Test: Ensures the repository blocks completion 
    if the habit is not strictly ACTIVE.
    """
    # Setup: Create a paused habit
    habit = Habit(
        name="Study Spanish", 
        periodicity=Periodicity.DAILY, 
        status=HabitStatus.PAUSED
    )
    repository.save(habit)

    # Action & Assert: Attempting to complete it must raise a ValueError
    with pytest.raises(ValueError) as exc_info:
        repository.record_completion(habit.id)

    assert "Cannot complete habit" in str(exc_info.value)
    assert "paused" in str(exc_info.value)

def test_cannot_complete_nonexistent_habit(repository: HabitRepository):
    """Ensures referential integrity checks work before saving."""
    fake_id = uuid.uuid4()
    
    with pytest.raises(ValueError) as exc_info:
        repository.record_completion(fake_id)
        
    assert "does not exist" in str(exc_info.value)