def build_timeline(files, findings):
    timeline = []

    for f in files:
        timeline.append({
            "time": f.get("modified", 0),
            "event": "file_scanned",
            "source_file": f.get("path", ""),
            "details": f.get("name", "")
        })

    for item in findings:
        timeline.append({
            "time": 0,
            "event": "sensitive_data_found",
            "source_file": item.get("source_file", ""),
            "details": f"{item.get('kind', '')}: {item.get('value', '')}"
        })

    timeline.sort(key=lambda x: x["time"])
    return timeline