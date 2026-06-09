"""
Template habits for easy user onboarding.

This module provides a list of common, predefined habits that users can 
load into their database to get started quickly. Unlike test fixtures or 
heavy seed data, these habits are loaded completely fresh with zero 
historical tracking data.
"""

import logging
from habit_tracker.period import Periodicity
from habit_tracker.habit import Habit
from habit_tracker.repository import HabitRepository

logger = logging.getLogger(__name__)

PREDEFINED_HABITS = [
    # HOURLY
    {"name": "Drink Water", "desc": "Drink a glass of water", "period": Periodicity.HOURLY},
    {"name": "Stretch Body", "desc": "Do light stretching for mobility", "period": Periodicity.HOURLY},
    {"name": "Stand Up From Desk", "desc": "Take a short standing break", "period": Periodicity.HOURLY},
    {"name": "Eye Rest Break", "desc": "Follow the 20-20-20 eye rule", "period": Periodicity.HOURLY},
    {"name": "Deep Breathing", "desc": "Practice mindful breathing for 2 minutes", "period": Periodicity.HOURLY},
    {"name": "Check Posture", "desc": "Correct sitting posture", "period": Periodicity.HOURLY},
    {"name": "Walk Around Office", "desc": "Take a quick walk", "period": Periodicity.HOURLY},
    {"name": "Review Tasks", "desc": "Recheck current priorities", "period": Periodicity.HOURLY},

    # DAILY
    {"name": "Brush Teeth", "desc": "Brush teeth morning and night", "period": Periodicity.DAILY},
    {"name": "Morning Prayer", "desc": "Spend time praying or meditating", "period": Periodicity.DAILY},
    {"name": "Exercise", "desc": "Complete a workout session", "period": Periodicity.DAILY},
    {"name": "Read a Book", "desc": "Read for at least 20 minutes", "period": Periodicity.DAILY},
    {"name": "Journal Thoughts", "desc": "Write daily reflections", "period": Periodicity.DAILY},
    {"name": "Practice Coding", "desc": "Solve programming exercises", "period": Periodicity.DAILY},
    {"name": "Eat Fruits", "desc": "Consume healthy fruits", "period": Periodicity.DAILY},
    {"name": "Sleep Before 11 PM", "desc": "Maintain healthy sleep schedule", "period": Periodicity.DAILY},
    {"name": "Make Bed", "desc": "Organize bed after waking up", "period": Periodicity.DAILY},
    {"name": "Study Bible", "desc": "Read and reflect on scripture", "period": Periodicity.DAILY},
    {"name": "Language Practice", "desc": "Learn vocabulary or grammar", "period": Periodicity.DAILY},
    {"name": "Clean Workspace", "desc": "Keep desk tidy", "period": Periodicity.DAILY},

    # WEEKLY
    {"name": "Grocery Shopping", "desc": "Buy household supplies", "period": Periodicity.WEEKLY},
    {"name": "Call Parents", "desc": "Spend time talking with family", "period": Periodicity.WEEKLY},
    {"name": "Team Workout", "desc": "Participate in group exercise", "period": Periodicity.WEEKLY},
    {"name": "Review Weekly Goals", "desc": "Analyze weekly achievements", "period": Periodicity.WEEKLY},
    {"name": "Laundry", "desc": "Wash clothes", "period": Periodicity.WEEKLY},
    {"name": "Church Attendance", "desc": "Attend worship service", "period": Periodicity.WEEKLY},
    {"name": "Meal Prep", "desc": "Prepare meals for the week", "period": Periodicity.WEEKLY},
    {"name": "Budget Review", "desc": "Review personal expenses", "period": Periodicity.WEEKLY},
    {"name": "Clean Apartment", "desc": "Deep clean living area", "period": Periodicity.WEEKLY},
    {"name": "Networking Session", "desc": "Connect with professionals", "period": Periodicity.WEEKLY},

    # MONTHLY
    {"name": "Pay Bills", "desc": "Handle recurring payments", "period": Periodicity.MONTHLY},
    {"name": "Dentist Floss Review", "desc": "Improve dental hygiene consistency", "period": Periodicity.MONTHLY},
    {"name": "Backup Laptop Files", "desc": "Secure important data", "period": Periodicity.MONTHLY},
    {"name": "Read One Book", "desc": "Finish a complete book", "period": Periodicity.MONTHLY},
    {"name": "Financial Savings Review", "desc": "Evaluate savings progress", "period": Periodicity.MONTHLY},
    {"name": "Donate to Charity", "desc": "Contribute to a cause", "period": Periodicity.MONTHLY},
    {"name": "Replace Toothbrush", "desc": "Maintain oral hygiene tools", "period": Periodicity.MONTHLY},
    {"name": "Social Media Audit", "desc": "Reduce unnecessary distractions", "period": Periodicity.MONTHLY},
    {"name": "Vision Board Update", "desc": "Revisit life goals", "period": Periodicity.MONTHLY},

    # QUARTERLY
    {"name": "Medical Checkup", "desc": "Routine health assessment", "period": Periodicity.QUARTERLY},
    {"name": "Career Goal Review", "desc": "Evaluate professional progress", "period": Periodicity.QUARTERLY},
    {"name": "Wardrobe Organization", "desc": "Sort and donate clothes", "period": Periodicity.QUARTERLY},
    {"name": "Tax Preparation Review", "desc": "Organize financial records", "period": Periodicity.QUARTERLY},
    {"name": "Home Safety Inspection", "desc": "Check household safety items", "period": Periodicity.QUARTERLY},
    {"name": "Deep Digital Cleanup", "desc": "Organize files and emails", "period": Periodicity.QUARTERLY},
    {"name": "Skill Certification Progress", "desc": "Review certification goals", "period": Periodicity.QUARTERLY},

    # YEARLY
    {"name": "Full Medical Examination", "desc": "Annual body checkup", "period": Periodicity.YEARLY},
    {"name": "Renew Passport", "desc": "Update travel documents", "period": Periodicity.YEARLY},
    {"name": "Set Annual Goals", "desc": "Define yearly objectives", "period": Periodicity.YEARLY},
    {"name": "File Taxes", "desc": "Complete tax filing", "period": Periodicity.YEARLY},
    {"name": "Dental Visit", "desc": "Visit dentist for examination", "period": Periodicity.YEARLY},
    {"name": "Review Insurance Policies", "desc": "Evaluate insurance coverage", "period": Periodicity.YEARLY},
    {"name": "Career Reflection", "desc": "Reflect on career achievements", "period": Periodicity.YEARLY},
    {"name": "Declutter Home", "desc": "Remove unused items", "period": Periodicity.YEARLY},

    # SPRING
    {"name": "Spring Cleaning", "desc": "Deep clean home after winter", "period": Periodicity.SPRING},
    {"name": "Plant Flowers", "desc": "Start gardening activities", "period": Periodicity.SPRING},
    {"name": "Refresh Wardrobe", "desc": "Organize seasonal clothing", "period": Periodicity.SPRING},
    {"name": "Outdoor Jogging", "desc": "Resume outdoor fitness routines", "period": Periodicity.SPRING},
    {"name": "Allergy Preparation", "desc": "Prepare medication and prevention", "period": Periodicity.SPRING},

    # SUMMER
    {"name": "Drink Extra Water", "desc": "Increase hydration", "period": Periodicity.SUMMER},
    {"name": "Apply Sunscreen", "desc": "Protect skin from sun", "period": Periodicity.SUMMER},
    {"name": "Swimming Practice", "desc": "Engage in water exercise", "period": Periodicity.SUMMER},
    {"name": "Vacation Planning", "desc": "Organize summer trips", "period": Periodicity.SUMMER},
    {"name": "Outdoor Photography", "desc": "Explore outdoor creativity", "period": Periodicity.SUMMER},

    # AUTUMN
    {"name": "Prepare Warm Clothing", "desc": "Organize seasonal wear", "period": Periodicity.AUTUMN},
    {"name": "Reflect on Year Goals", "desc": "Review yearly progress", "period": Periodicity.AUTUMN},
    {"name": "Garden Cleanup", "desc": "Prepare garden for colder weather", "period": Periodicity.AUTUMN},
    {"name": "Reading Challenge", "desc": "Increase indoor reading time", "period": Periodicity.AUTUMN},
    {"name": "Immune Boost Routine", "desc": "Improve nutrition and vitamins", "period": Periodicity.AUTUMN},

    # WINTER
    {"name": "Drink Warm Tea", "desc": "Maintain warmth and hydration", "period": Periodicity.WINTER},
    {"name": "Indoor Exercise", "desc": "Continue workouts indoors", "period": Periodicity.WINTER},
    {"name": "Skin Moisturizing", "desc": "Prevent dry skin", "period": Periodicity.WINTER},
    {"name": "Gratitude Journaling", "desc": "Practice positive reflection", "period": Periodicity.WINTER},
    {"name": "Prepare Emergency Supplies", "desc": "Organize winter necessities", "period": Periodicity.WINTER},
    {"name": "Limit Holiday Spending", "desc": "Manage festive expenses", "period": Periodicity.WINTER},
]

def load_template_habits(repository: HabitRepository) -> None:
    """
    Parses the PREDEFINED_HABITS list and saves them directly to the database.
    Does not attach any historical completion data.
    """
    logger.info(f"Loading {len(PREDEFINED_HABITS)} template habits into the database.")
    
    for habit_data in PREDEFINED_HABITS:
        # The period is already an Enum in the dictionary, but if you ever switch to 
        # JSON strings in the future, it's safe to parse it dynamically like this:
        raw_period = habit_data["period"]
        period_enum = Periodicity(raw_period) if not isinstance(raw_period, Periodicity) else raw_period
        
        habit = Habit(
            name=str(habit_data["name"]),
            description=str(habit_data["desc"]),
            periodicity=period_enum
        )
        repository.save(habit)
        
    logger.info("Template habits successfully loaded.")