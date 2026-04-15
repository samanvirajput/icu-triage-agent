import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent / "mock_data" / "clinical_notes.json"


def fetch_clinical_notes(patient_id: str) -> list[dict]:
    """Return all clinical notes for the given patient."""
    with open(_DATA_PATH) as f:
        return json.load(f)
