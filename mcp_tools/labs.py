import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent / "mock_data" / "lab_results.json"


def query_lab_results(patient_id: str) -> list[dict]:
    """Return last 48hr lab results for the given patient."""
    with open(_DATA_PATH) as f:
        return json.load(f)
