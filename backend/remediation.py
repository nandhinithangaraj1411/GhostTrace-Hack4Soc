def build_remediations(findings):
    remediations = []

    for item in findings:
        category = str(item.get("category", "")).strip()
        source_file = item.get("source_file", "")
        kind = str(item.get("kind", "")).strip().lower()

        # classify_finding() returns broad categories (identity, contact,
        # government_id, ...), not "<Thing> Exposure" strings, so match on
        # the specific `kind` instead - it's what actually distinguishes
        # an email from a phone number from a token.
        if kind == "email":
            act = "DPDP Act, 2023"
            principle = "Data minimization"
            obligation = "Avoid unnecessary disclosure of personal data"
            action = "Remove email addresses from public documents"
            reason = "Reduces phishing risk"
        elif kind == "phone":
            act = "DPDP Act, 2023"
            principle = "Security safeguards"
            obligation = "Protect personal data from unauthorized access or misuse"
            action = "Redact phone numbers before sharing"
            reason = "Prevents smishing attacks"
        elif kind == "aadhaar":
            act = "DPDP Act, 2023"
            principle = "Data minimization and purpose limitation"
            obligation = "Use sensitive personal data only for a lawful purpose"
            action = "Mask Aadhaar numbers"
            reason = "Prevents identity theft"
        elif kind == "pan":
            act = "DPDP Act, 2023"
            principle = "Data minimization and purpose limitation"
            obligation = "Use sensitive personal data only for a lawful purpose"
            action = "Mask or redact PAN numbers"
            reason = "Prevents identity and financial fraud"
        elif kind == "token":
            act = "DPDP Act, 2023"
            principle = "Security safeguards and accountability"
            obligation = "Prevent unauthorized access and account compromise"
            action = "Rotate exposed tokens"
            reason = "Prevents unauthorized access"
        elif kind == "cookie":
            act = "DPDP Act, 2023"
            principle = "Storage limitation and security safeguards"
            obligation = "Limit retention and reduce session abuse"
            action = "Clear unnecessary cookies"
            reason = "Reduces tracking and session abuse"
        else:
            act = "DPDP Act, 2023"
            principle = "Data minimization"
            obligation = "Limit processing to necessary personal data"
            action = "Review file and remove unnecessary personal data"
            reason = "Reduces exposure"

        remediations.append({
            "source_file": source_file,
            "kind": kind,
            "category": category,
            "act": act,
            "principle": principle,
            "obligation": obligation,
            "action": action,
            "reason": reason
        })

    return remediations