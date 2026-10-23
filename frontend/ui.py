"""Shared look-and-feel for the GhostTrace Streamlit app.

Design tokens, CSS, small HTML components, value masking and Altair chart
builders. No data is fetched or computed here beyond formatting what the
scan results already contain.
"""

import html
import re

import altair as alt
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------- tokens
BG = "#080D18"
CARD = "#111827"
CARD_2 = "#0F172A"
BORDER = "#1F2937"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"
FAINT = "#64748B"
CYAN = "#38BDF8"
VIOLET = "#8B5CF6"
RED = "#F87171"
AMBER = "#FBBF24"
GREEN = "#34D399"
SLATE = "#64748B"

FONT = "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif"

SEV_ORDER = ["High", "Medium", "Low"]
SEV_COLORS = {"High": RED, "Medium": AMBER, "Low": GREEN}
SEV_BADGE = {"High": "red", "Medium": "yellow", "Low": "green"}

STATUS_LABEL = {"scanned": "Scanned", "failed": "Failed", "unsupported": "Unsupported"}
STATUS_COLORS = {"Scanned": GREEN, "Failed": RED, "Unsupported": AMBER, "Scanned with warning": AMBER}

esc = html.escape


def finding_severity(risk):
    """Per-finding severity band from the classifier's risk weight.

    Same bands the dashboard has always used: < 5 Low, 5-8 Medium, > 8 High.
    """
    risk = int(risk or 0)
    if risk < 5:
        return "Low"
    if risk <= 8:
        return "Medium"
    return "High"


def score_color(level):
    return SEV_COLORS.get(level, SLATE)


