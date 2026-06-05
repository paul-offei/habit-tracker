"""
Time and scheduling domain logic.

This module defines the allowed periodicities for habits and provides
pure functions for calculating chronological boundaries (start and end times)
to determine if a habit was completed within its required window.
"""

import calendar
from enum import Enum
from datetime import datetime, timedelta, timezone


class Periodicity(str, Enum):
    """
    Defines the complete set of allowed scheduling intervals, 
    including standard frequencies and seasonal blocks.
    """
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


def get_period_boundaries(period: Periodicity, current_time: datetime) -> tuple[datetime, datetime]:
    """
    Calculates the exact start and end datetimes for a given period, 
    based on the provided timestamp.

    This is a pure function designed to support functional analytics pipelines.
    
    Args:
        period: The Periodicity interval to calculate.
        current_time: The reference datetime (must be timezone-aware).

    Returns:
        A tuple containing (period_start, period_end).
    """
    if current_time.tzinfo is None:
        raise ValueError("current_time must be timezone-aware.")

    year = current_time.year
    month = current_time.month
    day = current_time.day
    hour = current_time.hour
    tz = current_time.tzinfo

    if period == Periodicity.HOURLY:
        start = datetime(year, month, day, hour, tzinfo=tz)
        end = start + timedelta(hours=1) - timedelta(microseconds=1)
        return start, end

    if period == Periodicity.DAILY:
        start = datetime(year, month, day, tzinfo=tz)
        end = start + timedelta(days=1) - timedelta(microseconds=1)
        return start, end

    if period == Periodicity.WEEKLY:
        # Assuming Monday is the start of the week
        start = datetime(year, month, day, tzinfo=tz) - timedelta(days=current_time.weekday())
        end = start + timedelta(days=7) - timedelta(microseconds=1)
        return start, end

    if period == Periodicity.MONTHLY:
        start = datetime(year, month, 1, tzinfo=tz)
        _, last_day = calendar.monthrange(year, month)
        end = datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=tz)
        return start, end

    if period == Periodicity.QUARTERLY:
        quarter = (month - 1) // 3 + 1
        start_month = 3 * quarter - 2
        start = datetime(year, start_month, 1, tzinfo=tz)
        
        end_month = start_month + 2
        _, last_day = calendar.monthrange(year, end_month)
        end = datetime(year, end_month, last_day, 23, 59, 59, 999999, tzinfo=tz)
        return start, end

    if period == Periodicity.YEARLY:
        start = datetime(year, 1, 1, tzinfo=tz)
        end = datetime(year, 12, 31, 23, 59, 59, 999999, tzinfo=tz)
        return start, end

    # Meteorological Seasons (Northern Hemisphere Standard)
    if period == Periodicity.SPRING:
        start = datetime(year, 3, 1, tzinfo=tz)
        end = datetime(year, 5, 31, 23, 59, 59, 999999, tzinfo=tz)
        return start, end

    if period == Periodicity.SUMMER:
        start = datetime(year, 6, 1, tzinfo=tz)
        end = datetime(year, 8, 31, 23, 59, 59, 999999, tzinfo=tz)
        return start, end

    if period == Periodicity.AUTUMN:
        start = datetime(year, 9, 1, tzinfo=tz)
        end = datetime(year, 11, 30, 23, 59, 59, 999999, tzinfo=tz)
        return start, end

    if period == Periodicity.WINTER:
        # Winter wraps around the year end (Dec, Jan, Feb)
        # If we are in Jan/Feb, winter started last December.
        if month in (1, 2):
            start = datetime(year - 1, 12, 1, tzinfo=tz)
            end = datetime(year, 2, 28 if not calendar.isleap(year) else 29, 23, 59, 59, 999999, tzinfo=tz)
        else:
            start = datetime(year, 12, 1, tzinfo=tz)
            end = datetime(year + 1, 2, 28 if not calendar.isleap(year + 1) else 29, 23, 59, 59, 999999, tzinfo=tz)
        return start, end

    raise NotImplementedError(f"Boundary calculation for {period} is not implemented.")