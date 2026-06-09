"""
Healthcare operational and clinical habits.

This module provides a predefined set of hospital-specific habits and a loader
function to populate the database with these habits alongside 4 weeks of 
realistic historical completion data for analytics testing.
"""

import logging
from datetime import datetime, timedelta, timezone
from habit_tracker.period import Periodicity
from habit_tracker.habit import Habit
from habit_tracker.repository import HabitRepository

logger = logging.getLogger(__name__)

HEALTHCARE_HABITS = [
    # DAILY HABITS
    {"name": "Hand Hygiene Compliance Check", "desc": "Ensure staff follow handwashing and sanitization protocols.", "period": Periodicity.DAILY},
    {"name": "Patient Vital Signs Monitoring", "desc": "Record and review vital signs for admitted patients.", "period": Periodicity.DAILY},
    {"name": "Medication Administration Audit", "desc": "Verify medications are administered correctly and on schedule.", "period": Periodicity.DAILY},
    {"name": "Ward Cleanliness Inspection", "desc": "Inspect wards for cleanliness and infection control compliance.", "period": Periodicity.DAILY},
    {"name": "Medical Equipment Functionality Check", "desc": "Verify critical medical equipment is operational.", "period": Periodicity.DAILY},
    {"name": "Emergency Department Readiness Review", "desc": "Ensure emergency supplies and equipment are available.", "period": Periodicity.DAILY},
    {"name": "Patient Bed Occupancy Update", "desc": "Record and review current bed occupancy status.", "period": Periodicity.DAILY},
    {"name": "Laboratory Sample Collection Verification", "desc": "Confirm all required samples are collected and processed.", "period": Periodicity.DAILY},
    {"name": "Staff Attendance Review", "desc": "Monitor attendance and staffing levels for all shifts.", "period": Periodicity.DAILY},
    {"name": "Shift Handover Documentation", "desc": "Complete and review handover notes between shifts.", "period": Periodicity.DAILY},
    {"name": "Infection Control Surveillance", "desc": "Monitor and document infection prevention measures.", "period": Periodicity.DAILY},
    {"name": "Patient Feedback Collection", "desc": "Gather patient satisfaction and service feedback.", "period": Periodicity.DAILY},
    {"name": "Pharmacy Stock Level Check", "desc": "Review medication inventory and identify shortages.", "period": Periodicity.DAILY},
    {"name": "Medical Waste Disposal Verification", "desc": "Ensure waste is segregated and disposed of properly.", "period": Periodicity.DAILY},
    {"name": "Oxygen Supply Monitoring", "desc": "Verify oxygen tanks and central supply levels.", "period": Periodicity.DAILY},
    {"name": "Ambulance Readiness Check", "desc": "Confirm ambulances are fueled, stocked, and operational.", "period": Periodicity.DAILY},
    {"name": "Critical Care Unit Review", "desc": "Assess ICU patient status and resource availability.", "period": Periodicity.DAILY},
    {"name": "Security Patrol Log Review", "desc": "Review security reports and incident logs.", "period": Periodicity.DAILY},
    {"name": "Dietary Service Verification", "desc": "Ensure patient meals meet prescribed dietary requirements.", "period": Periodicity.DAILY},
    {"name": "Patient Discharge Planning Review", "desc": "Track patients ready for discharge and required actions.", "period": Periodicity.DAILY},

    # WEEKLY HABITS
    {"name": "Infection Control Committee Review", "desc": "Analyze infection rates and prevention measures.", "period": Periodicity.WEEKLY},
    {"name": "Staff Training Session", "desc": "Conduct training on procedures, safety, or compliance topics.", "period": Periodicity.WEEKLY},
    {"name": "Medical Equipment Maintenance Review", "desc": "Review maintenance schedules and completed work orders.", "period": Periodicity.WEEKLY},
    {"name": "Pharmacy Inventory Audit", "desc": "Perform detailed medication stock audits.", "period": Periodicity.WEEKLY},
    {"name": "Safety Incident Review", "desc": "Analyze accidents, near misses, and corrective actions.", "period": Periodicity.WEEKLY},
    {"name": "Emergency Response Drill", "desc": "Conduct preparedness exercises for emergency scenarios.", "period": Periodicity.WEEKLY},
    {"name": "Quality Assurance Meeting", "desc": "Review healthcare quality indicators and improvement plans.", "period": Periodicity.WEEKLY},
    {"name": "Hospital Waste Management Audit", "desc": "Evaluate waste handling and disposal compliance.", "period": Periodicity.WEEKLY},
    {"name": "Patient Satisfaction Analysis", "desc": "Review feedback trends and improvement opportunities.", "period": Periodicity.WEEKLY},
    {"name": "Department Performance Review", "desc": "Assess department KPIs and operational metrics.", "period": Periodicity.WEEKLY},
    {"name": "Blood Bank Inventory Assessment", "desc": "Verify blood product availability and expiration dates.", "period": Periodicity.WEEKLY},
    {"name": "Clinical Documentation Audit", "desc": "Review patient records for completeness and accuracy.", "period": Periodicity.WEEKLY},
    {"name": "Nursing Care Quality Assessment", "desc": "Evaluate nursing care standards and outcomes.", "period": Periodicity.WEEKLY},
    {"name": "Hospital Security Review", "desc": "Assess security incidents and preventive measures.", "period": Periodicity.WEEKLY},
    {"name": "Fire Safety Inspection", "desc": "Check fire extinguishers, alarms, and evacuation routes.", "period": Periodicity.WEEKLY},
    {"name": "Operating Theatre Readiness Audit", "desc": "Review equipment, supplies, and cleanliness standards.", "period": Periodicity.WEEKLY},
    {"name": "Procurement and Supply Review", "desc": "Monitor pending orders and supply chain performance.", "period": Periodicity.WEEKLY},
    {"name": "Staff Wellness Check-In", "desc": "Review staff workload, morale, and well-being initiatives.", "period": Periodicity.WEEKLY},
    {"name": "Financial Operations Review", "desc": "Assess billing, claims, and revenue cycle activities.", "period": Periodicity.WEEKLY},
    {"name": "Executive Operations Meeting", "desc": "Review hospital-wide operational performance and priorities.", "period": Periodicity.WEEKLY},
]


