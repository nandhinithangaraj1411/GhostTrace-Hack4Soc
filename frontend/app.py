import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="GhostTrace", page_icon="👻", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "selected_finding" not in st.session_state:
    st.session_state.selected_finding = None

if "selected_finding_idx" not in st.session_state:
    st.session_state.selected_finding_idx = None

if "scanned" not in st.session_state:
    st.session_state.scanned = False

st.markdown("""
<style>
    .stApp { background: #0b0b0b; color: #ffb366; }
    .main-title { font-size: 3rem; font-weight: 900; color: #ff8c1a; margin-bottom: 0; text-shadow: 0 0 18px rgba(255, 140, 26, 0.18); }
    .sub-title { font-size: 1rem; color: #ffb366; margin-top: 0.15rem; }
    .team-badge { display: inline-block; padding: 0.25rem 0.65rem; border-radius: 999px; background: #2a1200; color: #ffcc99; border: 1px solid #6b2f00; font-size: 0.8rem; }
    .panel-box, .sim-box, .white-box, .rem-box { background: #121212; border: 1px solid #2c1b10; border-radius: 18px; padding: 1rem 1.1rem; box-shadow: 0 0 0 1px rgba(255,140,26,0.05); }
    .section-title { color: #ff8c1a; font-weight: 800; font-size: 1.2rem; margin-bottom: 0.25rem; }
    .white-box, .white-box p, .white-box div, .white-box span { color: #ffd7b3 !important; }
    div[data-testid="stSidebar"] { background: #111111; border-right: 1px solid #2a2a2a; }
    .stButton > button { background: #1a1007; color: #ffcc99; border: 1px solid #ff8c1a; border-radius: 12px; padding: 0.5rem 0.9rem; font-weight: 700; transform: none !important; box-shadow: none !important; }
    .stButton > button:hover { background: #ff8c1a; color: #111111; border-color: #ff8c1a; transform: none !important; }
    .stButton > button:focus, .stButton > button:active { background: #ff8c1a !important; color: #111111 !important; border-color: #ffcc99 !important; transform: none !important; box-shadow: 0 0 0 2px rgba(255, 140, 26, 0.25) !important; }
    [data-testid="stMetricLabel"] { color: #ffb366 !important; }
    [data-testid="stMetricValue"] { color: #ff8c1a !important; }
    [data-testid="stMetricDelta"] { color: #ffd7b3 !important; }
    .sim-highlight, .sim-target-box, .step-chain, .rem-card { width: 100%; box-sizing: border-box; }
    .sim-highlight { background: linear-gradient(135deg, #1a0f08 0%, #241107 100%); border: 1px solid #ff8c1a; border-radius: 18px; padding: 1.1rem 1.2rem; margin-bottom: 1rem; box-shadow: 0 0 0 1px rgba(255, 140, 26, 0.15), 0 0 22px rgba(255, 140, 26, 0.08); }
    .sim-icon { font-size: 2rem; margin-bottom: 0.35rem; }
    .sim-headline { font-size: 1.2rem; font-weight: 800; color: #ffcc99; line-height: 1.45; }
    .sim-subline { margin-top: 0.4rem; color: #ffb366; font-size: 0.92rem; }
    .sim-target-box { background: #161616; border: 1px solid #2c1b10; border-radius: 16px; padding: 0.85rem 1rem; margin-top: 0.8rem; }
    .sim-label { color: #ff8c1a; font-weight: 800; font-size: 1rem; margin-bottom: 0.35rem; }
    .sim-target-value { color: #ffd7b3; font-size: 1.1rem; font-weight: 700; word-break: break-word; }
    .step-chain { display: flex; flex-direction: row; flex-wrap: wrap; gap: 0.65rem; width: 100%; align-items: center; background: #151515; border: 1px solid #2c1b10; border-radius: 16px; padding: 0.85rem 0.95rem; box-sizing: border-box; }
    .step-pill { background: #ff8c1a; color: #111111; font-weight: 800; border-radius: 999px; padding: 0.45rem 0.8rem; white-space: nowrap; }
    .step-arrow { color: #ffb366; font-size: 1.1rem; font-weight: 900; line-height: 1; }
    .rem-grid { display: grid; grid-template-columns: 1fr; gap: 0.9rem; margin-top: 0.8rem; }
    .rem-card { background: linear-gradient(135deg, #120c07 0%, #17110a 100%); border: 1px solid #ff8c1a; border-radius: 18px; padding: 1rem 1.1rem; box-shadow: 0 0 0 1px rgba(255, 140, 26, 0.12), 0 0 18px rgba(255, 140, 26, 0.06); }
    .rem-title { color: #ffcc99; font-size: 1.05rem; font-weight: 800; margin-bottom: 0.4rem; }
    .rem-desc { color: #ffd7b3; font-size: 0.95rem; line-height: 1.5; margin-top: 0.25rem; }
    .rem-tag { display: inline-block; margin-bottom: 0.55rem; padding: 0.25rem 0.6rem; border-radius: 999px; background: #2a1200; border: 1px solid #ff8c1a; color: #ffcc99; font-size: 0.78rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-title">GhostTrace</div>
<div class="sub-title">Dark privacy forensics dashboard</div>
<span class="team-badge">Cooper Trio</span>
""", unsafe_allow_html=True)