# ------------------------------------------------------------------- CSS
CSS = f"""
<style>
.stApp {{ background: {BG}; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1360px; }}
html, body, .stApp {{ font-family: {FONT}; }}

section[data-testid="stSidebar"] {{ background: #0B1222; }}
section[data-testid="stSidebar"] .block-container {{ padding-top: 1.2rem; }}
section[data-testid="stSidebar"] .stButton button {{
    justify-content: flex-start; width: 100%; border: 1px solid transparent;
    background: transparent; color: {MUTED}; font-weight: 500; padding: 0.45rem 0.75rem;
}}
section[data-testid="stSidebar"] .stButton button > div {{ justify-content: flex-start; }}
section[data-testid="stSidebar"] .stButton button:hover {{ background: rgba(148,163,184,0.08); color: {TEXT}; }}
section[data-testid="stSidebar"] .stButton button[kind="primary"] {{
    background: rgba(56,189,248,0.10); color: {CYAN}; border: 1px solid rgba(56,189,248,0.25);
    font-weight: 600;
}}

div[data-testid="stExpander"] details {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; }}
div[data-testid="stExpander"] summary:hover {{ color: {CYAN}; }}

.gt-brand {{ display: flex; align-items: center; gap: 0.7rem; padding: 0.2rem 0.3rem 0.9rem; }}
.gt-brand-name {{ font-size: 1.2rem; font-weight: 700; color: {TEXT}; letter-spacing: -0.01em; line-height: 1.1; }}
.gt-brand-sub {{ font-size: 0.72rem; color: {MUTED}; letter-spacing: 0.08em; text-transform: uppercase; }}
.gt-nav-label {{ font-size: 0.7rem; color: {FAINT}; letter-spacing: 0.1em; text-transform: uppercase; margin: 0.6rem 0 0.3rem 0.3rem; }}

.gt-side-status {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; padding: 0.75rem 0.85rem; font-size: 0.82rem; color: {MUTED}; line-height: 1.5; }}
.gt-side-status b {{ color: {TEXT}; font-weight: 600; }}

.gt-eyebrow {{ font-size: 0.72rem; color: {CYAN}; letter-spacing: 0.12em; text-transform: uppercase; font-weight: 600; }}
.gt-h1 {{ font-size: 1.75rem; font-weight: 700; color: {TEXT}; letter-spacing: -0.02em; margin: 0.15rem 0 0.2rem; }}
.gt-sub {{ font-size: 0.95rem; color: {MUTED}; margin-bottom: 1.2rem; }}
.gt-h2 {{ font-size: 1.02rem; font-weight: 650; color: {TEXT}; margin: 0.2rem 0 0.15rem; }}
.gt-h2-sub {{ font-size: 0.82rem; color: {FAINT}; margin-bottom: 0.6rem; }}

.gt-card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px; padding: 1rem 1.15rem; }}
.gt-stat-label {{ display: flex; align-items: center; gap: 0.45rem; font-size: 0.74rem; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }}
.gt-dot {{ width: 8px; height: 8px; border-radius: 999px; display: inline-block; }}
.gt-stat-value {{ font-size: 1.95rem; font-weight: 700; color: {TEXT}; margin-top: 0.35rem; letter-spacing: -0.02em; font-variant-numeric: tabular-nums; }}
.gt-stat-value small {{ font-size: 0.95rem; color: {FAINT}; font-weight: 500; }}
.gt-stat-sub {{ font-size: 0.8rem; color: {FAINT}; margin-top: 0.15rem; }}

.gt-pill {{ display: inline-block; padding: 0.12rem 0.55rem; border-radius: 999px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.02em; white-space: nowrap; }}

.gt-row {{ display: flex; align-items: center; justify-content: space-between; gap: 0.8rem; padding: 0.55rem 0; border-bottom: 1px solid {BORDER}; }}
.gt-row:last-child {{ border-bottom: 0; }}
.gt-row-main {{ min-width: 0; }}
.gt-row-title {{ color: {TEXT}; font-size: 0.88rem; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.gt-row-meta {{ color: {FAINT}; font-size: 0.76rem; margin-top: 0.1rem; }}

.gt-kv {{ display: grid; grid-template-columns: 9.5rem 1fr; gap: 0.35rem 0.8rem; font-size: 0.86rem; }}
.gt-kv dt {{ color: {FAINT}; }}
.gt-kv dd {{ color: {TEXT}; margin: 0; word-break: break-word; }}

.gt-empty {{ text-align: center; padding: 2.6rem 1.5rem; background: {CARD}; border: 1px dashed #2B3A55; border-radius: 16px; }}
.gt-empty-title {{ font-size: 1.15rem; font-weight: 650; color: {TEXT}; margin-top: 0.8rem; }}
.gt-empty-body {{ font-size: 0.9rem; color: {MUTED}; max-width: 34rem; margin: 0.35rem auto 0; line-height: 1.55; }}

.gt-chain {{ display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; }}
.gt-chain span.step {{ background: rgba(139,92,246,0.12); border: 1px solid rgba(139,92,246,0.35); color: #C4B5FD; border-radius: 999px; padding: 0.15rem 0.6rem; font-size: 0.76rem; }}
.gt-chain span.arrow {{ color: {FAINT}; font-size: 0.8rem; }}

.gt-chip {{ display: inline-block; background: {CARD_2}; border: 1px solid {BORDER}; color: {MUTED}; border-radius: 6px; padding: 0.05rem 0.4rem; font-size: 0.74rem; font-family: 'Cascadia Mono', Consolas, monospace; }}
.gt-format {{ display: flex; gap: 0.6rem; align-items: baseline; padding: 0.35rem 0; border-bottom: 1px solid {BORDER}; font-size: 0.84rem; color: {MUTED}; }}
.gt-format:last-child {{ border-bottom: 0; }}
</style>
"""

LOGO_SVG = f"""<svg width="34" height="34" viewBox="0 0 32 32" aria-hidden="true">
<path d="M16 2.5 27.7 9.25v13.5L16 29.5 4.3 22.75V9.25Z" fill="{CARD}" stroke="{CYAN}" stroke-width="1.8" stroke-linejoin="round"/>
<circle cx="16" cy="16" r="7.5" fill="none" stroke="{CYAN}" stroke-opacity="0.35" stroke-width="1.4"/>
<circle cx="16" cy="16" r="3.6" fill="{VIOLET}"/></svg>"""

