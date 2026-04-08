"""
OBD Diagnostic Tool — CrewAI Custom Tool
Simulates OBD-II code lookup against a known DTC database.
In production: replace mock data with real OBD API (e.g., AutoMD, ALLDATA).
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type


# ── DTC Mock Database ──────────────────────────────────────────────────────────
DTC_DATABASE = {
    "P0300": {
        "description": "Random/Multiple Cylinder Misfire Detected",
        "severity": "HIGH",
        "system": "Engine",
        "symptoms": ["Rough idle", "Loss of power", "Poor fuel economy"],
        "likely_causes": ["Spark plugs", "Ignition coils", "Fuel injectors"],
        "estimated_repair_hours": 2.5,
    },
    "P0420": {
        "description": "Catalyst System Efficiency Below Threshold (Bank 1)",
        "severity": "MEDIUM",
        "system": "Emissions",
        "symptoms": ["Check engine light", "Reduced fuel efficiency"],
        "likely_causes": ["Catalytic converter", "O2 sensors", "Exhaust leaks"],
        "estimated_repair_hours": 3.0,
    },
    "P0171": {
        "description": "System Too Lean (Bank 1)",
        "severity": "MEDIUM",
        "system": "Fuel/Air Mixture",
        "symptoms": ["Rough idle", "Hesitation on acceleration", "Stalling"],
        "likely_causes": ["MAF sensor", "Vacuum leaks", "Fuel pump"],
        "estimated_repair_hours": 2.0,
    },
    "P0505": {
        "description": "Idle Air Control System Malfunction",
        "severity": "LOW",
        "system": "Engine",
        "symptoms": ["Erratic idle", "Engine stalling at idle"],
        "likely_causes": ["IAC valve", "Throttle body", "Vacuum leaks"],
        "estimated_repair_hours": 1.5,
    },
    "B0001": {
        "description": "Driver Frontal Stage 1 Deployment Control",
        "severity": "CRITICAL",
        "system": "Airbag/SRS",
        "symptoms": ["Airbag warning light"],
        "likely_causes": ["Airbag module", "Clock spring", "Wiring harness"],
        "estimated_repair_hours": 4.0,
    },
    "C0035": {
        "description": "Left Front Wheel Speed Sensor Circuit",
        "severity": "HIGH",
        "system": "ABS/Brakes",
        "symptoms": ["ABS light on", "Traction control disabled"],
        "likely_causes": ["Wheel speed sensor", "Tone ring", "Wiring"],
        "estimated_repair_hours": 1.5,
    },
    "U0100": {
        "description": "Lost Communication with ECM/PCM",
        "severity": "CRITICAL",
        "system": "Communication Network",
        "symptoms": ["Multiple warning lights", "Limp mode"],
        "likely_causes": ["CAN bus fault", "ECM failure", "Power supply"],
        "estimated_repair_hours": 5.0,
    },
}


class OBDLookupInput(BaseModel):
    dtc_codes: str = Field(
        description="Comma-separated DTC codes to look up (e.g., 'P0300,P0420')"
    )
    vehicle_id: str = Field(
        description="Vehicle identifier (e.g., VIN or fleet ID like 'TRUCK-007')"
    )


class OBDDiagnosticTool(BaseTool):
    name: str = "OBD Diagnostic Lookup"
    description: str = (
        "Looks up OBD-II Diagnostic Trouble Codes (DTCs) and returns detailed diagnostic "
        "information including severity, affected systems, likely causes, and estimated repair hours. "
        "Input comma-separated DTC codes and a vehicle ID."
    )
    args_schema: Type[BaseModel] = OBDLookupInput

    def _run(self, dtc_codes: str, vehicle_id: str) -> str:
        codes = [c.strip().upper() for c in dtc_codes.split(",")]
        results = []
        total_hours = 0.0
        highest_severity = "LOW"
        severity_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

        for code in codes:
            if code in DTC_DATABASE:
                dtc = DTC_DATABASE[code]
                total_hours += dtc["estimated_repair_hours"]
                if severity_rank.get(dtc["severity"], 0) > severity_rank.get(highest_severity, 0):
                    highest_severity = dtc["severity"]

                results.append(
                    f"CODE: {code}\n"
                    f"  Description: {dtc['description']}\n"
                    f"  Severity: {dtc['severity']}\n"
                    f"  System: {dtc['system']}\n"
                    f"  Symptoms: {', '.join(dtc['symptoms'])}\n"
                    f"  Likely Causes: {', '.join(dtc['likely_causes'])}\n"
                    f"  Est. Repair Hours: {dtc['estimated_repair_hours']}h"
                )
            else:
                results.append(
                    f"CODE: {code}\n"
                    f"  Description: Unknown code — manual inspection required\n"
                    f"  Severity: UNKNOWN\n"
                    f"  Est. Repair Hours: 1.0h (inspection only)"
                )
                total_hours += 1.0

        output = (
            f"=== OBD DIAGNOSTIC REPORT ===\n"
            f"Vehicle ID: {vehicle_id}\n"
            f"Codes Analyzed: {', '.join(codes)}\n"
            f"Overall Severity: {highest_severity}\n"
            f"Total Estimated Repair Time: {total_hours}h\n\n"
            f"DETAILED FINDINGS:\n"
            + "\n\n".join(results)
        )

        # Urgency recommendation
        if highest_severity == "CRITICAL":
            output += "\n\n⚠️  RECOMMENDATION: IMMEDIATE service required. Do not operate vehicle."
        elif highest_severity == "HIGH":
            output += "\n\n⚠️  RECOMMENDATION: Schedule service within 24-48 hours."
        elif highest_severity == "MEDIUM":
            output += "\n\n⚠️  RECOMMENDATION: Schedule service within 1 week."
        else:
            output += "\n\n✅  RECOMMENDATION: Schedule service at next convenient time."

        return output
