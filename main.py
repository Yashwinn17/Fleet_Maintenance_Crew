"""
Fleet Maintenance Crew CLI entry point.
Usage: python main.py --vehicle TRUCK-007 --codes "P0300,P0420"
"""

import argparse
import sys

from src.crew.fleet_crew import build_fleet_maintenance_crew


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fleet Maintenance Crew - multi-agent diagnostic to appointment system"
    )
    parser.add_argument(
        "--vehicle",
        "-v",
        type=str,
        default="TRUCK-007",
        help="Vehicle/fleet ID (default: TRUCK-007)",
    )
    parser.add_argument(
        "--codes",
        "-c",
        type=str,
        default="P0300,P0420",
        help="Comma-separated DTC codes (default: P0300,P0420)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed agent reasoning",
    )
    parser.add_argument(
        "--provider",
        choices=["ollama", "groq", "openrouter"],
        default=None,
        help="LLM provider override (default: use LLM_PROVIDER from .env)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Optional worker model override for the selected provider",
    )
    parser.add_argument(
        "--manager-model",
        type=str,
        default=None,
        help="Optional manager model override for the selected provider",
    )
    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print("  FLEET MAINTENANCE CREW")
    print(f"  Vehicle: {args.vehicle}")
    print(f"  DTC Codes: {args.codes}")
    print(f"{'=' * 60}\n")

    try:
        crew = build_fleet_maintenance_crew(
            vehicle_id=args.vehicle,
            dtc_codes=args.codes,
            verbose=args.verbose,
            provider=args.provider,
            model=args.model,
            manager_model=args.manager_model,
        )

        print("[Crew] Starting hierarchical workflow...")
        result = crew.kickoff()

        print(f"\n{'=' * 60}")
        print("  FLEET MAINTENANCE ACTION REPORT")
        print(f"{'=' * 60}\n")

        if hasattr(result, "raw"):
            print(result.raw)
        else:
            print(str(result))

        print(f"\n{'=' * 60}")
        if hasattr(result, "token_usage"):
            print(f"Token Usage: {result.token_usage}")
        print("  Workflow complete.")
        print(f"{'=' * 60}\n")

    except KeyboardInterrupt:
        print("\n[Interrupted] Crew run cancelled.")
        sys.exit(0)
    except Exception as exc:
        print(f"\n[ERROR] Crew execution failed: {exc}")
        print("\nTroubleshooting:")
        print("  - Ollama running? Run: ollama serve")
        print("  - Set GROQ_API_KEY in .env for the Groq provider")
        sys.exit(1)


if __name__ == "__main__":
    main()