EMPTY_ICON = f"""<svg width="46" height="46" viewBox="0 0 32 32" aria-hidden="true">
<path d="M16 2.5 27.7 9.25v13.5L16 29.5 4.3 22.75V9.25Z" fill="none" stroke="{FAINT}" stroke-width="1.4" stroke-linejoin="round"/>
<circle cx="16" cy="16" r="3.4" fill="none" stroke="{CYAN}" stroke-width="1.4"/></svg>"""


def inject_css():
    st.html(CSS)


# ------------------------------------------------------------ components
def brand():
    st.html(
        f'<div class="gt-brand">{LOGO_SVG}<div>'
        f'<div class="gt-brand-name">GhostTrace</div>'
        f'<div class="gt-brand-sub">Privacy Intelligence</div></div></div>'
    )


def nav_label(text):
    st.html(f'<div class="gt-nav-label">{esc(text)}</div>')


def page_header(eyebrow, title, subtitle=""):
    st.html(
        f'<div class="gt-eyebrow">{esc(eyebrow)}</div>'
        f'<div class="gt-h1">{esc(title)}</div>'
        + (f'<div class="gt-sub">{esc(subtitle)}</div>' if subtitle else "")
    )


def section(title, subtitle=""):
    st.html(
        f'<div class="gt-h2">{esc(title)}</div>'
        + (f'<div class="gt-h2-sub">{esc(subtitle)}</div>' if subtitle else "")
    )


def pill(text, color):
    return (f'<span class="gt-pill" style="color:{color};background:{color}1A;'
            f'border:1px solid {color}55;">{esc(str(text))}</span>')


def stat_card(label, value, sub="", accent=CYAN, suffix=""):
    suffix_html = f"<small> {esc(suffix)}</small>" if suffix else ""
    st.html(
        f'<div class="gt-card"><div class="gt-stat-label">'
        f'<span class="gt-dot" style="background:{accent}"></span>{esc(label)}</div>'
        f'<div class="gt-stat-value">{esc(str(value))}{suffix_html}</div>'
        f'<div class="gt-stat-sub">{sub}</div></div>'
    )


def empty_state(title, body):
    st.html(
        f'<div class="gt-empty">{EMPTY_ICON}'
        f'<div class="gt-empty-title">{esc(title)}</div>'
        f'<div class="gt-empty-body">{esc(body)}</div></div>'
    )


def rows_card(rows):
    """rows: [(title, meta, right_html)] -> one card with divided rows."""
    inner = "".join(
        f'<div class="gt-row"><div class="gt-row-main"><div class="gt-row-title">{esc(t)}</div>'
        f'<div class="gt-row-meta">{esc(m)}</div></div><div>{r}</div></div>'
        for t, m, r in rows
    )
    st.html(f'<div class="gt-card" style="padding-top:0.4rem;padding-bottom:0.4rem;">{inner}</div>')


def kv_card(pairs):
    inner = "".join(f"<dt>{esc(k)}</dt><dd>{v}</dd>" for k, v in pairs)
    st.html(f'<div class="gt-card"><dl class="gt-kv">{inner}</dl></div>')


def chain_html(steps):
    parts = []
    for i, s in enumerate(steps):
        parts.append(f'<span class="step">{esc(s)}</span>')
        if i < len(steps) - 1:
            parts.append('<span class="arrow">→</span>')
    return f'<div class="gt-chain">{"".join(parts)}</div>'


def human_size(n):
    n = float(n or 0)
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


# --------------------------------------------------------------- masking
_KEEP_LAST4 = {"phone", "aadhaar", "pan", "account", "card", "bank"}
_UNMASKED = {"camera_make", "camera_model", "software"}  # device metadata, not personal


def _mask_chars(text, keep_last=0, keep_first=0):
    # Mask letters/digits but keep separators so the shape stays readable.
    chars = list(text)
    idx = [i for i, c in enumerate(chars) if c.isalnum()]
    keep = set(idx[:keep_first]) | set(idx[len(idx) - keep_last:] if keep_last else [])
    return "".join("•" if (i in idx and i not in keep) else c for i, c in enumerate(chars))


