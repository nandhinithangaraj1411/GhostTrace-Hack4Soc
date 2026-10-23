from pathlib import Path

# Resolve relative to this file's location (backend/), not the process cwd,
# so scanning works the same whether invoked from the repo root, from
# backend/, or via an absolute path to this script.
SCAN_ROOT = str(Path(__file__).resolve().parent.parent / "demo_data")

ALLOWED_EXTENSIONS = {
    ".txt", ".csv", ".json", ".pdf", ".jpg", ".jpeg", ".png", ".sqlite", ".db",".docx"
}

CATEGORY_WEIGHTS = {
    "identity": 8,
    "contact": 6,
    "government_id": 20,
    "financial": 18,
    "credentials": 22,
    "location": 15,
    "behavioral": 10
}