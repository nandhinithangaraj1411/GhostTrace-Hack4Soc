def classify_finding(kind, value, source_file=""):
    kind = kind.lower()

    if kind == "email":
        category = "identity"
        risk = 8
    elif kind == "phone":
        category = "contact"
        risk = 6
    elif kind == "aadhaar":
        category = "government_id"
        risk = 20
    elif kind in ["token", "cookie"]:
        category = "credentials"
        risk = 22
    elif kind in ["url"]:
        category = "behavioral"
        risk = 5
    elif kind in ["gps", "location"]:
        category = "location"
        risk = 15
    elif kind in ["bank", "card", "pan", "account"]:
        category = "financial"
        risk = 18
    elif kind in ["camera_make", "camera_model"]:
        category = "device"
        risk = 7

    elif kind in ["timestamp"]:
        category = "behavioral"
        risk = 5

    elif kind in ["software"]:
        category = "device"
        risk = 4

    elif kind in ["copyright", "artist", "name"]:
        category = "identity"
        risk = 6
    else:
        category = "identity"
        risk = 4

    return {
        "source_file": source_file,
        "kind": kind,
        "value": value,
        "category": category,
        "risk": risk
    }