DATA_PATH = Path("../shared/analysis.json")
st.write("FILE EXISTS:", DATA_PATH.exists())
st.write("ABS PATH:", DATA_PATH.resolve())
st.write("SCANNED:", st.session_state.scanned)

def load_data():
    if DATA_PATH.exists():
        try:
            return json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def get_findings(data):
    raw = data.get("findings", [])
    return raw if isinstance(raw, list) else []

def normalize_remediations(remediations):
    normalized = []
    for item in remediations:
        if isinstance(item, dict):
            issue = item.get("issue") or item.get("title") or "Remediation"
            action = item.get("action") or item.get("description") or ""
            reason = item.get("reason") or ""
            act = item.get("act") or "DPDP Act, 2023"
            principle = item.get("principle") or ""
            obligation = item.get("obligation") or ""
        else:
            issue = str(item)
            action = ""
            reason = ""
            act = "DPDP Act, 2023"
            principle = ""
            obligation = ""
        low = issue.lower()
        if not action:
            if "email" in low:
                action = "Remove email from public documents"
                reason = "Reduces exposure and limits unnecessary processing."
                principle = "Data minimization, storage limitation"
                obligation = "Collect and retain only what is necessary for the stated purpose"
            elif "name" in low:
                action = "Anonymize author metadata"
                reason = "Reduces identity linking across public sources."
                principle = "Data minimization, purpose limitation"
                obligation = "Process personal data only for a clear, defined purpose"
            elif "phone" in low:
                action = "Remove phone numbers from public records"
                reason = "Prevents smishing and call-based scams."
                principle = "Data minimization, security safeguards"
                obligation = "Protect personal data from unauthorized access or misuse"
            elif "address" in low or "location" in low:
                action = "Redact address details from shared files"
                reason = "Reduces physical-location exposure."
                principle = "Data minimization, security safeguards"
                obligation = "Avoid unnecessary disclosure of personal data"
            else:
                action = "Limit exposure and remove the sensitive field"
                reason = "Reduces the chance of profile matching and abuse."
                principle = "Security safeguards"
                obligation = "Use reasonable safeguards to prevent misuse"
        normalized.append({"issue": issue, "act": act, "principle": principle, "obligation": obligation, "action": action, "reason": reason})
    return normalized

def build_chain(kind):
    k = str(kind).lower()
    if k == "email": return ["EMAIL", "phishing lure", "credential capture", "account takeover"]
    if k in ["phone", "phone_number", "mobile"]: return ["PHONE", "smishing", "social engineering", "fraud"]
    if k in ["address", "location", "gps"]: return ["LOCATION", "tracking", "targeting", "privacy exposure"]
    if k in ["aadhaar", "aadhar", "aadhaar number", "aadhar number"]: return ["AADHAAR", "KYC impersonation", "identity misuse", "fraud"]
    if k in ["token", "cookie", "session", "session_token"]: return ["TOKEN", "session hijack", "account access", "unauthorized login"]
    if k == "url": return ["URL", "tracking link", "profile enrichment", "osint linking"]
    if k == "software": return ["SOFTWARE", "app fingerprinting", "usage profiling", "behavior inference"]
    if k in ["timestamp", "date", "datetime"]: return ["TIMESTAMP", "activity timeline", "behavior tracking", "pattern inference"]
    if k in ["camera_make", "camera_model"]: return ["CAMERA METADATA", "device fingerprinting", "photo provenance", "source tracing"]
    if k in ["exif", "metadata"]: return ["METADATA", "photo tracing", "location leak", "identity linking"]
    return [k.upper() if k else "UNKNOWN", "profile matching", "trust abuse", "potential fraud"]

