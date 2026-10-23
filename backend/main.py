import subprocess
import sys
from pathlib import Path

# backend/scanner.py only lists files - extraction, classification, scoring,
# and writing scan.json/analysis.json all live in backend/report.py. That is
# the single real pipeline entry point; run it directly instead of the old
# (nonexistent) backend/scanner/scanner.py + analyzer.py two-step split.
REPORT_SCRIPT = Path(__file__).resolve().parent / "report.py"

print("Running GhostTrace Pipeline...")

result = subprocess.run([sys.executable, str(REPORT_SCRIPT)])

if result.returncode != 0:
    print("GhostTrace pipeline failed - see errors above.")
    sys.exit(result.returncode)

print("Analysis complete!")
print("Check shared/analysis.json")