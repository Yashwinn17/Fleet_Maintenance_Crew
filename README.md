# Fleet Maintenance Crew

> **Day 17 / 84-Day Agentic AI Roadmap**  
> Multi-agent fleet maintenance: from diagnostic code to booked appointment in one conversation.

## The Problem

Fleet maintenance is fragmented across **5 systems**:
1. OBD scanner software
2. Parts management system
3. Shop calendar
4. Technician assignment
5. Work order system

A single `P0300` code can trigger hours of coordination before a wrench touches the vehicle.

## The Solution

One **hierarchical multi-agent crew** handles the workflow end to end:

```text
DTC Code Input
      |
      v
+-----------------------------------------+
|  COORDINATOR (Hierarchical Manager)     |
|  Orchestrates full workflow             |
+-------+---------+------------+----------+
        |         |            |
        v         v            v
+----------+ +----------+ +-----------+
|Diagnostic| |  Parts   | | Scheduler |
|  Agent   | |  Agent   | |   Agent   |
| OBD Tool | |Parts API | | Calendar  |
+----------+ +----------+ +-----------+
        \         |            /
         +--------v-----------+
          Fleet Maintenance Action Report
```

**Input:** Vehicle ID + DTC codes  
**Output:** Confirmed work order + appointment + action report

## Architecture

| Component | Details |
|-----------|---------|
| Framework | CrewAI with hierarchical process |
| Agents | 4 (Diagnostic, Parts, Scheduler, Coordinator) |
| Custom Tools | 3 (OBD lookup, parts search, bay scheduler) |
| LLM | Ollama or Groq |
| UI | Streamlit |

## Setup

### 1. Clone & Install

```bash
git clone https://github.com/Yashwinn17/fleet-maintenance-crew
cd fleet-maintenance-crew
pip install -r requirements.txt
```

### 2. Configure LLM

```bash
cp .env.example .env
```

Add this to `.env` for Groq:

```env
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=groq/llama-3.1-70b-versatile
LLM_PROVIDER=groq
```

For Ollama, keep:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=ollama/llama3.1:8b
```

### 3. Run

**Streamlit UI**

```bash
streamlit run app.py
```

The UI now includes an **LLM Provider** selector so you can switch between `ollama` and `groq`.

**CLI**

```bash
python main.py --vehicle TRUCK-007 --codes "P0300,P0420"
python main.py --vehicle VAN-012 --codes "C0035,B0001" --provider groq --verbose
```

## Example DTC Codes

| Code | Description | Severity |
|------|-------------|----------|
| `P0300` | Random Cylinder Misfire | HIGH |
| `P0420` | Catalyst Efficiency Low | MEDIUM |
| `P0171` | System Too Lean | MEDIUM |
| `C0035` | Wheel Speed Sensor | HIGH |
| `B0001` | Airbag/SRS Fault | CRITICAL |
| `U0100` | Lost ECM Communication | CRITICAL |

## Project Structure

```text
fleet_maintenance_crew/
|-- app.py
|-- main.py
|-- requirements.txt
|-- .env
|-- .env.example
`-- src/
    |-- agents/
    |   |-- __init__.py
    |   `-- agents.py
    |-- config/
    |   |-- __init__.py
    |   `-- llm_config.py
    |-- crew/
    |   |-- __init__.py
    |   `-- fleet_crew.py
    |-- tools/
    |   |-- __init__.py
    |   |-- obd_tool.py
    |   |-- parts_tool.py
    |   `-- scheduler_tool.py
    `-- __init__.py
```
