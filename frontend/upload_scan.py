"""Stage uploaded documents and run them through backend/report.py.

There is no second scanner here: uploads are written to a private temp
directory and handed to the existing pipeline via a manifest file. Everything
runs locally; nothing is sent over the network.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
REPORT_SCRIPT = ROOT_DIR / "backend" / "report.py"
SHARED_DIR = ROOT_DIR / "shared"
ANALYSIS_JSON = SHARED_DIR / "analysis.json"
LOCK_FILE = SHARED_DIR / ".scan.lock"

# Extensions report.py actually has an extractor branch for. config.py also
# lists .sqlite/.db, but report.py never extracts them, so they're not
# offered for upload.
SUPPORTED_EXTENSIONS = {
    ".txt": "Plain text (full text scanned)",
    ".csv": "CSV (read as plain text)",
    ".json": "JSON (read as plain text)",
    ".pdf": "PDF (embedded text layer only - no OCR)",
    ".docx": "Word .docx (body paragraphs only)",
    ".jpg": "JPEG (EXIF metadata only - no OCR)",
    ".jpeg": "JPEG (EXIF metadata only - no OCR)",
    ".png": "PNG (EXIF metadata only - no OCR)",
}

SCAN_TIMEOUT_SECONDS = 600


class ScanBusyError(RuntimeError):
    pass


def validate_upload(name, data):
    """Return None if the upload can be scanned, else a reason string."""
    ext = Path(name).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return f"Unsupported file type '{ext or '(none)'}'"
    if not data:
        return "File is empty (0 bytes)"
    return None


def display_name(name):
    # Only the final path component, never a client-supplied directory.
    base = Path(str(name).replace("\\", "/")).name.strip()
    return base or "unnamed"


def unique_names(names):
    """De-duplicate display names so findings stay attributable per file."""
    seen = {}
    result = []
    for name in names:
        candidate = name
        stem, ext = os.path.splitext(name)
        n = 1
        while candidate in seen:
            n += 1
            candidate = f"{stem} ({n}){ext}"
        seen[candidate] = True
        result.append(candidate)
    return result


def _acquire_lock():
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        age = time.time() - LOCK_FILE.stat().st_mtime
        if age > SCAN_TIMEOUT_SECONDS + 60:
            LOCK_FILE.unlink(missing_ok=True)
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ScanBusyError(
            "Another scan is already running. Wait for it to finish and try again."
        )
    with os.fdopen(fd, "w") as fp:
        fp.write(f"{os.getpid()} {time.time()}")


def _release_lock():
    LOCK_FILE.unlink(missing_ok=True)


def _run_pipeline(manifest, work_dir):
    manifest_path = Path(work_dir) / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), "--manifest", str(manifest_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(ROOT_DIR),
        timeout=SCAN_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "").strip()[-3000:]
        raise RuntimeError(f"Pipeline exited with code {result.returncode}.\n\n{tail}")

    analysis = json.loads(ANALYSIS_JSON.read_text(encoding="utf-8"))
    got_id = analysis.get("scan_meta", {}).get("scan_id")
    if got_id != manifest["scan_id"]:
        # Someone else's scan result; never show it as ours.
        raise RuntimeError("analysis.json does not belong to this scan (scan id mismatch).")
    return analysis


def scan_uploads(uploads, progress=None):
    """Scan [(display_name, bytes), ...] with the existing pipeline.

    Returns the analysis dict written by backend/report.py for this scan.
    """
    progress = progress or (lambda msg: None)
    if not uploads:
        raise ValueError("No documents selected.")

    scan_id = uuid.uuid4().hex
    _acquire_lock()
    work_dir = tempfile.mkdtemp(prefix="ghosttrace_upload_")
    try:
        progress(f"Staging {len(uploads)} document(s) in a private temp folder...")
        entries = []
        for i, (name, data) in enumerate(uploads):
            ext = Path(name).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                raise ValueError(f"Unsupported file type: {name}")
            # On-disk name is generated, never taken from the client, so a
            # crafted filename can't escape work_dir or clobber anything.
            path = Path(work_dir) / f"{i:03d}{ext}"
            path.write_bytes(data)
            entries.append({"path": str(path), "name": name})

        progress("Running GhostTrace pipeline (extract -> classify -> score -> remediate)...")
        analysis = _run_pipeline(
            {
                "scan_id": scan_id,
                "source": "upload",
                "include_cookies": False,
                "files": entries,
            },
            work_dir,
        )
        progress("Loading results...")
        return analysis
    finally:
        # Only ever removes the directory created above.
        shutil.rmtree(work_dir, ignore_errors=True)
        _release_lock()


def scan_demo_folder(progress=None):
    """The original behaviour: scan demo_data/ (plus local browser cookies)."""
    progress = progress or (lambda msg: None)
    scan_id = uuid.uuid4().hex
    _acquire_lock()
    work_dir = tempfile.mkdtemp(prefix="ghosttrace_demo_")
    try:
        progress("Running GhostTrace pipeline on demo_data...")
        return _run_pipeline(
            {"scan_id": scan_id, "source": "demo_folder", "include_cookies": True},
            work_dir,
        )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
        _release_lock()
