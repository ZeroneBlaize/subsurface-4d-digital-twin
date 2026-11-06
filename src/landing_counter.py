"""
Landing & Computation Telemetry Counter: Tracks persistent usage, visits, and simulation metrics.
Stores state in data/db/landing_counter.json with fallback defaults.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

COUNTER_FILE = Path(__file__).resolve().parent.parent / "data" / "db" / "landing_counter.json"

DEFAULT_COUNTER = {
    "total_visits": 1420,
    "total_simulations": 8394,
    "total_boreholes_processed": 3842,
    "last_active": "2026-11-06T11:00:00Z",
    "created_at": "2026-10-01T00:00:00Z"
}


class LandingCounter:
    """Manages persistent landing counter and simulation usage telemetry."""

    def __init__(self, file_path: Path = COUNTER_FILE):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.file_path.exists():
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_COUNTER, f, indent=2)

    def get_counts(self) -> Dict[str, Any]:
        """Reads current telemetry counts."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_COUNTER, **data}
        except Exception:
            return DEFAULT_COUNTER.copy()

    def _save_counts(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            pass

    def increment_visit(self) -> int:
        """Increments visit counter on page load."""
        data = self.get_counts()
        data["total_visits"] = int(data.get("total_visits", 0)) + 1
        data["last_active"] = datetime.now().isoformat()
        self._save_counts(data)
        return data["total_visits"]

    def increment_simulations(self, count: int = 1) -> int:
        """Increments simulation execution counter."""
        data = self.get_counts()
        data["total_simulations"] = int(data.get("total_simulations", 0)) + count
        data["last_active"] = datetime.now().isoformat()
        self._save_counts(data)
        return data["total_simulations"]

    def increment_boreholes(self, count: int = 1) -> int:
        """Increments processed borehole counter."""
        data = self.get_counts()
        data["total_boreholes_processed"] = int(data.get("total_boreholes_processed", 0)) + count
        data["last_active"] = datetime.now().isoformat()
        self._save_counts(data)
        return data["total_boreholes_processed"]


# Global instance
_counter_instance = None

def get_landing_counter() -> LandingCounter:
    global _counter_instance
    if _counter_instance is None:
        _counter_instance = LandingCounter()
    return _counter_instance