def mask_value(kind, value):
    v = str(value)
    k = str(kind).lower()
    if k in _UNMASKED or not v:
        return v
    if k == "email" and "@" in v:
        user, dom = v.split("@", 1)
        host, _, tld = dom.rpartition(".")
        return f"{user[:1]}•••@{host[:1]}•••.{tld}" if host else f"{user[:1]}•••@•••"
    if k == "url":
        m = re.match(r"(https?://)([^/?#]+)(.*)", v)
        if m:
            return m.group(1) + m.group(2) + ("/•••" if m.group(3).strip("/") else "")
    if k == "timestamp":
        return v[:10] + " ••:••:••" if len(v) > 10 else _mask_chars(v)
    if k in _KEEP_LAST4:
        return _mask_chars(v, keep_last=4)
    if k == "token":
        return _mask_chars(v, keep_first=3, keep_last=2)
    return _mask_chars(v, keep_first=1)


# ---------------------------------------------------------------- charts
def _style(chart, height):
    return (
        chart.properties(height=height, background="transparent", padding={"left": 4, "right": 12, "top": 8, "bottom": 4})
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor=MUTED, titleColor=FAINT, gridColor=BORDER, domainColor=BORDER,
            tickColor=BORDER, labelFont=FONT, titleFont=FONT, labelFontSize=12,
            titleFontSize=11, titleFontWeight=500, labelLimit=190,
        )
        .configure_legend(
            labelColor=MUTED, titleColor=FAINT, labelFont=FONT, titleFont=FONT,
            orient="bottom", direction="horizontal", symbolType="circle", titleFontWeight=500,
        )
    )


def _sev_scale():
    return alt.Scale(domain=SEV_ORDER, range=[SEV_COLORS[s] for s in SEV_ORDER])


def show_chart(chart):
    st.altair_chart(chart, theme=None, width="stretch")


def severity_chart(findings, height=220):
    counts = pd.DataFrame({
        "Severity": SEV_ORDER,
        "Findings": [sum(1 for f in findings if finding_severity(f.get("risk")) == s) for s in SEV_ORDER],
    })
    base = alt.Chart(counts).encode(
        y=alt.Y("Severity:N", sort=SEV_ORDER, title=None),
        x=alt.X("Findings:Q", title="Findings", axis=alt.Axis(tickMinStep=1, format="d")),
    )
    bars = base.mark_bar(cornerRadiusEnd=4, height=26).encode(
        color=alt.Color("Severity:N", scale=_sev_scale(), legend=None),
        tooltip=[alt.Tooltip("Severity:N"), alt.Tooltip("Findings:Q", format="d")],
    )
    labels = base.mark_text(align="left", dx=6, color=TEXT, font=FONT, fontSize=12).encode(text="Findings:Q")
    return _style(bars + labels, height)


def category_chart(findings, height=260):
    rows = [{"Category": str(f.get("category", "unknown")).replace("_", " "),
             "Severity": finding_severity(f.get("risk"))} for f in findings]
    df = pd.DataFrame(rows).groupby(["Category", "Severity"]).size().reset_index(name="Findings")
    order = df.groupby("Category")["Findings"].sum().sort_values(ascending=False).index.tolist()
    pick = alt.selection_point(fields=["Severity"], bind="legend")
    chart = alt.Chart(df).mark_bar(height=22).encode(
        y=alt.Y("Category:N", sort=order, title=None),
        x=alt.X("sum(Findings):Q", title="Findings", axis=alt.Axis(tickMinStep=1, format="d")),
        color=alt.Color("Severity:N", scale=_sev_scale(), title="Severity (click to highlight)"),
        order=alt.Order("Severity:N", sort="ascending"),
        opacity=alt.condition(pick, alt.value(1), alt.value(0.25)),
        tooltip=[alt.Tooltip("Category:N"), alt.Tooltip("Severity:N"), alt.Tooltip("Findings:Q", format="d")],
    ).add_params(pick)
    return _style(chart, max(height, 34 * len(order) + 60))


