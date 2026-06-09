"""
Integration tests for Habit mutations (Update and Smart-Delete).
Ensures that immutability is preserved and historical data dictates deletion behavior.
"""

import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from habit_tracker.database import Base
from habit_tracker.habit import Habit
from habit_tracker.period import Periodicity
from habit_tracker.status import HabitStatus
from habit_tracker.repository import HabitRepository


@pytest.fixture
def repository():
    """Provides a fresh, isolated in-memory SQLite repository."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    repo = HabitRepository(session=session)
    yield repo
    
    session.close()
    Base.metadata.drop_all(bind=engine)


# =====================================================================
# UPDATE FEATURE TESTS
# =====================================================================

def test_update_habit_name_and_description(repository: HabitRepository):
    """Verifies that a user can edit the text fields of a habit."""
    habit = Habit(name="Old Name", description="Old Desc", periodicity=Periodicity.DAILY)
    repository.save(habit)

    updated_habit = repository.update_habit(
        habit_id=habit.id,
        name="New Name",
        description="New Desc"
    )

    assert updated_habit.name == "New Name"
    assert updated_habit.description == "New Desc"
    assert updated_habit.id == habit.id  # Identity remains unchanged

    # Verify persistence
    fetched = repository.get_by_id(habit.id)
    assert fetched is not None
    assert fetched.name == "New Name"


def test_update_habit_status_to_paused(repository: HabitRepository):
    """Verifies that a user can explicitly pause an active habit."""
    habit = Habit(name="Read", periodicity=Periodicity.DAILY, status=HabitStatus.ACTIVE)
    repository.save(habit)

    updated_habit = repository.update_habit(
        habit_id=habit.id,
        status=HabitStatus.PAUSED
    )

    assert updated_habit.status == HabitStatus.PAUSED
    
    # Verify persistence
    fetched = repository.get_by_id(habit.id)
    assert fetched is not None
    assert fetched.status == HabitStatus.PAUSED


def test_update_nonexistent_habit_raises_error(repository: HabitRepository):
    """Ensures updating a fake ID raises a clear domain exception."""
    fake_id = uuid.uuid4()
    with pytest.raises(ValueError, match="does not exist"):
        repository.update_habit(habit_id=fake_id, name="Ghost")


# =====================================================================
# SMART DELETE FEATURE TESTS
# =====================================================================

def test_delete_habit_without_completions_becomes_deleted(repository: HabitRepository):
    """
    Business Rule: Deleting a habit with zero check-offs 
    changes its status to DELETED.
    """
    habit = Habit(name="Never Started", periodicity=Periodicity.DAILY)
    repository.save(habit)

    # Execute delete
    deleted_habit = repository.delete_habit(habit.id)

    assert deleted_habit.status == HabitStatus.DELETED
    
    # Verify persistence
    fetched = repository.get_by_id(habit.id)
    assert fetched is not None
    assert fetched.status == HabitStatus.DELETED


def test_delete_habit_with_completions_becomes_archived(repository: HabitRepository):
    """
    Business Rule: Deleting a habit that has been checked off at least once 
    changes its status to ARCHIVED to protect analytics history.
    """
    habit = Habit(name="Worked Out Once", periodicity=Periodicity.DAILY)
    repository.save(habit)

    # Record a completion
    repository.record_completion(habit.id)

    # Execute delete
    deleted_habit = repository.delete_habit(habit.id)

    assert deleted_habit.status == HabitStatus.ARCHIVED
    
    # Verify persistence
    fetched = repository.get_by_id(habit.id)
    assert fetched is not None
    assert fetched.status == HabitStatus.ARCHIVED


def test_delete_nonexistent_habit_raises_error(repository: HabitRepository):
    """Ensures deleting a fake ID raises a clear domain exception."""
    fake_id = uuid.uuid4()
    with pytest.raises(ValueError, match="does not exist"):
        repository.delete_habit(habit_id=fake_id)