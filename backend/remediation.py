def build_remediations(findings):
    remediations = []

    for item in findings:
        category = item.get("category", "")
        source_file = item.get("source_file", "")
        kind = item.get("kind", "")

        if category == "credentials":
            action = "remove or rotate credentials"
        elif category == "government_id":
            action = "move sensitive ID to encrypted vault"
        elif category == "location":
            action = "strip metadata or remove location traces"
        elif category == "financial":
            action = "redact financial data"
        elif category == "contact":
            action = "review and minimize exposure"
        else:
            action = "review file and remove unnecessary personal data"

        remediations.append({
            "source_file": source_file,
            "kind": kind,
            "category": category,
            "action": action
        })

    return remediations