def document_chart(doc_results, findings, height=280):
    rows = []
    for d in doc_results:
        if d.get("status") != "scanned":
            continue
        doc_f = [f for f in findings if f.get("source_file") == d["source_file"]]
        for s in SEV_ORDER:
            n = sum(1 for f in doc_f if finding_severity(f.get("risk")) == s)
            if n:
                rows.append({"Document": d["source_file"], "Severity": s, "Findings": n,
                             "Score": d.get("privacy_score"), "Level": d.get("risk_level")})
    if not rows:
        return None
    df = pd.DataFrame(rows)
    order = (df.groupby("Document")["Score"].max().sort_values(ascending=False).index.tolist())
    pick = alt.selection_point(fields=["Severity"], bind="legend")
    chart = alt.Chart(df).mark_bar(height=22).encode(
        y=alt.Y("Document:N", sort=order, title=None),
        x=alt.X("sum(Findings):Q", title="Findings", axis=alt.Axis(tickMinStep=1, format="d")),
        color=alt.Color("Severity:N", scale=_sev_scale(), title="Severity (click to highlight)"),
        order=alt.Order("Severity:N", sort="ascending"),
        opacity=alt.condition(pick, alt.value(1), alt.value(0.25)),
        tooltip=[alt.Tooltip("Document:N"), alt.Tooltip("Severity:N"),
                 alt.Tooltip("Findings:Q", format="d"),
                 alt.Tooltip("Score:Q", title="Document score"), alt.Tooltip("Level:N", title="Document level")],
    ).add_params(pick)
    return _style(chart, max(height, 36 * len(order) + 60))


def document_score_chart(doc_results, height=260):
    rows = [{"Document": d["source_file"], "Score": d["privacy_score"], "Level": d["risk_level"]}
            for d in doc_results if d.get("status") == "scanned"]
    if not rows:
        return None
    df = pd.DataFrame(rows)
    order = df.sort_values("Score", ascending=False)["Document"].tolist()
    base = alt.Chart(df).encode(
        y=alt.Y("Document:N", sort=order, title=None),
        x=alt.X("Score:Q", title="Document score (0–100)", scale=alt.Scale(domain=[0, 100])),
    )
    bars = base.mark_bar(cornerRadiusEnd=4, height=20).encode(
        color=alt.Color("Level:N", scale=_sev_scale(), title="Document level"),
        tooltip=[alt.Tooltip("Document:N"), alt.Tooltip("Score:Q", title="Score"), alt.Tooltip("Level:N")],
    )
    labels = base.mark_text(align="left", dx=6, color=TEXT, font=FONT, fontSize=12).encode(text="Score:Q")
    rules = alt.Chart(pd.DataFrame({"x": [40, 70]})).mark_rule(color=FAINT, strokeDash=[3, 3]).encode(x="x:Q")
    return _style(bars + labels + rules, max(height, 34 * len(order) + 60))


def processing_chart(doc_results, height=200):
    labels = []
    for d in doc_results:
        label = STATUS_LABEL.get(d.get("status"), "Failed")
        if label == "Scanned" and d.get("warning"):
            label = "Scanned with warning"
        labels.append(label)
    order = ["Scanned", "Scanned with warning", "Failed", "Unsupported"]
    df = pd.DataFrame({"Status": order, "Documents": [labels.count(s) for s in order]})
    df = df[df["Documents"] > 0]
    base = alt.Chart(df).encode(
        y=alt.Y("Status:N", sort=order, title=None),
        x=alt.X("Documents:Q", title="Documents", axis=alt.Axis(tickMinStep=1, format="d")),
    )
    bars = base.mark_bar(cornerRadiusEnd=4, height=24).encode(
        color=alt.Color("Status:N", scale=alt.Scale(domain=order, range=[STATUS_COLORS[s] for s in order]), legend=None),
        tooltip=[alt.Tooltip("Status:N"), alt.Tooltip("Documents:Q", format="d")],
    )
    text = base.mark_text(align="left", dx=6, color=TEXT, font=FONT, fontSize=12).encode(text="Documents:Q")
    return _style(bars + text, max(height, 40 * len(df) + 50))
