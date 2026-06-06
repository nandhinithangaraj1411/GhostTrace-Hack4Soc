import os

print("Running GhostTrace Pipeline...")

os.system("python backend/analyzer/analyzer.py")

print("Analysis complete!")
print("Check shared/analysis.json")