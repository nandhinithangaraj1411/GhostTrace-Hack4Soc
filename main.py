import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT_SCRIPT = ROOT / "backend" / "report.py"

print("Running GhostTrace Pipeline...")

result = subprocess.run([sys.executable, str(REPORT_SCRIPT)])

if result.returncode != 0:
    print("GhostTrace pipeline failed - see errors above.")
    sys.exit(result.returncode)

print("Analysis complete!")
print("Check shared/analysis.json")