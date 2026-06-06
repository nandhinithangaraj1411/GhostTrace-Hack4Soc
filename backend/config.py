SCAN_ROOT = "../demo_data"

ALLOWED_EXTENSIONS = {
    ".txt", ".csv", ".json", ".pdf", ".jpg", ".jpeg", ".png", ".sqlite", ".db",".docx",
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