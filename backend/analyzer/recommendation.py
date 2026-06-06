def generate_recommendations(scan_data):

    recs = []

    if len(scan_data.get("gps", [])) > 0:

        recs.append("Remove image metadata")

    if len(scan_data.get("documents", [])) > 0:

        recs.append("Encrypt sensitive documents")

    if len(scan_data.get("emails", [])) > 0:

        recs.append("Enable 2FA on linked accounts")

    return recs