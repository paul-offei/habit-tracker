"""
Integration tests for the HabitRepository.

Utilizes an in-memory SQLite database and parameterized real-world data
to ensure the repository logic correctly maps pure domain entities 
to SQL tables and back, preserving strict data quality for downstream analytics.
"""

import uuid
import pytest
from datetime import timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from habit_tracker.database import Base
from habit_tracker.habit import Habit
from habit_tracker.period import Periodicity
from habit_tracker.repository import HabitRepository
from habit_tracker.status import HabitStatus

# Table-driven test data using the 10 catalog examples
HABIT_EXAMPLES = [
    ("Drink Water", "Drink 1 glass of water", Periodicity.HOURLY),
    ("Morning Exercise", "Complete a workout session", Periodicity.DAILY),
    ("Meal Prep", "Prepare healthy meals for the week", Periodicity.WEEKLY),
    ("Pay Bills", "Pay recurring bills", Periodicity.MONTHLY),
    ("Quarterly Planning", "Plan next 3 months", Periodicity.QUARTERLY),
    ("Health Screening", "Perform medical checkup", Periodicity.YEARLY),
    ("Spring Cleaning", "Deep clean entire house", Periodicity.SPRING),
    ("Summer Relaxation", "Spend intentional time relaxing", Periodicity.SUMMER),
    ("Autumn Hiking", "Go on nature hikes", Periodicity.AUTUMN),
    ("Winter Indoor Cardio", "Maintain indoor fitness routine", Periodicity.WINTER),
]


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


@pytest.mark.parametrize("name, description, periodicity", HABIT_EXAMPLES)
def test_save_and_retrieve_all_periodicities(
    repository: HabitRepository, 
    name: str, 
    description: str, 
    periodicity: Periodicity
):
    """
    Tests the full lifecycle of translating a domain model to the DB and back
    across all 10 real-world scenarios. Validates the ORM handles Enums and Strings flawlessly.
    """
    # 1. Create a pure domain model
    original_habit = Habit(
        name=name,
        description=description,
        periodicity=periodicity
    )

    # 2. Save it via repository
    repository.save(original_habit)

    # 3. Retrieve it
    fetched_habit = repository.get_by_id(original_habit.id)

    # 4. Assert domain rules and state survived the round trip
    assert fetched_habit is not None
    assert fetched_habit.id == original_habit.id
    assert fetched_habit.name == name
    assert fetched_habit.description == description
    assert fetched_habit.periodicity == periodicity
    assert fetched_habit.status == HabitStatus.ACTIVE
    
    # Ensure timezone awareness survived the SQLite translation
    assert fetched_habit.created_at == original_habit.created_at
    assert fetched_habit.created_at.tzinfo == timezone.utc


def test_get_nonexistent_habit(repository: HabitRepository):
    """
    Ensures the repository safely returns None for missing records.
    """
    fake_id = uuid.uuid4()
    assert repository.get_by_id(fake_id) is None


def test_list_all_habits_bulk(repository: HabitRepository):
    """
    Tests bulk insertion and retrieval of domain models using all 10 examples.
    """
    # Insert all 10 examples into the database
    for name, description, periodicity in HABIT_EXAMPLES:
        habit = Habit(name=name, description=description, periodicity=periodicity)
        repository.save(habit)

    # Retrieve them all
    all_habits = repository.list_all()

    # Verify the count
    assert len(all_habits) == 10
    
    # Verify specific elements exist in the returned dataset
    names = [h.name for h in all_habits]
    assert "Drink Water" in names
    assert "Winter Indoor Cardio" in names
    assert "Quarterly Planning" in names