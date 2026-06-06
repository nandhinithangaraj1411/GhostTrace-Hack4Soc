from pathlib import Path
from config import SCAN_ROOT, ALLOWED_EXTENSIONS

def scan_files(root_path=SCAN_ROOT):
    root = Path(root_path)
    print("SCAN_ROOT =", root.resolve())
    print("Exists =", root.exists())
    root = Path(root_path)
    files = []

    if not root.exists():
        return files

    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS:
            print(path.name, path.suffix.lower())
            stat = path.stat()
            files.append({
                "path": str(path),
                "name": path.name,
                "extension": path.suffix.lower(),
                "size": stat.st_size,
                "modified": stat.st_mtime
            })

    return files