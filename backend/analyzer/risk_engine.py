def calculate_risk(scan_data):

    score = 0

    emails = scan_data.get("emails", [])
    phones = scan_data.get("phones", [])
    aadhaars = scan_data.get("aadhaars", [])
    urls = scan_data.get("urls", [])
    tokens = scan_data.get("tokens", [])
    docs = scan_data.get("documents", [])
    photos = scan_data.get("photos", [])
    cookies = scan_data.get("cookies", [])
    gps = scan_data.get("gps", [])

    if isinstance(photos, int):
        photo_count = photos
    else:
        photo_count = len(photos)

    if isinstance(gps, int):
        gps_count = gps
    else:
        gps_count = len(gps)

    score += len(emails) * 2
    score += len(phones) * 3
    score += len(aadhaars) * 12
    score += len(urls) * 3
    score += len(tokens) * 6
    score += len(docs) * 2
    score += photo_count * 2
    score += gps_count * 8
    score += len(cookies) * 2

    if score > 100:
        score = 100

    if score >= 70:
        level = "HIGH"

    elif score >= 35:
        level = "MEDIUM"

    else:
        level = "LOW"

    return {
        "risk_score": score,
        "risk_level": level
    }