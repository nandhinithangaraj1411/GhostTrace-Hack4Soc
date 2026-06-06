from pathlib import Path

def extract_text(file_path):
    path = Path(file_path)
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        try:
            return path.read_text(encoding="latin-1", errors="ignore")
        except Exception:
            return ""