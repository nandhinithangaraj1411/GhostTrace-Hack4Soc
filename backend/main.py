import json
import subprocess
from pathlib import Path

print("Running GhostTrace Pipeline...")

# Run scanner first
subprocess.run(["python", "backend/scanner/scanner.py"])

# Then analyzer
subprocess.run(["python", "backend/analyzer/analyzer.py"])

print("Analysis complete!")
print("Check shared/analysis.json")