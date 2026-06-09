"""
Functional Analytics Module.

This module utilizes the Functional Programming (FP) paradigm to calculate
statistics, streaks, and filter entities. All functions are pure, deterministic,
and strictly avoid side-effects (e.g., no database calls or state mutations).
"""

import uuid
from datetime import datetime, timedelta
from functools import reduce
from typing import List, Dict
from habit_tracker.habit import Habit, HabitCompletion
from habit_tracker.period import Periodicity, get_period_boundaries
from habit_tracker.status import HabitStatus


# =====================================================================
# FEATURE 1 & 2: PURE FILTERING FUNCTIONS
# =====================================================================

def filter_by_status(habits: List[Habit], status: HabitStatus) -> List[Habit]:
    """
    Generic pure function to filter a list of habits by any lifecycle status.
    """
    return list(filter(lambda h: h.status == status, habits))


def filter_active_habits(habits: List[Habit]) -> List[Habit]:
    """Returns a list of all currently tracked (ACTIVE) habits."""
    return filter_by_status(habits, HabitStatus.ACTIVE)


def filter_paused_habits(habits: List[Habit]) -> List[Habit]:
    """Returns a list of all temporarily suspended (PAUSED) habits."""
    return filter_by_status(habits, HabitStatus.PAUSED)


def filter_archived_habits(habits: List[Habit]) -> List[Habit]:
    """Returns a list of all permanently stopped but preserved (ARCHIVED) habits."""
    return filter_by_status(habits, HabitStatus.ARCHIVED)


def filter_deleted_habits(habits: List[Habit]) -> List[Habit]:
    """Returns a list of all soft-removed (DELETED) habits."""
    return filter_by_status(habits, HabitStatus.DELETED)


def filter_by_periodicity(habits: List[Habit], periodicity: Periodicity) -> List[Habit]:
    """
    Returns a list of all habits matching the given periodicity.
    Uses pure FP filtering.
    """
    return list(filter(lambda h: h.periodicity == periodicity, habits))


# =====================================================================
# STREAK CALCULATION HELPER FUNCTIONS (PURE)
# =====================================================================

def _get_period_start(period: Periodicity, current_time: datetime) -> datetime:
    """Extracts the deterministic start boundary for a given timestamp."""
    start, _ = get_period_boundaries(period, current_time)
    return start


def _get_previous_period_start(period: Periodicity, current_period_start: datetime) -> datetime:
    """
    Functionally determines the start of the immediately preceding chronological period.
    By subtracting 1 microsecond, we traverse backwards safely regardless of leap years or month lengths.
    """
    time_in_prev_period = current_period_start - timedelta(microseconds=1)
    return _get_period_start(period, time_in_prev_period)


# =====================================================================
# FEATURE 3 & 4: LONG RUN STREAK FUNCTIONS
# =====================================================================

def calculate_longest_streak(habit: Habit, completions: List[HabitCompletion]) -> int:
    """
    Calculates the longest consecutive completion streak for a given habit.
    
    Algorithm:
    1. Map all completion timestamps to their normalized period boundaries.
    2. Remove duplicates (if a user completed a task twice in one day, it counts once).
    3. Sort the unique periods descending (newest to oldest).
    4. Fold (reduce) over the timeline to calculate the max streak.
    """
    if not completions:
        return 0

    # 1 & 2: Map to period starts and enforce uniqueness via set comprehensions
    normalized_starts = {
        _get_period_start(habit.periodicity, c.completed_at) for c in completions
    }
    
    # 3: Sort descending
    sorted_unique_starts = sorted(list(normalized_starts), reverse=True)

    # 4: Pure Reducer function for folding the timeline
    def streak_reducer(acc: tuple[int, int, datetime | None], current_start: datetime) -> tuple[int, int, datetime | None]:
        current_streak, max_streak, expected_start = acc

        # Initialization step for the very first element
        if expected_start is None:
            return (1, 1, _get_previous_period_start(habit.periodicity, current_start))

        # Contiguous period match
        if current_start == expected_start:
            new_streak = current_streak + 1
            return (
                new_streak,
                max(max_streak, new_streak),
                _get_previous_period_start(habit.periodicity, current_start)
            )
        
        # Streak broken, reset current streak count to 1
        return (
            1,
            max_streak,
            _get_previous_period_start(habit.periodicity, current_start)
        )

    # Execute the functional fold
    # Initial accumulator state: (current_streak, max_streak, expected_next_start)
    initial_state: tuple[int, int, datetime | None] = (0, 0, None)
    final_state = reduce(streak_reducer, sorted_unique_starts, initial_state)
    
    # Extract the max_streak from the tuple
    _, max_streak, _ = final_state
    return max_streak


def calculate_longest_streak_overall(habits: List[Habit], completions_map: Dict[uuid.UUID, List[HabitCompletion]]) -> int:
    """
    Returns the longest run streak out of all defined habits.
    Maps the `calculate_longest_streak` function over the entire collection.
    """
    if not habits:
        return 0

    # Map the streak calculation over all habits
    streaks = map(
        lambda h: calculate_longest_streak(h, completions_map.get(h.id, [])), 
        habits
    )
    
    # Reduce to maximum value
    return max(streaks, default=0)