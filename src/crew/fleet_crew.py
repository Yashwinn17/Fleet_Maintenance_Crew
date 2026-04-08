"""
Fleet Maintenance Crew assembly and task definitions.
"""

from crewai import Crew, Process, Task

from src.agents.agents import build_agents
from src.config.llm_config import get_manager_llm


def build_tasks(agents: dict, vehicle_id: str, dtc_codes: str) -> list[Task]:
    """Build the four-task pipeline for a fleet maintenance request."""
    task_diagnose = Task(
        description=(
            f"Run a full diagnostic analysis for vehicle '{vehicle_id}' "
            f"with the following OBD-II DTC codes: {dtc_codes}.\n\n"
            "Use the OBD Diagnostic Lookup tool to analyze each code. "
            "Your output must include:\n"
            "1. Full description of each fault code\n"
            "2. Overall severity assessment (CRITICAL/HIGH/MEDIUM/LOW)\n"
            "3. List of all required repairs, in priority order\n"
            "4. Total estimated repair hours\n"
            "5. Urgency recommendation (immediate/this week/next service)\n"
            "6. Whether the vehicle should be grounded immediately"
        ),
        expected_output=(
            "A structured diagnostic report with severity level, complete list of faults, "
            "required repairs in priority order, total repair hours, and a clear urgency recommendation."
        ),
        agent=agents["diagnostic"],
    )

    task_source_parts = Task(
        description=(
            f"Based on the diagnostic report for vehicle '{vehicle_id}', "
            "source all required parts for the identified repairs.\n\n"
            "Use the Parts Inventory Search tool to find the best options for each part. "
            "Consider availability, pricing, and lead times.\n\n"
            "Your output must include:\n"
            "1. Best supplier and part number for each required part\n"
            "2. Total estimated parts cost\n"
            "3. Confirmation that all parts are in stock, or flag if ordering is needed\n"
            "4. Earliest date all parts will be available\n"
            "5. Any supply chain risks that could delay the repair"
        ),
        expected_output=(
            "A parts sourcing summary with best option per part, total parts cost, "
            "stock confirmation, and earliest parts availability date."
        ),
        agent=agents["parts"],
        context=[task_diagnose],
    )

    task_schedule = Task(
        description=(
            f"Schedule a maintenance appointment for vehicle '{vehicle_id}' "
            "based on the diagnostic findings and parts availability.\n\n"
            "Use the Maintenance Bay Scheduler tool to book the appointment. "
            "Key inputs to pass:\n"
            f"- vehicle_id: '{vehicle_id}'\n"
            "- repair_type: main repairs from the diagnostic report\n"
            "- estimated_hours: total hours from the diagnostic report\n"
            "- urgency: map diagnostic severity directly to CRITICAL/HIGH/MEDIUM/LOW\n"
            "- requires_lift: True if catalytic converter, exhaust, or underbody work is needed\n\n"
            "Ensure the appointment is scheduled after parts will be available."
        ),
        expected_output=(
            "A confirmed booking with work order number, date, time slot, bay assignment, "
            "assigned technician, and next steps for the fleet manager."
        ),
        agent=agents["scheduler"],
        context=[task_diagnose, task_source_parts],
    )

    task_final_report = Task(
        description=(
            f"Synthesize all outputs from the Diagnostic, Parts, and Scheduling agents "
            f"into a final Fleet Maintenance Action Report for vehicle '{vehicle_id}'.\n\n"
            "This report goes directly to the Fleet Operations Manager and must be concise, complete, "
            "actionable, and formatted for quick scanning.\n\n"
            "Include the following sections:\n"
            "1. EXECUTIVE SUMMARY\n"
            "2. DIAGNOSTIC FINDINGS\n"
            "3. PARTS STATUS\n"
            "4. APPOINTMENT DETAILS\n"
            "5. ACTION ITEMS\n"
            "6. ESTIMATED DOWNTIME"
        ),
        expected_output=(
            "A complete Fleet Maintenance Action Report with executive summary, diagnostic findings, "
            "parts status, appointment details, action items, and estimated downtime."
        ),
        agent=agents["coordinator"],
        context=[task_diagnose, task_source_parts, task_schedule],
    )

    return [task_diagnose, task_source_parts, task_schedule, task_final_report]


def build_fleet_maintenance_crew(
    vehicle_id: str,
    dtc_codes: str,
    verbose: bool = True,
    provider: str | None = None,
    model: str | None = None,
    manager_model: str | None = None,
) -> Crew:
    """Build and return the Fleet Maintenance Crew."""
    agents = build_agents(verbose=verbose, provider=provider, model=model)
    tasks = build_tasks(agents, vehicle_id, dtc_codes)
    manager_llm = get_manager_llm(provider=provider, model=manager_model)

    return Crew(
        agents=[
            agents["diagnostic"],
            agents["parts"],
            agents["scheduler"],
        ],
        tasks=tasks,
        process=Process.hierarchical,
        manager_agent=agents["coordinator"],
        manager_llm=manager_llm,
        verbose=verbose,
        full_output=True,
    )
