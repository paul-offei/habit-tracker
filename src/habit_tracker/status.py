"""
Lifecycle and state management domain logic.

Defines the allowed statuses for a habit, enabling soft-deletion
and historical tracking without destroying analytics data.
"""

from enum import Enum


class HabitStatus(str, Enum):
    """
    Represents the current lifecycle state of a habit.
    Inheriting from str allows for native JSON and SQL serialization.
    """
    ACTIVE = "active"       # Currently tracked
    PAUSED = "paused"       # Temporarily suspended
    ARCHIVED = "archived"   # Permanently stopped but preserved for history
    DELETED = "deleted"     # Soft removed (hidden from main UI)