def threshold(score):
    if score < 5: return ("Low", "#1D9E75", "🟢")
    if score <= 8: return ("Medium", "#EF9F27", "🟡")
    return ("High", "#E24B4A", "🔴")

def trim(text, limit):
    text = str(text or "")
    return text if len(text) <= limit else text[:limit - 3] + "..."

def ring_html(score, title, subtitle, ring_color, risk_label, risk_emoji, files_count, findings_count, small_label):
    score = int(score) if score is not None else 0
    title = trim(title, 14)
    subtitle = trim(subtitle, 22)
    circumference = 339.3
    fill_len = (score / 100) * circumference
    gap_len = circumference - fill_len
    return f"""
    <div style="background:#0F172A;border:0.5px solid #1E293B;border-radius:16px;padding:0.95rem 1rem;text-align:center;font-family:system-ui,sans-serif;color:#F8FAFC;width:100%;box-sizing:border-box;overflow:hidden;">
        <div style="font-size:12px;font-weight:700;color:#94A3B8;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.45rem;">{small_label}</div>
        <svg viewBox="0 0 140 140" width="170" height="170" style="display:block;margin:0 auto;">
            <circle cx="70" cy="70" r="54" fill="none" stroke="#1E293B" stroke-width="12"/>
            <circle cx="70" cy="70" r="54" fill="none" stroke="{ring_color}" stroke-width="12" stroke-linecap="round" stroke-dasharray="{fill_len:.1f} {gap_len:.1f}" transform="rotate(-90 70 70)"/>
            <text x="70" y="64" text-anchor="middle" font-size="16" font-weight="800" fill="#F8FAFC">{title}</text>
            <text x="70" y="80" text-anchor="middle" font-size="9" fill="#94A3B8">{subtitle}</text>
            <text x="70" y="93" text-anchor="middle" font-size="10" fill="#CBD5E1">{risk_emoji} {risk_label.upper()}</text>
        </svg>
        <div style="display:inline-block;margin:0.1rem 0 0.6rem;padding:3px 12px;border-radius:999px;background:{ring_color}22;border:1px solid {ring_color};color:{ring_color};font-size:12px;font-weight:700;">Score: {score}/100</div>
        <div style="display:flex;justify-content:center;gap:1.3rem;border-top:0.5px solid #1E293B;padding-top:0.72rem;margin-top:0.1rem;">
            <div><p style="margin:0;font-size:11px;color:#64748B;text-transform:uppercase;">Files</p><p style="margin:0;font-size:20px;font-weight:700;color:#F8FAFC;">{files_count}</p></div>
            <div style="width:0.5px;background:#1E293B;"></div>
            <div><p style="margin:0;font-size:11px;color:#64748B;text-transform:uppercase;">Findings</p><p style="margin:0;font-size:20px;font-weight:700;color:#F8FAFC;">{findings_count}</p></div>
        </div>
    </div>
    """

with st.sidebar:
    st.markdown("## Navigation")
    if st.button("Dashboard", use_container_width=True): st.session_state.page = "Dashboard"
    if st.button("Remediation", use_container_width=True): st.session_state.page = "Remediation"
    st.markdown("---")
    folder = st.text_input("Demo folder", value="demo_data")
    scan_clicked = st.button("Scan", use_container_width=True)

if scan_clicked:
    st.session_state.scanned = True
    st.session_state.page = "Dashboard"
    st.session_state.selected_finding = None
    st.session_state.selected_finding_idx = None
    st.rerun()

data = load_data() if st.session_state.scanned else {}
summary = data.get("summary", {})
findings = get_findings(data) if st.session_state.scanned else []
files_count = summary.get("total_files", 0)
findings_count = summary.get("total_findings", len(findings))
score = int(data.get("risk_score", data.get("privacy_score", 0)) or 0)
score_label = data.get("risk_level", "Unknown")
user_label, user_color, user_emoji = threshold(score)

