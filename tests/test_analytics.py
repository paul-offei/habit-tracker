"""
Unit tests for the Functional Analytics Module.

Because the analytics module is strictly pure and free of side-effects,
we test it using lightweight, in-memory Pydantic objects. No database 
connections are required, ensuring ultra-fast and isolated test runs.
"""

from datetime import datetime, timedelta, timezone
import pytest

from habit_tracker.habit import Habit, HabitCompletion
from habit_tracker.period import Periodicity
from habit_tracker.status import HabitStatus
from habit_tracker.analytics import (
    filter_active_habits,
    filter_archived_habits,
    filter_by_periodicity,
    calculate_longest_streak,
    calculate_longest_streak_overall,
    filter_by_status,
    filter_deleted_habits,
    filter_paused_habits
)


@pytest.fixture
def sample_habits() -> list[Habit]:
    """
    Provides a diverse list of pure Habit models, ensuring every single 
    lifecycle status is represented for thorough filter testing.
    """
    return [
        Habit(name="Morking Workout", periodicity=Periodicity.DAILY, status=HabitStatus.ACTIVE),
        Habit(name="Reading Exercise", periodicity=Periodicity.WEEKLY, status=HabitStatus.ACTIVE),
        Habit(name="Cooking Challenge", periodicity=Periodicity.DAILY, status=HabitStatus.PAUSED),
        Habit(name="Holiday Travel", periodicity=Periodicity.MONTHLY, status=HabitStatus.ARCHIVED),
        Habit(name="Birthday Celebration", periodicity=Periodicity.YEARLY, status=HabitStatus.DELETED),
    ]

# =====================================================================
# FEATURE 1 & 2 TESTS: STATUS AND PERIODICITY FILTERING
# =====================================================================

def test_filter_active_habits(sample_habits: list[Habit]):
    """Verifies that only ACTIVE habits are retained."""
    results = filter_active_habits(sample_habits)
    assert len(results) == 2
    assert {h.status for h in results} == {HabitStatus.ACTIVE}


def test_filter_paused_habits(sample_habits: list[Habit]):
    """Verifies that only PAUSED habits are retained."""
    results = filter_paused_habits(sample_habits)
    assert len(results) == 1
    assert results[0].status == HabitStatus.PAUSED


def test_filter_archived_habits(sample_habits: list[Habit]):
    """Verifies that only ARCHIVED habits are retained."""
    results = filter_archived_habits(sample_habits)
    assert len(results) == 1
    assert results[0].status == HabitStatus.ARCHIVED


def test_filter_deleted_habits(sample_habits: list[Habit]):
    """Verifies that only DELETED habits are retained."""
    results = filter_deleted_habits(sample_habits)
    assert len(results) == 1
    assert results[0].status == HabitStatus.DELETED


def test_filter_by_status_generic(sample_habits: list[Habit]):
    """Verifies the underlying generic functional filter operates correctly."""
    results = filter_by_status(sample_habits, HabitStatus.ACTIVE)
    assert len(results) == 2


def test_filter_by_periodicity(sample_habits: list[Habit]):
    """Verifies correct functional filtering by Enum."""
    daily_habits = filter_by_periodicity(sample_habits, Periodicity.DAILY)
    assert len(daily_habits) == 2
    assert {h.periodicity for h in daily_habits} == {Periodicity.DAILY}

# =====================================================================
# FEATURE 3: LONGEST STREAK FOR A GIVEN HABIT
# =====================================================================

def test_calculate_longest_streak_perfect_run():
    """Tests a flawless contiguous streak of 5 days."""
    habit = Habit(name="Read", periodicity=Periodicity.DAILY)
    anchor_date = datetime(2026, 6, 8, 12, 0, 0, tzinfo=timezone.utc)
    
    # Generate 5 back-to-back days of HabitCompletions
    HabitCompletions = [
        HabitCompletion(habit_id=habit.id, completed_at=anchor_date - timedelta(days=i))
        for i in range(5)
    ]
    
    streak = calculate_longest_streak(habit, HabitCompletions)
    assert streak == 5


