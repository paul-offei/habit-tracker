"""
Integration tests for the analytics engine using the Healthcare seed data.
Validates streak calculations, overall hospital compliance, and functional filtering
over a predictable 4-week (28-day) horizon.
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from habit_tracker.database import Base
from habit_tracker.repository import HabitRepository
from habit_tracker.healthcare_habits import load_healthcare_data
from habit_tracker.period import Periodicity
from habit_tracker.orm import CompletionORM
from habit_tracker.analytics import (
    calculate_longest_streak,
    calculate_longest_streak_overall,
    filter_by_periodicity,
    filter_active_habits
)

# Use a fixed anchor date so time-based tests are perfectly reproducible
FIXED_NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

@pytest.fixture
def healthcare_repo():
    """Provides an in-memory repository pre-loaded with 4 weeks of healthcare data."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    repo = HabitRepository(session)
    # Load the 40 habits with 4 weeks of history relative to our FIXED_NOW
    load_healthcare_data(repo, anchor_date=FIXED_NOW)
    
    yield repo
    
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_daily_hospital_operations_perfect_compliance(healthcare_repo: HabitRepository):
    """
    Question: Do critical daily tasks (like Hand Hygiene) correctly calculate 
    a perfect 28-day streak over a 4-week period using the functional reducer?
    """
    all_habits = healthcare_repo.list_all()
    hygiene_habit = next(h for h in all_habits if h.name == "Hand Hygiene Compliance Check")
    
    completions = healthcare_repo.get_completions(hygiene_habit.id)
    longest = calculate_longest_streak(hygiene_habit, completions)
    
    assert len(completions) == 28, "There should be exactly 28 daily check-offs."
    assert longest == 28, "The longest streak should be a perfect 28 days."


def test_weekly_administrative_perfect_compliance(healthcare_repo: HabitRepository):
    """
    Question: Do weekly administrative tasks (like Staff Training) correctly calculate 
    a 4-week streak without being confused by the 7-day gaps between check-offs?
    """
    all_habits = healthcare_repo.list_all()
    training_habit = next(h for h in all_habits if h.name == "Staff Training Session")
    
    completions = healthcare_repo.get_completions(training_habit.id)
    longest = calculate_longest_streak(training_habit, completions)
    
    assert len(completions) == 4, "There should be exactly 4 weekly check-offs."
    assert longest == 4, "The longest streak should be 4 weeks."


def test_analytics_break_on_missed_hospital_protocol(healthcare_repo: HabitRepository):
    """
    Question: If a hospital department fails to check equipment on day 14, 
    does the analytics engine correctly break the 28-day streak into two 13-day streaks?
    """
    all_habits = healthcare_repo.list_all()
    equipment_habit = next(h for h in all_habits if h.name == "Medical Equipment Functionality Check")
    completions = healthcare_repo.get_completions(equipment_habit.id)
    
    # SABOTAGE THE DATA: Delete the completion that happened on Day 14
    sabotage_date = FIXED_NOW - timedelta(days=14)
    target_date_str = sabotage_date.strftime("%Y-%m-%d")
    
    completion_to_delete = next(
        c for c in completions 
        if c.completed_at.strftime("%Y-%m-%d") == target_date_str
    )
    
    # Remove it directly via ORM to simulate a missed day
    db_comp = healthcare_repo.session.query(CompletionORM).filter(CompletionORM.id == str(completion_to_delete.id)).first()
    healthcare_repo.session.delete(db_comp)
    healthcare_repo.session.commit()
    
    # Recalculate with the broken history
    broken_completions = healthcare_repo.get_completions(equipment_habit.id)
    longest = calculate_longest_streak(equipment_habit, broken_completions)
    
    assert len(broken_completions) == 27, "One day was missed, leaving 27 completions."
    assert longest == 14, "The longest consecutive run should be 14 days."


def test_hospital_wide_overall_streak(healthcare_repo: HabitRepository):
    """
    Question: Can the analytics engine map over all habits and correctly 
    reduce them to find the highest compliance streak in the entire hospital?
    """
    all_habits = healthcare_repo.list_all()
    
    # Build the completions map required by your calculate_longest_streak_overall function
    completions_map = {}
    for habit in all_habits:
        completions_map[habit.id] = healthcare_repo.get_completions(habit.id)
        
    overall_max = calculate_longest_streak_overall(all_habits, completions_map)
    
    # Because daily tasks ran for 28 days and weekly ran for 4, the absolute max is 28
    assert overall_max == 28, "The maximum streak across all departments should be 28."


def test_functional_filtering_of_healthcare_data(healthcare_repo: HabitRepository):
    """
    Question: Do the pure filtering functions successfully slice the hospital 
    data into the correct operational buckets?
    """
    all_habits = healthcare_repo.list_all()
    
    active_habits = filter_active_habits(all_habits)
    daily_habits = filter_by_periodicity(all_habits, Periodicity.DAILY)
    weekly_habits = filter_by_periodicity(all_habits, Periodicity.WEEKLY)
    
    assert len(active_habits) == 40, "All predefined habits should be active."
    assert len(daily_habits) == 20, "Exactly 20 habits should be daily operations."
    assert len(weekly_habits) == 20, "Exactly 20 habits should be weekly operations."