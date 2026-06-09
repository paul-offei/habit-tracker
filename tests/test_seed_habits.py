"""
Unit tests for the template habit loading functionality.
Ensures bulk operations successfully persist via the repository layer.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from habit_tracker.database import Base
from habit_tracker.repository import HabitRepository
from habit_tracker.seed_habits import load_template_habits, PREDEFINED_HABITS


@pytest.fixture
def empty_repository():
    """Provides a totally clean, in-memory SQLite repository."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    repo = HabitRepository(session)
    yield repo
    
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_load_template_habits_persists_all_records(empty_repository: HabitRepository):
    """
    Verifies that the exact number of defined habits are successfully 
    inserted into a fresh database.
    """
    # Act
    load_template_habits(empty_repository)
    
    # Assert
    saved_habits = empty_repository.list_all()
    assert len(saved_habits) == len(PREDEFINED_HABITS)


def test_load_template_habits_maps_data_correctly(empty_repository: HabitRepository):
    """
    Verifies that the domain models are constructed correctly from the dictionary,
    checking specific properties like Enums and descriptions.
    """
    # Act
    load_template_habits(empty_repository)
    saved_habits = empty_repository.list_all()
    
    # Assert
    # Grab "Practice Coding" to ensure it mapped correctly
    coding_habit = next(h for h in saved_habits if h.name == "Practice Coding")
    assert coding_habit is not None
    assert coding_habit.description == "Solve programming exercises"
    assert coding_habit.periodicity.value == "daily"
    
    # Ensure no completions were magically generated
    completions = empty_repository.get_completions(coding_habit.id)
    assert len(completions) == 0