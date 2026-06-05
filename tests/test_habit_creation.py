"""
Unit tests for the Habit domain model.

Utilizes pytest parameterization to rigorously test entity creation
across various real-world scenarios and periodicities without code duplication.
"""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from habit_tracker.habit import Habit
from habit_tracker.period import Periodicity


# Table-driven test data using the provided catalog examples
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

@pytest.mark.parametrize("name, description, periodicity", HABIT_EXAMPLES)
def test_create_valid_habits(name: str, description: str, periodicity: Periodicity):
    """
    Tests the creation of 10 distinct real-world habits, ensuring that
    all provided fields map correctly and auto-generated fields instantiate properly.
    """
    habit = Habit(
        name=name,
        description=description,
        periodicity=periodicity
    )

    # Verify explicitly provided fields
    assert habit.name == name
    assert habit.description == description
    assert habit.periodicity == periodicity

    # Verify auto-generated fields
    assert isinstance(habit.id, uuid.UUID)
    assert isinstance(habit.created_at, datetime)
    assert habit.created_at.tzinfo == timezone.utc


def test_habit_optional_description():
    """
    Ensures that a habit can be created without a description, 
    defaulting to an empty string.
    """
    habit = Habit(
        name="Read a Book",
        periodicity=Periodicity.DAILY
    )
    assert habit.description == ""


def test_habit_requires_valid_name_length():
    """
    Ensures domain constraints prevent empty names.
    """
    with pytest.raises(ValidationError) as exc_info:
        Habit(name="", periodicity=Periodicity.DAILY)
    
    assert "String should have at least 1 character" in str(exc_info.value)


def test_habit_name_length_limit():
    """
    Ensures that excessively long names are rejected to protect database sizing.
    The limit is currently 100 characters.
    """
    long_name = "A" * 101
    with pytest.raises(ValidationError) as exc_info:
        Habit(name=long_name, periodicity=Periodicity.DAILY)
        
    assert "String should have at most 100 characters" in str(exc_info.value)


def test_habit_immutability():
    """
    Verifies that the Habit entity cannot be mutated in place,
    enforcing functional updates across the architecture.
    """
    habit = Habit(name="Read", periodicity=Periodicity.DAILY)

    with pytest.raises(ValidationError) as exc_info:
        habit.name = "Read More"  # type: ignore
        
    assert "Instance is frozen" in str(exc_info.value)


def test_habit_functional_update():
    """
    Demonstrates the correct Domain-Driven Design (DDD) approach to updating a frozen Pydantic model.
    """
    original_habit = Habit(name="Run", periodicity=Periodicity.DAILY)
    
    # Simulate an update (e.g., user changes the frequency to weekly)
    updated_habit = original_habit.model_copy(update={"periodicity": Periodicity.WEEKLY})
    
    assert original_habit.periodicity == Periodicity.DAILY
    assert updated_habit.periodicity == Periodicity.WEEKLY
    assert original_habit.id == updated_habit.id  # The entity identity remains the same


