"""
Fleet Maintenance Crew Streamlit UI.
"""

import streamlit as st

from src.crew.fleet_crew import build_fleet_maintenance_crew

st.set_page_config(
    page_title="Fleet Maintenance Crew",
    page_icon="truck",
    layout="wide",
)

st.markdown(
    """
<style>
    .main { background-color: #0f1117; }
    .stTextInput > div > div > input { background-color: #1e2130; color: white; border: 1px solid #3a3f5a; }
    .severity-critical { color: #ff4757; font-weight: bold; }
    .severity-high { color: #ffa502; font-weight: bold; }
    .severity-medium { color: #ffd32a; }
    .severity-low { color: #2ed573; }
    .code-tag {
        display: inline-block;
        background: #1e2130;
        border: 1px solid #3a3f5a;
        padding: 2px 10px;
        border-radius: 4px;
        font-family: monospace;
        margin: 2px;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("# Fleet Maintenance Crew")
st.markdown("**Multi-agent system: Diagnostic -> Parts Sourcing -> Scheduling -> Report**")
st.divider()

with st.sidebar:
    st.header("Maintenance Request")

    provider = st.selectbox(
        "LLM Provider",
        options=["openrouter", "ollama", "groq"],
        index=0,
        help="Choose the LLM provider: OpenRouter (cloud), Ollama (local), or Groq (cloud).",
    )
    model_override = st.text_input(
        "Agent Model Override",
        value="",
        placeholder="Optional",
        help=(
            "Leave blank to use OLLAMA_MODEL from .env."
            if provider == "ollama"
            else "Leave blank to use GROQ_MODEL from .env."
        ),
    )
    manager_model_override = st.text_input(
        "Manager Model Override",
        value="",
        placeholder="Optional",
        help="Optional stronger model for the coordinator/manager agent.",
    )

    vehicle_id = st.text_input(
        "Vehicle ID",
        value="TRUCK-007",
        placeholder="e.g., TRUCK-007, VAN-012, BUS-003",
    )
    dtc_input = st.text_area(
        "OBD-II DTC Codes",
        value="P0300, P0420",
        placeholder="Enter comma-separated codes\ne.g., P0300, P0171, C0035",
        height=80,
    )

    st.markdown("**Common DTC Codes to Try:**")
    code_examples = {
        "Engine Misfire": "P0300",
        "Catalytic Converter": "P0420",
        "System Too Lean": "P0171",
        "Wheel Speed Sensor": "C0035",
        "Airbag/SRS": "B0001",
        "Multi-System Fault": "P0300, P0420, C0035",
    }
    for label, codes in code_examples.items():
        if st.button(label, use_container_width=True):
            st.session_state["quick_codes"] = codes

    if "quick_codes" in st.session_state:
        dtc_input = st.session_state["quick_codes"]

    st.divider()
    verbose = st.checkbox("Show Agent Reasoning", value=False)
    run_btn = st.button("Run Fleet Maintenance Crew", type="primary", use_container_width=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Agents", "4", "Hierarchical")
col2.metric("Process", "Hierarchical", "Coordinator-led")
col3.metric("Custom Tools", "3", "OBD + Parts + Calendar")
col4.metric("Providers", "2", "Ollama + Groq")

st.divider()

if run_btn:
    if not vehicle_id or not dtc_input:
        st.error("Please enter a Vehicle ID and at least one DTC code.")
    else:
        st.markdown(f"### Running maintenance workflow for `{vehicle_id}`")
        st.markdown(f"**Provider:** `{provider}`")
        st.markdown(f"**DTC Codes:** `{dtc_input.strip()}`")

        progress_bar = st.progress(0)

        with st.spinner("Fleet Maintenance Crew is working..."):
            with st.container():
                st.markdown("**Agent Pipeline:**")
                a1, a2, a3, a4 = st.columns(4)
                a1_box = a1.info("Diagnostic\n\nWaiting...")
                a2_box = a2.empty()
                a2_box.info("Parts\n\nWaiting...")
                a3_box = a3.empty()
                a3_box.info("Scheduler\n\nWaiting...")
                a4_box = a4.empty()
                a4_box.info("Coordinator\n\nWaiting...")

            try:
                a1_box.warning("Diagnostic\n\nRunning...")
                progress_bar.progress(10)

                crew = build_fleet_maintenance_crew(
                    vehicle_id=vehicle_id.strip(),
                    dtc_codes=dtc_input.strip(),
                    verbose=verbose,
                    provider=provider,
                    model=model_override.strip() or None,
                    manager_model=manager_model_override.strip() or None,
                )

                progress_bar.progress(25)
                a1_box.success("Diagnostic\n\nComplete")
                a2_box.warning("Parts\n\nRunning...")

                result = crew.kickoff()

                progress_bar.progress(75)
                a2_box.success("Parts\n\nComplete")
                a3_box.success("Scheduler\n\nComplete")
                progress_bar.progress(95)
                a4_box.success("Coordinator\n\nComplete")
                progress_bar.progress(100)

                st.success("Fleet Maintenance Crew completed successfully.")
                st.divider()

                st.markdown("## Fleet Maintenance Action Report")
                final_output = result.raw if hasattr(result, "raw") else str(result)
                st.markdown(final_output)

                if hasattr(result, "tasks_output") and result.tasks_output:
                    st.divider()
                    st.markdown("### Individual Agent Outputs")
                    tabs = st.tabs(
                        ["Diagnostic Report", "Parts Sourcing", "Scheduling", "Final Report"]
                    )
                    for index, tab in enumerate(tabs):
                        with tab:
                            if index < len(result.tasks_output):
                                task_out = result.tasks_output[index]
                                st.markdown(task_out.raw if hasattr(task_out, "raw") else str(task_out))

                if hasattr(result, "token_usage") and result.token_usage:
                    st.divider()
                    st.caption(f"Token Usage: {result.token_usage}")

            except Exception as exc:
                progress_bar.progress(0)
                a1_box.error("Error")
                st.error(f"**Crew execution failed:** {exc}")
                st.markdown("**Troubleshooting:**")
                st.markdown("- Ensure Ollama is running: `ollama serve`")
                st.markdown("- Or set `GROQ_API_KEY` in your `.env` file")
                st.markdown("- Check `LLM_PROVIDER` in your `.env`")
                with st.expander("Full error details"):
                    st.exception(exc)
else:
    st.markdown(
        """
## How It Works

This system unifies five fragmented fleet maintenance systems into a single conversation:

| Step | Agent | Tool | Output |
|------|-------|------|--------|
| 1 | **Diagnostic Specialist** | OBD Code Lookup | Severity, root causes, repair scope |
| 2 | **Parts Procurement** | Parts Inventory API | Best supplier, pricing, availability |
| 3 | **Maintenance Scheduler** | Calendar/Bay API | Confirmed work order + appointment |
| 4 | **Operations Coordinator** | Delegation | Final Fleet Action Report |

**Before:** 5 systems, 3 departments, hours of back-and-forth

**After:** One conversation. One report. One booked appointment.
"""
    )

    st.markdown("### Try it")
    st.markdown("1. Choose `ollama` or `groq` in the sidebar.")
    st.markdown("2. Enter a Vehicle ID and one or more DTC codes.")
    st.markdown("3. Click **Run Fleet Maintenance Crew**.")
