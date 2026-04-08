"""
Parts Sourcing Tool — CrewAI Custom Tool
Simulates a parts inventory/supplier API lookup.
In production: replace with real APIs (AutoZone API, OReilly, FleetPride, RockAuto).
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, field_validator
from typing import Type
import random


# ── Mock Parts Catalog ─────────────────────────────────────────────────────────
PARTS_CATALOG = {
    "spark plugs": [
        {"supplier": "FleetPride", "part_number": "NGK-7090", "brand": "NGK", "price": 8.99, "in_stock": True, "lead_days": 0, "qty_available": 48},
        {"supplier": "AutoZone Pro", "part_number": "ACL-R5671", "brand": "ACDelco", "price": 6.49, "in_stock": True, "lead_days": 0, "qty_available": 24},
        {"supplier": "OEM Direct", "part_number": "OEM-SP-VQ35", "brand": "OEM", "price": 14.99, "in_stock": False, "lead_days": 3, "qty_available": 0},
    ],
    "ignition coils": [
        {"supplier": "FleetPride", "part_number": "UF-330", "brand": "Standard Motor", "price": 42.00, "in_stock": True, "lead_days": 0, "qty_available": 12},
        {"supplier": "OEM Direct", "part_number": "OEM-IC-22448", "brand": "OEM", "price": 89.00, "in_stock": True, "lead_days": 1, "qty_available": 6},
    ],
    "catalytic converter": [
        {"supplier": "FleetPride", "part_number": "MagFlow-CC-450", "brand": "MagnaFlow", "price": 187.00, "in_stock": True, "lead_days": 0, "qty_available": 4},
        {"supplier": "OEM Direct", "part_number": "OEM-CC-2341", "brand": "OEM", "price": 425.00, "in_stock": False, "lead_days": 5, "qty_available": 0},
    ],
    "o2 sensors": [
        {"supplier": "AutoZone Pro", "part_number": "BOB-15717", "brand": "Bosch", "price": 34.99, "in_stock": True, "lead_days": 0, "qty_available": 30},
        {"supplier": "FleetPride", "part_number": "NTK-24321", "brand": "NTK", "price": 28.50, "in_stock": True, "lead_days": 0, "qty_available": 18},
    ],
    "maf sensor": [
        {"supplier": "AutoZone Pro", "part_number": "DEA-0280218037", "brand": "Delphi", "price": 68.99, "in_stock": True, "lead_days": 0, "qty_available": 8},
        {"supplier": "OEM Direct", "part_number": "OEM-MAF-22680", "brand": "OEM", "price": 145.00, "in_stock": True, "lead_days": 2, "qty_available": 3},
    ],
    "wheel speed sensor": [
        {"supplier": "FleetPride", "part_number": "ALS-1051", "brand": "Standard Motor", "price": 29.99, "in_stock": True, "lead_days": 0, "qty_available": 16},
        {"supplier": "AutoZone Pro", "part_number": "DUR-ABS-551", "brand": "Dorman", "price": 24.50, "in_stock": True, "lead_days": 0, "qty_available": 22},
    ],
    "iac valve": [
        {"supplier": "AutoZone Pro", "part_number": "ACL-217-3201", "brand": "ACDelco", "price": 52.00, "in_stock": True, "lead_days": 0, "qty_available": 7},
        {"supplier": "FleetPride", "part_number": "STD-IAC-22", "brand": "Standard Motor", "price": 45.00, "in_stock": False, "lead_days": 2, "qty_available": 0},
    ],
    "fuel injectors": [
        {"supplier": "FleetPride", "part_number": "RC-17-0921", "brand": "RC Engineering", "price": 38.00, "in_stock": True, "lead_days": 0, "qty_available": 32},
        {"supplier": "OEM Direct", "part_number": "OEM-FI-16600", "brand": "OEM", "price": 95.00, "in_stock": True, "lead_days": 1, "qty_available": 8},
    ],
}


class PartsSearchInput(BaseModel):
    parts_needed: str = Field(
        description="Comma-separated list of parts to search for (e.g., 'spark plugs, ignition coils')"
    )
    quantity: int = Field(default=1, description="Quantity needed for each part")
    prefer_oem: bool = Field(default=False, description="Whether to prefer OEM parts over aftermarket")

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_quantity(cls, v):
        return int(v)


class PartsSourcerTool(BaseTool):
    name: str = "Parts Inventory Search"
    description: str = (
        "Searches fleet parts suppliers for required components. Returns availability, pricing, "
        "supplier information, stock levels, and lead times for each requested part. "
        "Use this to find the best parts options for a repair job."
    )
    args_schema: Type[BaseModel] = PartsSearchInput

    def _run(self, parts_needed: str, quantity: int = 1, prefer_oem: bool = False) -> str:
        parts = [p.strip().lower() for p in parts_needed.split(",")]
        report_sections = []
        total_min_cost = 0.0
        all_in_stock = True

        for part_name in parts:
            # Fuzzy match against catalog
            matched_key = None
            for catalog_key in PARTS_CATALOG:
                if catalog_key in part_name or part_name in catalog_key:
                    matched_key = catalog_key
                    break

            if not matched_key:
                report_sections.append(
                    f"PART: {part_name.title()}\n"
                    f"  ⚠️  Not found in catalog — contact procurement team\n"
                    f"  Recommended: Request quote from FleetPride or OEM Direct"
                )
                all_in_stock = False
                continue

            options = PARTS_CATALOG[matched_key]

            # Filter by availability and OEM preference
            in_stock = [o for o in options if o["in_stock"] and o["qty_available"] >= quantity]
            out_of_stock = [o for o in options if not o["in_stock"] or o["qty_available"] < quantity]

            if not in_stock:
                all_in_stock = False

            # Sort: OEM preference or by price
            if prefer_oem:
                in_stock.sort(key=lambda x: (x["brand"] != "OEM", x["price"]))
            else:
                in_stock.sort(key=lambda x: x["price"])

            best = in_stock[0] if in_stock else (out_of_stock[0] if out_of_stock else None)

            if best:
                total_min_cost += best["price"] * quantity
                section = f"PART: {part_name.title()}\n"
                section += f"  ✅ BEST OPTION:\n"
                section += f"    Supplier: {best['supplier']}\n"
                section += f"    Part #: {best['part_number']}\n"
                section += f"    Brand: {best['brand']}\n"
                section += f"    Price: ${best['price']:.2f} x{quantity} = ${best['price']*quantity:.2f}\n"
                section += f"    In Stock: {'Yes' if best['in_stock'] else 'No'}\n"
                lead_time = (
                    'Same day' if best['lead_days'] == 0 else f"{best['lead_days']} business days"
                )
                section += f"    Lead Time: {lead_time}\n"
                section += f"    Qty Available: {best['qty_available']} units\n"

                if len(in_stock) > 1:
                    alt = in_stock[1]
                    section += f"  📦 ALTERNATE:\n"
                    section += f"    {alt['supplier']} | {alt['part_number']} | ${alt['price']:.2f} | {alt['brand']}"

                report_sections.append(section)

        output = (
            f"=== PARTS SOURCING REPORT ===\n"
            f"Parts Requested: {', '.join(p.title() for p in parts)}\n"
            f"Quantity Per Part: {quantity}\n"
            f"OEM Preferred: {'Yes' if prefer_oem else 'No'}\n"
            f"Estimated Parts Cost: ${total_min_cost:.2f}\n"
            f"All Parts In Stock: {'Yes ✅' if all_in_stock else 'No — some items require ordering ⚠️'}\n\n"
            f"DETAILED SOURCING:\n"
            + "\n\n".join(report_sections)
        )

        return output
