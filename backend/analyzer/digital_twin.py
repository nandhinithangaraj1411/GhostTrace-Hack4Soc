def generate_twin(scan_data):

    twin = {}

    gps = scan_data.get("gps", [])
    docs = scan_data.get("documents", [])
    photos = scan_data.get("photos", [])
    tokens = scan_data.get("tokens", [])
    aadhaars = scan_data.get("aadhaars", [])

    if isinstance(gps, int):
        gps_count = gps
    else:
        gps_count = len(gps)

    if isinstance(photos, int):
        photo_count = photos
    else:
        photo_count = len(photos)

    twin["traveler"] = gps_count > 0

    twin["student"] = len(docs) > 2

    twin["financial_activity"] = (
        "HIGH"
        if len(aadhaars) > 0
        else "LOW"
    )

    twin["profile"] = "General User"

    if len(tokens) > 3:
        twin["profile"] = "Developer / Technical User"

    if photo_count > 0:
        twin["profile"] = "Social / Active User"

    return twin