def test_calculate_longest_streak_with_break():
    """
    Tests a timeline with a missed period.
    Timeline: 3 days complete -> 1 day missed -> 4 days complete.
    The max streak should be 4.
    """
    habit = Habit(name="Workout", periodicity=Periodicity.DAILY)
    anchor_date = datetime(2026, 6, 8, 12, 0, 0, tzinfo=timezone.utc)
    
    HabitCompletions = [
        # Recent streak of 3
        HabitCompletion(habit_id=habit.id, completed_at=anchor_date),
        HabitCompletion(habit_id=habit.id, completed_at=anchor_date - timedelta(days=1)),
        HabitCompletion(habit_id=habit.id, completed_at=anchor_date - timedelta(days=2)),
        
        # MISSED DAY 3
        
        # Older streak of 4
        HabitCompletion(habit_id=habit.id, completed_at=anchor_date - timedelta(days=4)),
        HabitCompletion(habit_id=habit.id, completed_at=anchor_date - timedelta(days=5)),
        HabitCompletion(habit_id=habit.id, completed_at=anchor_date - timedelta(days=6)),
        HabitCompletion(habit_id=habit.id, completed_at=anchor_date - timedelta(days=7)),
    ]
    
    streak = calculate_longest_streak(habit, HabitCompletions)
    assert streak == 4


def test_calculate_longest_streak_duplicate_HabitCompletions():
    """
    Ensures that logging multiple HabitCompletions in the same period 
    does not artificially inflate the streak count.
    """
    habit = Habit(name="Vitamins", periodicity=Periodicity.DAILY)
    anchor_date = datetime(2026, 6, 8, 12, 0, 0, tzinfo=timezone.utc)
    
    HabitCompletions = [
        # Two HabitCompletions on the same day (e.g., morning and night)
        HabitCompletion(habit_id=habit.id, completed_at=anchor_date),
        HabitCompletion(habit_id=habit.id, completed_at=anchor_date - timedelta(hours=2)),
        
        # One HabitCompletion the day before
        HabitCompletion(habit_id=habit.id, completed_at=anchor_date - timedelta(days=1)),
    ]
    
    streak = calculate_longest_streak(habit, HabitCompletions)
    # The streak spans 2 distinct days, so the result must be 2
    assert streak == 2


def test_calculate_longest_streak_no_data():
    """Ensures empty datasets are handled gracefully by the reducer."""
    habit = Habit(name="Empty", periodicity=Periodicity.DAILY)
    assert calculate_longest_streak(habit, []) == 0


# =====================================================================
# FEATURE 4: OVERALL LONGEST STREAK
# =====================================================================

def test_calculate_longest_streak_overall():
    """
    Verifies the mapping function correctly identifies the absolute highest
    streak across multiple distinct habits.
    """
    anchor_date = datetime(2026, 6, 8, 12, 0, 0, tzinfo=timezone.utc)
    
    # Habit A: Streak of 2
    habit_a = Habit(name="Habit A", periodicity=Periodicity.DAILY)
    comps_a = [
        HabitCompletion(habit_id=habit_a.id, completed_at=anchor_date - timedelta(days=i))
        for i in range(2)
    ]
    
    # Habit B: Streak of 7 (The Winner)
    habit_b = Habit(name="Habit B", periodicity=Periodicity.DAILY)
    comps_b = [
        HabitCompletion(habit_id=habit_b.id, completed_at=anchor_date - timedelta(days=i))
        for i in range(7)
    ]
    
    # Habit C: Streak of 0
    habit_c = Habit(name="Habit C", periodicity=Periodicity.DAILY)
    comps_c = []
    
    # Build the required data structures
    habits = [habit_a, habit_b, habit_c]
    HabitCompletions_map = {
        habit_a.id: comps_a,
        habit_b.id: comps_b,
        habit_c.id: comps_c,
    }
    
    overall_max = calculate_longest_streak_overall(habits, HabitCompletions_map)
    assert overall_max == 7