if st.session_state.page == "Dashboard":
    if not st.session_state.scanned:
        st.markdown('<div class="white-box">Choose a demo folder and press Scan to load analysis.json.</div>', unsafe_allow_html=True)
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Risk Score", f"{score}/100", score_label)
        c2.metric("Files Scanned", files_count)
        c3.metric("Findings", findings_count)
        st.markdown("---")
        st.subheader("🔎 Privacy Findings Breakdown")

        emails = []
        phones = []
        aadhaars = []
        tokens = []
        cookies = []
        metadata = []

        for item in findings:

            kind = item.get("kind", "").lower()

            if kind == "email":
                emails.append(item)

            elif kind == "phone":
                phones.append(item)

            elif kind in ["aadhaar", "aadhar"]:
                aadhaars.append(item)

            elif kind == "token":
                tokens.append(item)

            elif kind in ["cookie", "cookie_domain"]:
                cookies.append(item)

            else:
                metadata.append(item)

        col1, col2 = st.columns(2)

        with col1:

            if emails:
                    st.subheader(f"📧 Emails ({len(set(item['value'] for item in emails))} unique)")

                    unique_emails = sorted(
                        set(item["value"] for item in emails)
                    )

                    for value in unique_emails:
                        st.code(value)

            if phones:
                st.subheader(f"📱 Phone Numbers ({len(set(item['value'] for item in phones))} unique)")

                unique_phones = sorted(
                    set(item["value"] for item in phones)
                )

                for value in unique_phones:
                    st.code(value)

            if aadhaars:
                st.subheader(f"🪪 Aadhaar Numbers ({len(set(item['value'] for item in aadhaars))} unique)")

                unique_aadhaars = sorted(
                    set(item["value"] for item in aadhaars)
                )

                for value in unique_aadhaars:
                    st.code(value)

        with col2:

            if tokens:
                st.subheader(f"🔑 Tokens ({len(set(item['value'] for item in tokens))} unique)")

                unique_tokens = sorted(
                    set(item["value"] for item in tokens)
                )

                for value in unique_tokens:
                    st.code(value)

            if cookies:
                with st.expander(f"🍪 Cookies ({len(cookies)})"):
                    for item in cookies:
                        st.code(
                            f"{item['value']} : {item.get('count', 0)}"
                        )

            if metadata:
                with st.expander(f"📷 Metadata ({len(metadata)})"):
                    for item in metadata:
                        st.code(
                            f"{item['kind']} : {item['value']}"
                        )

        st.markdown("---")
        left, right = st.columns([1.05, 1])

        with left:
            st.markdown('<div class="panel-box">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Folder Scan</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="white-box">Current folder: <b>{folder}</b></div>', unsafe_allow_html=True)
            if findings:
                st.markdown('<div class="section-title">Detected items</div>', unsafe_allow_html=True)
                cols = st.columns(2)
                for i, item in enumerate(findings[:40]):
                    col = cols[i % 2]
                    kind = str(item.get("kind", "item")).upper()
                    value = trim(item.get("value", ""), 28)
                    with col:
                        if st.button(f"{kind} • {value}", key=f"finding_{i}", use_container_width=True):
                            st.session_state.selected_finding = item
                            st.session_state.selected_finding_idx = i
                            st.rerun()
            else:
                st.markdown('<div class="white-box">No findings yet. Add fake findings in analysis.json to activate the simulator.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with right:
            selected = st.session_state.selected_finding
            if selected:
                kind = str(selected.get("kind", "unknown")).lower()
                value = str(selected.get("value", ""))
                category = str(selected.get("category", "unknown"))
                risk = int(selected.get("risk", 0))
                ideal_score = max(0, risk - 1)
                ideal_label, ideal_color, ideal_emoji = threshold(ideal_score)

                components.html(ring_html(risk, value, f"{kind.upper()} • {category}", user_color, user_label, user_emoji, files_count, findings_count, "Selected Finding"), height=430, scrolling=False)
                components.html(ring_html(ideal_score, "Ideal", "should be lower", ideal_color, ideal_label, ideal_emoji, files_count, findings_count, "General Risk"), height=430, scrolling=False)
            else:
                components.html(ring_html(0, "No selection", "click a finding", "#1D9E75", "Low", "🟢", files_count, findings_count, "Selected Finding"), height=430, scrolling=False)
                components.html(ring_html(0, "Ideal", "should be lower", "#1D9E75", "Low", "🟢", files_count, findings_count, "General Risk"), height=430, scrolling=False)

            st.markdown('<div class="panel-box" style="margin-top: 1rem;">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Selected Finding</div>', unsafe_allow_html=True)
            if selected:
                kind = str(selected.get("kind", "unknown")).lower()
                value = str(selected.get("value", ""))
                category = str(selected.get("category", "unknown"))
                risk = selected.get("risk", 0)
                st.markdown(f'<div class="sim-highlight"><div class="sim-icon">🕵️</div><div class="sim-headline">{value}</div><div class="sim-subline">Selected finding: <b>{kind.upper()}</b> • Category: <b>{category}</b> • Risk: <b>{risk}</b></div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="white-box">Click an item on the left to see details.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        selected = st.session_state.selected_finding
        st.markdown('<div class="panel-box" style="margin-top: 1rem;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Attack Simulation</div>', unsafe_allow_html=True)
        if selected:
            kind = str(selected.get("kind", "unknown")).lower()
            value = str(selected.get("value", ""))
            category = str(selected.get("category", "unknown"))
            risk = selected.get("risk", 0)
            chain = build_chain(kind)
            headline_map = {
                "email": f"📧 Email exposure: {value} can be used in phishing or account linking.",
                "phone": f"📱 Phone exposure: {value} can be used for smishing or call scams.",
                "address": f"📍 Address exposure: {value} can reveal residence or office information.",
                "location": f"📍 Location exposure: {value} can reveal movement or presence history.",
                "gps": f"📍 GPS exposure: {value} can reveal location trails.",
                "aadhaar": f"🪪 Identity risk: {value} can support KYC impersonation or fraud.",
                "aadhar": f"🪪 Identity risk: {value} can support KYC impersonation or fraud.",
                "token": f"🔑 Token exposure: {value} can enable session hijacking or unauthorized login.",
                "cookie": f"🔑 Cookie exposure: {value} can enable session hijacking or unauthorized login.",
                "url": f"🌐 URL exposure: {value} can support tracking or OSINT linking.",
                "software": f"💻 Software trace: {value} can reveal app usage and device fingerprinting.",
                "timestamp": f"⏱ Timestamp trace: {value} can reveal activity timing and behavior patterns.",
                "camera_make": f"📷 Camera metadata: {value} can reveal device provenance.",
                "camera_model": f"📷 Camera metadata: {value} can reveal device provenance.",
                "exif": f"📷 EXIF metadata: {value} can expose source and context.",
            }
            headline = headline_map.get(kind, f"🕵️ OSINT risk: {value} can be linked across public sources.")
            st.markdown(f'<div class="sim-highlight"><div class="sim-icon">🕵️</div><div class="sim-headline">{headline}</div><div class="sim-subline">Selected finding: <b>{kind.upper()}</b> • Category: <b>{category}</b> • Risk: <b>{risk}</b></div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sim-target-box"><div class="sim-label">Target</div><div class="sim-target-value">{value}</div></div>', unsafe_allow_html=True)
            st.markdown('<div class="sim-label" style="margin-top: 1rem;">Attack Simulation</div>', unsafe_allow_html=True)
            flow_html = '<div class="step-chain">'
            for i, step in enumerate(chain):
                flow_html += f'<div class="step-pill">{step}</div>'
                if i < len(chain) - 1:
                    flow_html += '<div class="step-arrow">➜</div>'
            flow_html += '</div>'
            st.markdown(flow_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="white-box">Click an item on the left to generate the attack simulation.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "Remediation":
    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Remediation</div>', unsafe_allow_html=True)
    if st.session_state.scanned:
        remediations = data.get("recommendations", data.get("remediations", []))
        normalized = normalize_remediations(remediations)
        if normalized:
            st.markdown('<div class="rem-grid">', unsafe_allow_html=True)
            for item in normalized:
                st.markdown(f"""
                <div class="rem-card">
                    <div class="rem-tag">{item['act']}</div>
                    <div class="rem-title">{item['issue']}</div>
                    <div class="rem-desc"><b>DPDP principle:</b> {item['principle']}</div>
                    <div class="rem-desc"><b>Obligation:</b> {item['obligation']}</div>
                    <div class="rem-desc"><b>Do this:</b> {item['action']}</div>
                    <div class="rem-desc"><b>Why:</b> {item['reason']}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="white-box">No remediation suggestions yet. Add them to analysis.json.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="white-box">Scan first to load remediation content.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)