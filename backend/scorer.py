def calculate_privacy_score(findings):
    total = 0
    for item in findings:
        total += item.get("risk", 0)

    score = min(100, total)
    return score