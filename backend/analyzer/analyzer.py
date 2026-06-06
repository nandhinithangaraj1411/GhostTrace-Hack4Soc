import json

from risk_engine import calculate_risk
from digital_twin import generate_twin
from attack_engine import generate_attack_paths
from recommendation import generate_recommendations

INPUT_PATH = "shared/scan.json"
OUTPUT_PATH = "shared/analysis.json"


with open(INPUT_PATH, "r", encoding="utf-8") as f:
    scan_data = json.load(f)

risk = calculate_risk(scan_data)

twin = generate_twin(scan_data)

attacks = generate_attack_paths(scan_data)

recs = generate_recommendations(scan_data)


# ---------- Summary Stats ----------

total_files = (
    len(scan_data.get("documents", []))
    + len(scan_data.get("photos", []))
)

total_findings = (
    len(scan_data.get("emails", []))
    + len(scan_data.get("phones", []))
    + len(scan_data.get("gps", []))
    + len(scan_data.get("aadhaars", []))
    + len(scan_data.get("urls", []))
)

# ---------- Final Output ----------

final_output = {
    "summary": {
        "total_files": total_files,
        "total_findings": total_findings
    },

    "risk_score": risk["risk_score"],
    "risk_level": risk["risk_level"],

    "digital_twin": twin,

    "attack_paths": attacks,

    "recommendations": recs
}


with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=4)

print("analysis.json generated")
print("Files:", total_files)
print("Findings:", total_findings)