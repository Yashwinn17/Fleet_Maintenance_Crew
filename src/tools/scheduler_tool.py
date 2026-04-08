"""
Maintenance Scheduler Tool — CrewAI Custom Tool
Simulates a calendar/bay-booking system for fleet maintenance scheduling.
In production: replace with Google Calendar API, Fleetio, or ServiceMax.
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from datetime import datetime, timedelta


# ── Mock Bay Schedule ──────────────────────────────────────────────────────────
# Simulates a 5-bay fleet maintenance shop with current week availability
# Format: {bay_id: {date_str: [booked_hours]}}

TODAY = datetime.now()

MOCK_SCHEDULE = {
    "BAY-1": {
        (TODAY + timedelta(days=0)).strftime("%Y-%m-%d"): [8, 9, 10, 14, 15],      # Partially booked
        (TODAY + timedelta(days=1)).strftime("%Y-%m-%d"): [8, 9, 10, 11, 12, 13],  # Morning booked
        (TODAY + timedelta(days=2)).strftime("%Y-%m-%d"): [],                        # Open
        (TODAY + timedelta(days=3)).strftime("%Y-%m-%d"): [13, 14, 15, 16],
        (TODAY + timedelta(days=4)).strftime("%Y-%m-%d"): [8, 9],
    },
    "BAY-2": {
        (TODAY + timedelta(days=0)).strftime("%Y-%m-%d"): [8, 9, 10, 11, 12, 13, 14, 15],  # Fully booked
        (TODAY + timedelta(days=1)).strftime("%Y-%m-%d"): [14, 15, 16],
        (TODAY + timedelta(days=2)).strftime("%Y-%m-%d"): [8, 9, 10],
        (TODAY + timedelta(days=3)).strftime("%Y-%m-%d"): [],
        (TODAY + timedelta(days=4)).strftime("%Y-%m-%d"): [10, 11, 12],
    },
    "BAY-3": {
        (TODAY + timedelta(days=0)).strftime("%Y-%m-%d"): [11, 12, 13],
        (TODAY + timedelta(days=1)).strftime("%Y-%m-%d"): [],
        (TODAY + timedelta(days=2)).strftime("%Y-%m-%d"): [9, 10, 11, 12, 13, 14],
        (TODAY + timedelta(days=3)).strftime("%Y-%m-%d"): [8, 9],
        (TODAY + timedelta(days=4)).strftime("%Y-%m-%d"): [],
    },
    "BAY-LIFT": {  # Lift bay — for catalytic converter, exhaust work
        (TODAY + timedelta(days=0)).strftime("%Y-%m-%d"): [8, 9, 10, 11, 12, 13, 14, 15],  # Fully booked
        (TODAY + timedelta(days=1)).strftime("%Y-%m-%d"): [8, 9, 10, 11],
        (TODAY + timedelta(days=2)).strftime("%Y-%m-%d"): [],
        (TODAY + timedelta(days=3)).strftime("%Y-%m-%d"): [14, 15, 16],
        (TODAY + timedelta(days=4)).strftime("%Y-%m-%d"): [8, 9, 10, 11, 12],
    },
    "BAY-DIAG": {  # Diagnostic-only bay
        (TODAY + timedelta(days=0)).strftime("%Y-%m-%d"): [9, 10],
        (TODAY + timedelta(days=1)).strftime("%Y-%m-%d"): [],
        (TODAY + timedelta(days=2)).strftime("%Y-%m-%d"): [13, 14],
        (TODAY + timedelta(days=3)).strftime("%Y-%m-%d"): [],
        (TODAY + timedelta(days=4)).strftime("%Y-%m-%d"): [],
    },
}

WORK_HOURS = list(range(8, 17))  # 8am–5pm (last slot at 4pm/16:00)

TECHNICIAN_POOL = {
    "TECH-Carlos": {"specialty": "Engine/Drivetrain", "available_days": [0, 1, 2, 3, 4]},
    "TECH-Priya": {"specialty": "Electronics/Diagnostics", "available_days": [0, 1, 2, 4]},
    "TECH-Marcus": {"specialty": "Brakes/Suspension", "available_days": [1, 2, 3, 4]},
    "TECH-Ana": {"specialty": "Emissions/Exhaust", "available_days": [0, 2, 3, 4]},
}


class SchedulerInput(BaseModel):
    vehicle_id: str = Field(description="Vehicle/fleet ID to schedule (e.g., 'TRUCK-007')")
    repair_type: str = Field(description="Type of repair needed (e.g., 'engine misfire, catalytic converter')")
    estimated_hours: float = Field(description="Estimated hours needed for the repair")
    urgency: str = Field(
        default="MEDIUM",
        description="Urgency level: CRITICAL, HIGH, MEDIUM, or LOW"
    )
    requires_lift: bool = Field(default=False, description="Whether repair requires lift bay")


class MaintenanceSchedulerTool(BaseTool):
    name: str = "Maintenance Bay Scheduler"
    description: str = (
        "Checks fleet maintenance shop availability and books a maintenance slot for a vehicle. "
        "Finds the earliest available bay and technician matching the repair needs. "
        "Returns a confirmed booking with bay assignment, technician, date, and time."
    )
    args_schema: Type[BaseModel] = SchedulerInput

    def _run(
        self,
        vehicle_id: str,
        repair_type: str,
        estimated_hours: float,
        urgency: str = "MEDIUM",
        requires_lift: bool = False
    ) -> str:
        hours_needed = int(estimated_hours) + (1 if estimated_hours % 1 > 0 else 0)

        # Select bay pool
        if requires_lift:
            bay_candidates = ["BAY-LIFT"]
        else:
            bay_candidates = ["BAY-1", "BAY-2", "BAY-3"]

        # How far out to search (urgency-driven)
        search_days = {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 5,
            "LOW": 7,
        }.get(urgency.upper(), 5)

        booking = None
        for day_offset in range(search_days):
            date = TODAY + timedelta(days=day_offset)
            date_str = date.strftime("%Y-%m-%d")
            day_name = date.strftime("%A, %B %d %Y")

            for bay_id in bay_candidates:
                booked = MOCK_SCHEDULE.get(bay_id, {}).get(date_str, [])
                free_hours = [h for h in WORK_HOURS if h not in booked]

                # Find consecutive block
                start_hour = self._find_consecutive_block(free_hours, hours_needed)
                if start_hour is not None:
                    booking = {
                        "bay": bay_id,
                        "date_str": date_str,
                        "day_name": day_name,
                        "start_hour": start_hour,
                        "end_hour": start_hour + hours_needed,
                    }
                    break
            if booking:
                break

        # Assign best available technician
        technician = self._assign_technician(repair_type, booking["date_str"] if booking else None)

        if not booking:
            return (
                f"=== SCHEDULING RESULT ===\n"
                f"Vehicle ID: {vehicle_id}\n"
                f"Status: ❌ NO AVAILABILITY in next {search_days} days\n"
                f"Repair Type: {repair_type}\n"
                f"Urgency: {urgency}\n\n"
                f"ACTION REQUIRED: Contact shop manager to arrange emergency scheduling or outsource."
            )

        # Confirm booking
        start_time = f"{booking['start_hour']}:00"
        end_time = f"{booking['end_hour']}:00"

        confirmation_id = f"WO-{vehicle_id}-{booking['date_str'].replace('-','')}-{booking['start_hour']:02d}"

        output = (
            f"=== MAINTENANCE APPOINTMENT CONFIRMED ===\n"
            f"Work Order #: {confirmation_id}\n"
            f"Vehicle ID: {vehicle_id}\n"
            f"Status: ✅ BOOKED\n\n"
            f"APPOINTMENT DETAILS:\n"
            f"  Date: {booking['day_name']}\n"
            f"  Time: {start_time} – {end_time} ({hours_needed}h block)\n"
            f"  Bay: {booking['bay']}\n"
            f"  Assigned Technician: {technician['name']}\n"
            f"  Tech Specialty: {technician['specialty']}\n\n"
            f"REPAIR DETAILS:\n"
            f"  Repair Type: {repair_type}\n"
            f"  Urgency Level: {urgency}\n"
            f"  Estimated Duration: {estimated_hours}h\n"
            f"  Lift Required: {'Yes' if requires_lift else 'No'}\n\n"
            f"NEXT STEPS:\n"
            f"  1. Parts should arrive before appointment (check Parts Sourcing Report)\n"
            f"  2. Vehicle check-in: {booking['start_hour'] - 1}:30 – {booking['start_hour']}:00\n"
            f"  3. Driver notification sent to fleet manager\n"
            f"  4. Estimated completion: {end_time}"
        )

        return output

    def _find_consecutive_block(self, free_hours: list, needed: int) -> int | None:
        """Find the first block of `needed` consecutive hours in free_hours list."""
        if not free_hours or needed <= 0:
            return None
        for i in range(len(free_hours) - needed + 1):
            block = free_hours[i:i + needed]
            if block == list(range(block[0], block[0] + needed)):
                return block[0]
        return None

    def _assign_technician(self, repair_type: str, date_str: str) -> dict:
        """Match repair type to best available technician."""
        repair_lower = repair_type.lower()

        priority_map = {
            "engine": "TECH-Carlos",
            "misfire": "TECH-Carlos",
            "fuel": "TECH-Carlos",
            "catalytic": "TECH-Ana",
            "exhaust": "TECH-Ana",
            "emissions": "TECH-Ana",
            "brake": "TECH-Marcus",
            "abs": "TECH-Marcus",
            "suspension": "TECH-Marcus",
            "sensor": "TECH-Priya",
            "electrical": "TECH-Priya",
            "diagnostic": "TECH-Priya",
            "airbag": "TECH-Priya",
            "communication": "TECH-Priya",
        }

        for keyword, tech_id in priority_map.items():
            if keyword in repair_lower:
                tech = TECHNICIAN_POOL[tech_id]
                return {"name": tech_id, "specialty": tech["specialty"]}

        # Default to first available
        return {"name": "TECH-Carlos", "specialty": "General Maintenance"}
