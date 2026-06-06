import streamlit as st
import json

st.set_page_config(layout="wide")

# Load analysis file
with open("shared/analysis.json", "r") as f:
    data = json.load(f)

# Sidebar Navigation
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Digital Twin", "Remediation", "Scan"]
)

# ---------------- DASHBOARD ----------------
if page == "Dashboard":

    summary = data.get("summary", {})

    st.title("GhostTrace")
    st.subheader("Local privacy forensics dashboard")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Risk Score", data.get("risk_score", 0))

    with c2:
        st.metric("Risk Level", data.get("risk_level", "UNKNOWN"))

    with c3:
        st.metric(
            "Files Scanned",
            summary.get("total_files", 0)
        )

    with c4:
        st.metric(
            "Findings",
            summary.get("total_findings", 0)
        )

    st.divider()

    st.header("Attack Paths")

    for attack in data.get("attack_paths", []):
        st.warning(attack)

# ---------------- DIGITAL TWIN ----------------
elif page == "Digital Twin":

    st.title("Digital Twin")

    twin = data.get("digital_twin", {})

    c1, c2 = st.columns(2)

    with c1:
        st.metric("Traveler", str(twin.get("traveler")))
        st.metric("Student", str(twin.get("student")))

    with c2:
        st.metric(
            "Financial Activity",
            twin.get("financial_activity", "UNKNOWN")
        )

        st.metric(
            "Profile",
            twin.get("profile", "UNKNOWN")
        )

    st.json(twin)

# ---------------- REMEDIATION ----------------
elif page == "Remediation":

    st.title("Recommendations")

    for rec in data.get("recommendations", []):
        st.success(rec)

# ---------------- SCAN ----------------
elif page == "Scan":

    st.title("Scan Control")

    st.info(
        "Run backend scanner and analyzer. "
        "Dashboard updates automatically."
    )

    st.code("python main.py")