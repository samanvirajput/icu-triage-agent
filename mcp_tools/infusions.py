import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent / "mock_data" / "infusions.json"


def get_active_infusions(patient_id: str) -> list[dict]:
    """Return active IV medications and scheduled infusions for the given patient."""
    with open(_DATA_PATH) as f:
        return json.load(f)
