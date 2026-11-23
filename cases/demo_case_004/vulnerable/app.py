from pathlib import Path

NOTES_DIR = Path(__file__).resolve().parent / "notes"

def read_note(filename):
    return (NOTES_DIR / filename).read_text(encoding="utf-8")
