import json

from risk_engine import calculate_risk

with open("../../shared/scan.json") as f:

    data = json.load(f)

result = calculate_risk(data)

print(result)