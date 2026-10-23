import json

from attack_engine import generate_attack_paths as generate_attacks

with open("../../shared/scan.json") as f:

    data = json.load(f)

print(
    generate_attacks(data)
)