def load_healthcare_data(repository: HabitRepository, anchor_date: datetime | None = None) -> None:
    """
    Populates the database with healthcare habits and generates exactly 4 weeks 
    (28 days) of historical check-off data.
    """
    now = anchor_date or datetime.now(timezone.utc)
    
    # Define the starting point as exactly 4 weeks ago
    start_date = now - timedelta(days=28)
    
    logger.info(f"Loading {len(HEALTHCARE_HABITS)} healthcare habits with 4 weeks of history...")
    
    for habit_data in HEALTHCARE_HABITS:
        raw_period = habit_data["period"]
        period_enum = Periodicity(raw_period) if not isinstance(raw_period, Periodicity) else raw_period
        
        # 1. Create the habit domain entity
        habit = Habit(
            name=str(habit_data["name"]),
            description=str(habit_data["desc"]),
            periodicity=period_enum,
            created_at=start_date
        )
        repository.save(habit)
        
        # 2. Generate historical tracking data
        if period_enum == Periodicity.DAILY:
            # Generate 28 daily check-offs
            for day_offset in range(1, 29):
                completion_time = start_date + timedelta(days=day_offset)
                repository.record_completion(habit.id, completed_at=completion_time)
                
        elif period_enum == Periodicity.WEEKLY:
            # Generate 4 weekly check-offs (1 every 7 days)
            for week_offset in range(1, 5):
                completion_time = start_date + timedelta(weeks=week_offset)
                repository.record_completion(habit.id, completed_at=completion_time)
                
    logger.info("Healthcare seed data generation complete.")