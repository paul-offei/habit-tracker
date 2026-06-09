"""
Domain models for the Habit Tracker application.

This module defines the core business entities using Pydantic.
It handles data validation, type coercion, and domain rule enforcement.
It strictly avoids database operations or UI rendering logic.
"""

import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from habit_tracker.period import Periodicity 
from habit_tracker.status import HabitStatus


class Habit(BaseModel):
    """
    Core Domain Entity representing a tracked habit.
    """
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique identifier for the habit."
    )
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="The display name of the habit."
    )
    description: str = Field(
        default="",
        max_length=500,
        description="Optional detailed explanation of the task."
    )
    periodicity: Periodicity = Field(
        ...,
        description="How often the habit must be completed."
    )
    status: HabitStatus = Field(
        default=HabitStatus.ACTIVE,
        description="The current lifecycle state of the habit."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of when the habit was created."
    )

    model_config = {
        "frozen": True,
        "validate_assignment": True
    }


class HabitCompletion(BaseModel):
    """
    Domain models for habit completion events.
    Core Domain Entity representing a single instance of a habit being completed.
    """
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique identifier for the completion event."
    )
    habit_id: uuid.UUID = Field(
        ...,
        description="The ID of the habit that was completed."
    )
    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of when the habit was completed."
    )

    model_config = {
        "frozen": True
    }