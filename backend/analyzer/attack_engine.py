def generate_attack_paths(scan_data):

    attacks = []

    if len(scan_data.get("emails", [])) > 0:

        attacks.append("Account Recovery Risk")

    if len(scan_data.get("pan", [])) > 0:

        attacks.append("Identity Theft Risk")

    if len(scan_data.get("gps", [])) > 0:

        attacks.append("Location Profiling Risk")

    return attacks

    attacks = []

    if (

        len(scan_data.get("emails", [])) > 0

        and

        len(scan_data.get("phones", [])) > 0
    ):

        attacks.append(

            "Account Recovery Risk"
        )

    if len(scan_data.get("pan", [])) > 0:

        attacks.append(

            "Identity Theft Risk"
        )

    if len(scan_data.get("gps", [])) > 0:

        attacks.append(

            "Location Profiling Risk"
        )

    return attacks