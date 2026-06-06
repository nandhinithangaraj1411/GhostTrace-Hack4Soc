import json

from digital_twin import generate_twin

with open("../../shared/scan.json") as f:

    data = json.load(f)

print(
    generate_twin(data)
)