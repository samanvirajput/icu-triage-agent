import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent / "mock_data" / "vitals.json"


def get_live_vitals(patient_id: str) -> list[dict]:
    """Return time-series vitals for the given patient."""
    with open(_DATA_PATH) as f:
        return json.load(f)
