import hashlib
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Sibling modules (ui, upload_scan) resolve however the app is launched.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import ui
import upload_scan
from ui import esc

st.set_page_config(page_title="GhostTrace", page_icon=":material/shield:", layout="wide")
ui.inject_css()

PAGES = [
    ("Overview", ":material/space_dashboard:"),
    ("Upload & Scan", ":material/upload_file:"),
    ("Findings", ":material/manage_search:"),
    ("Risk Analytics", ":material/insights:"),
    ("Remediation", ":material/build:"),
    ("Scan History", ":material/history:"),
]
PAGE_SIZE = 20
MAX_HISTORY = 10
# Widget keys that depend on the active scan's documents; cleared whenever
# the active scan changes so no filter refers to a file from another scan.
VIEW_KEYS = ["f_search", "f_sev", "f_docs", "f_sort", "f_page", "f_reveal",
             "rem_doc", "rem_sev", "doc_metric"]

# ------------------------------------------------------------------ state
defaults = {
    "page": "Overview",
    # Results of the scan currently being viewed. Pages render only from
    # this snapshot, never from shared/analysis.json, so stale results or
    # another session's scan can't leak in.
    "analysis": None,
    "active_id": None,
    # Scans run in this browser session (memory only, never written to disk).
    "history": [],
    # Uploaded documents waiting to be scanned: {key: {"name", "data", "error", "selected"}}
    "staged": {},
    "uploader_key": 0,
    "scan_error": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------------------------------------------- helpers
def go(page):
    st.session_state.page = page


def reset_view_state():
    for k in VIEW_KEYS:
        st.session_state.pop(k, None)


def set_active(entry):
    st.session_state.analysis = entry["analysis"] if entry else None
    st.session_state.active_id = entry["id"] if entry else None
    reset_view_state()


def record(label, analysis=None, error=None):
    entry = {
        "id": analysis["scan_meta"]["scan_id"] if analysis else f"failed-{time.time()}",
        "label": label,
        "time": time.time(),
        "ok": analysis is not None,
        "analysis": analysis,
        "error": error,
    }
    st.session_state.history = ([entry] + st.session_state.history)[:MAX_HISTORY]
    return entry


def latest_entry():
    return st.session_state.history[0] if st.session_state.history else None


def run_scan(label, fn, *args):
    # Progress messages come from the scan steps themselves; there is no
    # per-file progress signal, so no percentage is shown.
    with st.status(f"Scanning {label}…", expanded=True) as status:
        try:
            analysis = fn(*args, progress=st.write)
        except upload_scan.ScanBusyError as e:
            status.update(label="Scan not started", state="error")
            st.session_state.scan_error = f"Scan not started: {e}"
            st.rerun()
        except Exception as e:
            status.update(label="Scan failed", state="error")
            # A failed run clears the active results instead of leaving the
            # previous scan on screen looking like the outcome of this run.
            set_active(None)
            record(label, error=str(e))
            st.session_state.scan_error = f"Scan failed. No results were produced.\n\n{e}"
            st.rerun()
        status.update(label="Scan complete", state="complete")
    st.session_state.scan_error = None
    set_active(record(label, analysis=analysis))
    st.rerun()


def fmt_time(ts, with_date=False):
    if not ts:
        return "—"
    return datetime.fromtimestamp(ts).strftime("%d %b %Y, %H:%M:%S" if with_date else "%H:%M:%S")


def md_escape(text):
    # For markdown labels (expanders): neutralise markdown syntax in file
    # names / detected values coming from user documents.
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|<>:~$])", r"\\\1", str(text))


def scan_outcome(analysis):
    """('complete'|'partial'|'failed', message) for a finished scan."""
    s = analysis.get("summary", {})
    total, failed = s.get("total_files", 0), s.get("failed_files", 0)
    if total and failed == total:
        return "failed", f"None of the {total} document(s) could be processed."
    if failed:
        return "partial", f"{failed} of {total} document(s) could not be processed. Their findings are not included."
    return "complete", f"All {total} document(s) processed."


def build_chain(kind):
    k = str(kind).lower()
    if k == "email": return ["Email", "Phishing lure", "Credential capture", "Account takeover"]
    if k in ["phone", "phone_number", "mobile"]: return ["Phone", "Smishing", "Social engineering", "Fraud"]
    if k in ["address", "location", "gps"]: return ["Location", "Tracking", "Targeting", "Privacy exposure"]
    if k in ["aadhaar", "aadhar"]: return ["Aadhaar", "KYC impersonation", "Identity misuse", "Fraud"]
    if k == "pan": return ["PAN", "Identity matching", "Financial fraud"]
    if k in ["token", "cookie", "session", "session_token"]: return ["Token", "Session hijack", "Account access", "Unauthorised login"]
    if k == "url": return ["URL", "Tracking link", "Profile enrichment", "OSINT linking"]
    if k == "software": return ["Software", "App fingerprinting", "Usage profiling"]
    if k in ["timestamp", "date", "datetime"]: return ["Timestamp", "Activity timeline", "Pattern inference"]
    if k in ["camera_make", "camera_model"]: return ["Camera metadata", "Device fingerprinting", "Source tracing"]
    if k in ["name", "artist", "copyright"]: return ["Name", "Identity linking", "Profile matching"]
    return [k.title() if k else "Unknown", "Profile matching", "Potential misuse"]


def normalize_remediations(remediations):
    normalized = []
    for item in remediations:
        if isinstance(item, dict):
            normalized.append({
                "issue": item.get("issue") or item.get("title") or "Remediation",
                "action": item.get("action") or item.get("description") or "",
                "reason": item.get("reason") or "",
            })
        else:
            normalized.append({"issue": str(item), "action": "", "reason": ""})
    return normalized


def no_scan_gate(what):
    """Empty / failed state shared by every results page. Returns True if rendered."""
    if st.session_state.analysis:
        return False
    last = latest_entry()
    if last and not last["ok"]:
        ui.empty_state("The last scan failed",
                       f"No {what} are available because the most recent scan did not produce results. "
                       "Check the error above and run the scan again.")
    else:
        ui.empty_state("No scan results yet",
                       f"Upload one or more documents and run a security scan to see {what} here.")
    c = st.columns([1, 1, 1])[1]
    c.button("Upload documents", icon=":material/upload_file:", type="primary", width="stretch",
             on_click=go, args=("Upload & Scan",), key=f"cta_{what}")
    return True


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    ui.brand()
    ui.nav_label("Workspace")
    for name, icon in PAGES:
        st.button(name, icon=icon, key=f"nav_{name}", width="stretch",
                  type="primary" if st.session_state.page == name else "secondary",
                  on_click=go, args=(name,))

    ui.nav_label("Session status")
    last = latest_entry()
    queued = sum(1 for i in st.session_state.staged.values() if not i["error"] and i["selected"])
    if not last:
        status_html = "<b>No scan yet</b><br>Nothing has been scanned in this session."
    elif not last["ok"]:
        status_html = f'{ui.pill("Failed", ui.RED)}<br><b>Last scan failed</b> at {fmt_time(last["time"])}'
    else:
        a = last["analysis"]
        state, _ = scan_outcome(a)
        p = {"complete": ui.pill("Complete", ui.GREEN), "partial": ui.pill("Partial", ui.AMBER),
             "failed": ui.pill("Failed", ui.RED)}[state]
        s = a["summary"]
        status_html = (f'{p}<br><b>Latest scan</b> · {fmt_time(last["time"])}<br>'
                       f'{s.get("scanned_files", 0)}/{s.get("total_files", 0)} documents · '
                       f'{s.get("total_findings", 0)} findings')
    status_html += f"<br>{queued} file(s) queued for next scan"
    st.html(f'<div class="gt-side-status">{status_html}</div>')
    st.caption("All processing runs locally on this machine.")

if st.session_state.scan_error:
    st.error(st.session_state.scan_error, icon=":material/error:")

data = st.session_state.analysis or {}
summary = data.get("summary", {})
all_findings = data.get("findings", []) if isinstance(data.get("findings"), list) else []
doc_results = data.get("document_results", [])
doc_names = [d["source_file"] for d in doc_results]
doc_by_name = {d["source_file"]: d for d in doc_results}
latest_ok = next((h for h in st.session_state.history if h["ok"]), None)

if data and latest_ok and st.session_state.active_id != latest_ok["id"]:
    active = next((h for h in st.session_state.history if h["id"] == st.session_state.active_id), None)
    with st.container():
        st.warning(f"You are viewing an earlier scan ({active['label'] if active else ''}, "
                   f"{fmt_time(active['time']) if active else ''}), not the most recent one.",
                   icon=":material/history:")

page = st.session_state.page

# ================================================================ OVERVIEW
if page == "Overview":
    sub = "Privacy exposure summary for the scan you are viewing."
    if data:
        meta = data.get("scan_meta", {})
        sub = f"Results of the scan completed {fmt_time(meta.get('finished_at'), with_date=True)}."
    ui.page_header("Overview", "Exposure overview", sub)

    if not no_scan_gate("results"):
        state, msg = scan_outcome(data)
        total = summary.get("total_files", 0)
        ok_files = summary.get("scanned_files", total)
        failed = summary.get("failed_files", 0)
        n_find = summary.get("total_findings", len(all_findings))
        high = sum(1 for f in all_findings if ui.finding_severity(f.get("risk")) == "High")
        score = int(data.get("risk_score", 0) or 0)
        level = data.get("risk_level", "Low")

        if state == "failed":
            st.error(msg + " The figures below do not describe these documents.", icon=":material/error:")
        elif state == "partial":
            st.warning(msg, icon=":material/warning:")
        elif n_find == 0:
            st.success(f"No sensitive data patterns were detected in the {ok_files} processed document(s).",
                       icon=":material/verified_user:")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            ui.stat_card("Documents processed", ok_files, suffix=f"/ {total}",
                         sub="All processed" if not failed else ui.pill(f"{failed} failed", ui.RED),
                         accent=ui.CYAN)
        with c2:
            docs_hit = len({f.get("source_file") for f in all_findings})
            ui.stat_card("Total findings", n_find, sub=f"in {docs_hit} document(s)", accent=ui.VIOLET)
        with c3:
            ui.stat_card("High-severity findings", high, sub="risk weight above 8",
                         accent=ui.RED if high else ui.GREEN)
        with c4:
            ui.stat_card("Overall risk score", score, suffix="/ 100",
                         sub=f"{ui.pill(level, ui.score_color(level))} &nbsp;heuristic index",
                         accent=ui.score_color(level))

        st.space("medium")
        left, right = st.columns(2, gap="large")
        with left:
            ui.section("Findings by severity", "Severity bands from each finding's classifier weight.")
            if all_findings:
                ui.show_chart(ui.severity_chart(all_findings))
            else:
                st.caption("No findings to chart.")
        with right:
            ui.section("Findings by category", "Click a legend entry to highlight a severity.")
            if all_findings:
                ui.show_chart(ui.category_chart(all_findings))
            else:
                st.caption("No findings to chart.")

        st.space("small")
        ui.section("Document results", "One row per document in this scan. Score = sum of finding weights, capped at 100.")
        st.dataframe(
            pd.DataFrame([{
                "Document": d["source_file"],
                "Type": d["extension"].lstrip(".").upper(),
                "Size": ui.human_size(d.get("size")),
                "Status": ui.STATUS_LABEL.get(d["status"], d["status"]),
                "Findings": d["total_findings"],
                "Score": d["privacy_score"],
                "Level": d["risk_level"] or "—",
            } for d in doc_results]),
            hide_index=True, width="stretch",
            column_config={
                "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
                "Findings": st.column_config.NumberColumn("Findings", format="%d"),
            },
        )

        st.space("small")
        left, right = st.columns([1, 1.3], gap="large")
        with left:
            ui.section("Scan summary")
            meta = data.get("scan_meta", {})
            started, finished = meta.get("started_at"), meta.get("finished_at")
            outcome_pill = {"complete": ui.pill("Complete", ui.GREEN), "partial": ui.pill("Partial", ui.AMBER),
                            "failed": ui.pill("Failed", ui.RED)}[state]
            ui.kv_card([
                ("Status", outcome_pill),
                ("Scan ID", f'<span class="gt-chip">{esc(str(meta.get("scan_id", ""))[:12])}</span>'),
                ("Source", "Uploaded documents" if meta.get("source") == "upload" else "Bundled demo_data folder"),
                ("Completed", esc(fmt_time(finished, with_date=True))),
                ("Duration", f"{finished - started:.1f} s" if started and finished else "—"),
                ("Browser cookies", "Included (this machine)" if meta.get("include_cookies") else "Not included"),
            ])
        with right:
            ui.section("File processing status")
            rows = []
            for d in doc_results:
                label = ui.STATUS_LABEL.get(d["status"], d["status"])
                color = {"Scanned": ui.GREEN, "Failed": ui.RED}.get(label, ui.AMBER)
                meta_txt = d.get("error") or d.get("warning") or f"{d['total_findings']} finding(s)"
                if d.get("warning") and not d.get("error"):
                    label, color = "Warning", ui.AMBER
                rows.append((d["source_file"], f"{d['extension']} · {ui.human_size(d.get('size'))} · {meta_txt}",
                             ui.pill(label, color)))
            ui.rows_card(rows)

# =========================================================== UPLOAD & SCAN
elif page == "Upload & Scan":
    ui.page_header("Upload & Scan", "Scan documents for exposed personal data",
                   "Add files, choose which ones to include, then run the scan. Nothing leaves this machine.")

    main, side = st.columns([1.7, 1], gap="large")
    with main:
        uploaded = st.file_uploader(
            "Drag and drop documents here, or browse",
            type=[e.lstrip(".") for e in upload_scan.SUPPORTED_EXTENSIONS],
            accept_multiple_files=True,
            key=f"uploader_{st.session_state.uploader_key}",
        )
        if uploaded:
            # Move files into the queue, then reset the uploader so files
            # survive page navigation and can be removed individually.
            for uf in uploaded:
                data_bytes = uf.getvalue()
                name = upload_scan.display_name(uf.name)
                key = f"{name}:{hashlib.sha256(data_bytes).hexdigest()[:16]}"
                if key not in st.session_state.staged:
                    error = upload_scan.validate_upload(name, data_bytes)
                    st.session_state.staged[key] = {"name": name, "data": data_bytes,
                                                    "error": error, "selected": error is None}
            st.session_state.uploader_key += 1
            st.rerun()

        staged = st.session_state.staged
        selected = [i for i in staged.values() if not i["error"] and i["selected"]]
        ui.section("Scan queue",
                   f"{len(selected)} of {len(staged)} file(s) selected · "
                   f"{ui.human_size(sum(len(i['data']) for i in selected))}" if staged else "No files added yet.")
        if staged:
            with st.container(border=True):
                for key, item in list(staged.items()):
                    c_sel, c_type, c_size, c_rm = st.columns([5, 1.1, 1.2, 0.6], vertical_alignment="center")
                    with c_sel:
                        if item["error"]:
                            st.checkbox(item["name"], value=False, disabled=True, key=f"sel_{key}")
                            st.caption(f":red[Cannot scan: {item['error']}]")
                        else:
                            item["selected"] = st.checkbox(item["name"], value=item["selected"], key=f"sel_{key}")
                    c_type.html(f'<span class="gt-chip">{esc(item["name"].rpartition(".")[2].upper() or "?")}</span>')
                    c_size.caption(ui.human_size(len(item["data"])))
                    if c_rm.button("", icon=":material/close:", key=f"rm_{key}", type="tertiary", help="Remove from queue"):
                        del staged[key]
                        st.rerun()

        b1, b2 = st.columns([2.2, 1])
        scan_clicked = b1.button("Run Security Scan", type="primary", icon=":material/radar:", width="stretch")
        if b2.button("Clear queue", icon=":material/delete_sweep:", width="stretch", disabled=not staged):
            staged.clear()
            st.rerun()
        if scan_clicked:
            st.session_state.scan_error = None
            if not selected:
                st.warning("No documents selected. Add at least one supported file and tick it before scanning.",
                           icon=":material/info:")
            else:
                names = upload_scan.unique_names([i["name"] for i in selected])
                run_scan(f"{len(selected)} uploaded document(s)", upload_scan.scan_uploads,
                         [(n, i["data"]) for n, i in zip(names, selected)])

    with side:
        ui.section("Supported formats", "What GhostTrace actually reads from each file type.")
        st.html('<div class="gt-card">' + "".join(
            f'<div class="gt-format"><span class="gt-chip">{esc(ext)}</span><span>{esc(desc)}</span></div>'
            for ext, desc in upload_scan.SUPPORTED_EXTENSIONS.items()) + "</div>")
        st.space("small")
        with st.expander("Use bundled demo data", icon=":material/science:"):
            st.caption("Scans the project's demo_data/ folder instead (original behaviour). "
                       "This also counts this machine's browser cookie stores.")
            if st.button("Scan demo_data folder", width="stretch"):
                run_scan("demo_data folder", upload_scan.scan_demo_folder)

    last = latest_entry()
    if last:
        st.space("small")
        ui.section("Last scan result", f"{last['label']} · {fmt_time(last['time'])}")
        if not last["ok"]:
            st.error("The scan failed and produced no results.", icon=":material/error:")
        else:
            a = last["analysis"]
            state, msg = scan_outcome(a)
            s = a["summary"]
            {"complete": st.success, "partial": st.warning, "failed": st.error}[state](
                f"{msg} {s.get('total_findings', 0)} finding(s); overall risk score "
                f"{a.get('risk_score', 0)}/100 ({a.get('risk_level', '')}).")
            c1, c2, _ = st.columns([1, 1, 2])
            c1.button("Open overview", icon=":material/space_dashboard:", width="stretch",
                      on_click=lambda e=last: (set_active(e), go("Overview")))
            c2.button("Explore findings", icon=":material/manage_search:", width="stretch",
                      on_click=lambda e=last: (set_active(e), go("Findings")))

# ================================================================ FINDINGS
elif page == "Findings":
    ui.page_header("Findings", "Findings explorer",
                   "Every sensitive-data match from the scan. Detected values are masked unless you reveal them.")
    if not no_scan_gate("findings"):
        if not all_findings:
            ui.empty_state("No findings in this scan",
                           "The processed documents contained no matches for GhostTrace's detection patterns. "
                           "Check the Overview for documents that failed or had no extractable text.")
        else:
            rem_lookup = {(r.get("source_file"), r.get("kind")): r for r in data.get("remediations", [])}

            f1, f2, f3, f4 = st.columns([2.2, 1.6, 2, 1.4], vertical_alignment="bottom")
            search = f1.text_input("Search", placeholder="File name, finding type or category",
                                   key="f_search", icon=":material/search:")
            sev_sel = f2.pills("Severity", ui.SEV_ORDER, selection_mode="multi", key="f_sev")
            docs_sel = f3.multiselect("Documents", doc_names, key="f_docs", placeholder="All documents")
            sort = f4.selectbox("Sort by", ["Severity", "Document", "Finding type", "Category"], key="f_sort")
            reveal = st.toggle("Reveal detected values", key="f_reveal",
                               help="Shown only in this browser session. Values are never stored or sent anywhere.")

            q = (search or "").strip().lower()
            rows = []
            for f in all_findings:
                sev = ui.finding_severity(f.get("risk"))
                hay = f"{f.get('source_file', '')} {f.get('kind', '')} {f.get('category', '')}".lower()
                if q and q not in hay:
                    continue
                if sev_sel and sev not in sev_sel:
                    continue
                if docs_sel and f.get("source_file") not in docs_sel:
                    continue
                rows.append((sev, f))

            sev_rank = {s: i for i, s in enumerate(ui.SEV_ORDER)}
            key_fn = {
                "Severity": lambda r: (sev_rank[r[0]], -int(r[1].get("risk", 0)), r[1].get("source_file", "")),
                "Document": lambda r: (r[1].get("source_file", "").lower(), sev_rank[r[0]]),
                "Finding type": lambda r: (r[1].get("kind", ""), sev_rank[r[0]]),
                "Category": lambda r: (r[1].get("category", ""), sev_rank[r[0]]),
            }[sort]
            rows.sort(key=key_fn)

            counts = {s: sum(1 for r in rows if r[0] == s) for s in ui.SEV_ORDER}
            st.html(f'<div style="color:{ui.MUTED};font-size:0.85rem;margin:0.3rem 0 0.6rem;">'
                    f'Showing <b style="color:{ui.TEXT}">{len(rows)}</b> of {len(all_findings)} findings &nbsp; '
                    + " ".join(ui.pill(f"{counts[s]} {s}", ui.SEV_COLORS[s]) for s in ui.SEV_ORDER) + "</div>")

            if not rows:
                ui.empty_state("No findings match these filters", "Try a different search term or clear the filters.")
                st.columns([1, 1, 1])[1].button("Clear filters", width="stretch", on_click=reset_view_state)
            else:
                pages = (len(rows) - 1) // PAGE_SIZE + 1
                pg = min(st.session_state.get("f_page", 0), pages - 1)
                for sev, f in rows[pg * PAGE_SIZE:(pg + 1) * PAGE_SIZE]:
                    kind = str(f.get("kind", ""))
                    value = str(f.get("value", ""))
                    shown = value if reveal else ui.mask_value(kind, value)
                    label = (f":{ui.SEV_BADGE[sev]}-badge[{sev}] **{md_escape(kind.replace('_', ' ').upper())}** "
                             f"· {md_escape(f.get('source_file', ''))} · `{shown.replace('`', '')[:60]}`")
                    with st.expander(label):
                        doc = doc_by_name.get(f.get("source_file"), {})
                        left, right = st.columns([1.1, 1], gap="large")
                        with left:
                            ui.kv_card([
                                ("Document", esc(f.get("source_file", ""))),
                                ("Finding type", esc(kind)),
                                ("Category", esc(str(f.get("category", "")).replace("_", " "))),
                                ("Severity", ui.pill(sev, ui.SEV_COLORS[sev])),
                                ("Risk weight", esc(str(f.get("risk", "")))),
                                ("Detected value", f'<span class="gt-chip">{esc(shown)}</span>'),
                                ("Document score", f"{doc.get('privacy_score')}/100 ({esc(str(doc.get('risk_level')))})"
                                 if doc.get("privacy_score") is not None else "—"),
                            ])
                        with right:
                            rem = rem_lookup.get((f.get("source_file"), kind))
                            if rem:
                                st.markdown(f"**Recommended action**  \n{rem.get('action', '')}")
                                st.caption(f"{rem.get('reason', '')} · {rem.get('act', '')}: {rem.get('principle', '')}")
                            st.markdown("**Illustrative misuse scenario**")
                            st.html(ui.chain_html(build_chain(kind)))
                            st.caption("A general example of how this data type can be abused — not an observed event.")
                if pages > 1:
                    p1, p2, p3 = st.columns([1, 2, 1], vertical_alignment="center")
                    p1.button("Previous", icon=":material/chevron_left:", disabled=pg == 0, width="stretch",
                              on_click=lambda: st.session_state.update(f_page=pg - 1))
                    p2.html(f'<div style="text-align:center;color:{ui.MUTED};font-size:0.85rem;">'
                            f'Page {pg + 1} of {pages}</div>')
                    p3.button("Next", icon=":material/chevron_right:", disabled=pg >= pages - 1, width="stretch",
                              on_click=lambda: st.session_state.update(f_page=pg + 1))

# =========================================================== RISK ANALYTICS
elif page == "Risk Analytics":
    ui.page_header("Risk Analytics", "Risk analytics",
                   "How exposure is distributed across severity, category and documents in this scan.")
    if not no_scan_gate("analytics"):
        with st.expander("How GhostTrace scores risk", icon=":material/help:"):
            st.markdown(
                "These scores are **heuristic exposure indicators** built from fixed weights. They are not a "
                "probability of a breach and have not been statistically validated.\n\n"
                "- **Finding weight** — each detected item gets a fixed weight from the classifier "
                "(for example email 8, phone 6, Aadhaar 20, token 22).\n"
                "- **Finding severity** — weight below 5 is *Low*, 5–8 is *Medium*, above 8 is *High*.\n"
                "- **Document score** — the sum of that document's finding weights, capped at 100. "
                "70+ is *High*, 40–69 *Medium*, below 40 *Low*.\n"
                "- **Overall score** — an aggregate over unique values across all documents: "
                "emails×2 + phones×1 + Aadhaar×8 + tokens×12 + cookies×1, capped at 100, with the same bands."
            )
        score = int(data.get("risk_score", 0) or 0)
        level = data.get("risk_level", "Low")
        c1, c2, c3 = st.columns(3)
        with c1:
            ui.stat_card("Overall risk score", score, suffix="/ 100",
                         sub=ui.pill(level, ui.score_color(level)), accent=ui.score_color(level))
        scored = [d for d in doc_results if d["privacy_score"] is not None]
        with c2:
            top = max(scored, key=lambda d: d["privacy_score"]) if scored else None
            ui.stat_card("Highest document score", top["privacy_score"] if top else "—", suffix="/ 100" if top else "",
                         sub=esc(top["source_file"]) if top else "No processed documents",
                         accent=ui.score_color(top["risk_level"]) if top else ui.SLATE)
        with c3:
            n_high_docs = sum(1 for d in scored if d["risk_level"] == "High")
            ui.stat_card("High-risk documents", n_high_docs, suffix=f"/ {len(scored)}",
                         sub="document score 70 or above", accent=ui.RED if n_high_docs else ui.GREEN)

        st.space("medium")
        left, right = st.columns(2, gap="large")
        with left:
            ui.section("Findings by risk level", "Count of findings in each severity band.")
            if all_findings:
                ui.show_chart(ui.severity_chart(all_findings))
            else:
                st.caption("No findings in this scan.")
        with right:
            ui.section("Findings by category", "Stacked by severity. Click a legend entry to highlight.")
            if all_findings:
                ui.show_chart(ui.category_chart(all_findings))
            else:
                st.caption("No findings in this scan.")

        left, right = st.columns([1.4, 1], gap="large")
        with left:
            ui.section("Document comparison", "Processed documents only; failed documents have no score.")
            metric = st.segmented_control("Compare by", ["Document score", "Findings by severity"],
                                          default="Document score", key="doc_metric", label_visibility="collapsed")
            chart = (ui.document_chart(doc_results, all_findings) if metric == "Findings by severity"
                     else ui.document_score_chart(doc_results))
            if chart is not None:
                ui.show_chart(chart)
                if metric != "Findings by severity":
                    st.caption("Dashed lines mark the Medium (40) and High (70) thresholds.")
            else:
                st.caption("No processed documents with findings to compare.")
        with right:
            ui.section("Scan processing summary", "Outcome for every document in the scan.")
            if doc_results:
                ui.show_chart(ui.processing_chart(doc_results))

        paths = data.get("attack_paths", [])
        if paths:
            ui.section("Exposure pathways", "Generic abuse patterns associated with the data types found (from the analysis).")
            ui.rows_card([(p, "", "") for p in paths])

# ============================================================= REMEDIATION
elif page == "Remediation":
    ui.page_header("Remediation", "Remediation guidance",
                   "Recommended actions for each finding. GhostTrace never modifies or deletes your files.")
    if not no_scan_gate("recommendations"):
        st.info("These are recommendations only. Nothing is marked as resolved — re-scan the corrected "
                "documents to confirm the exposure is gone.", icon=":material/info:")
        per_finding = data.get("remediations", [])
        if not per_finding:
            ui.empty_state("Nothing to remediate",
                           "This scan produced no findings, so there are no remediation steps.")
        else:
            recs = normalize_remediations(data.get("recommendations", []))
            if recs:
                ui.section("Priority actions", "Scan-wide actions derived from the data types found.")
                cols = st.columns(min(3, len(recs)))
                for i, r in enumerate(recs):
                    with cols[i % len(cols)]:
                        st.html(f'<div class="gt-card" style="margin-bottom:0.8rem;">'
                                f'<div class="gt-stat-label"><span class="gt-dot" style="background:{ui.VIOLET}"></span>'
                                f'{esc(r["issue"])}</div>'
                                f'<div style="color:{ui.TEXT};font-weight:600;margin-top:0.45rem;">{esc(r["action"])}</div>'
                                f'<div class="gt-stat-sub">{esc(r["reason"])}</div></div>')

            st.space("small")
            ui.section("By document", "Grouped by finding type. Documents are ordered by document score.")
            c1, c2 = st.columns([2, 1.4])
            rem_doc = c1.selectbox("Document", ["All documents"] + doc_names, key="rem_doc")
            rem_sev = c2.pills("Severity", ui.SEV_ORDER, selection_mode="multi", key="rem_sev")

            risk_of = {(f.get("source_file"), f.get("kind")): f.get("risk", 0) for f in all_findings}
            grouped = {}
            for r in per_finding:
                src, kind = r.get("source_file", ""), r.get("kind", "")
                if rem_doc != "All documents" and src != rem_doc:
                    continue
                sev = ui.finding_severity(risk_of.get((src, kind), 0))
                if rem_sev and sev not in rem_sev:
                    continue
                g = grouped.setdefault(src, {}).setdefault(kind, dict(r, severity=sev, count=0))
                g["count"] += 1

            if not grouped:
                st.caption("No remediation items match these filters.")
            sev_rank = {s: i for i, s in enumerate(ui.SEV_ORDER)}
            for src in sorted(grouped, key=lambda s: -(doc_by_name.get(s, {}).get("privacy_score") or 0)):
                doc = doc_by_name.get(src, {})
                with st.container(border=True):
                    h1, h2 = st.columns([3, 1], vertical_alignment="center")
                    h1.html(f'<div class="gt-h2">{esc(src)}</div>'
                            f'<div class="gt-h2-sub">{sum(k["count"] for k in grouped[src].values())} finding(s)</div>')
                    if doc.get("privacy_score") is not None:
                        score_txt = f"Score {doc['privacy_score']} · {doc['risk_level']}"
                        h2.html(f'<div style="text-align:right">{ui.pill(score_txt, ui.score_color(doc["risk_level"]))}</div>')
                    items = sorted(grouped[src].values(), key=lambda k: sev_rank[k["severity"]])
                    st.dataframe(pd.DataFrame([{
                        "Severity": k["severity"],
                        "Finding type": k.get("kind", ""),
                        "Category": str(k.get("category", "")).replace("_", " "),
                        "Count": k["count"],
                        "Recommended action": k.get("action", ""),
                        "Why": k.get("reason", ""),
                        "DPDP principle": k.get("principle", ""),
                    } for k in items]), hide_index=True, width="stretch",
                        column_config={"Count": st.column_config.NumberColumn(format="%d")})

# ============================================================ SCAN HISTORY
elif page == "Scan History":
    ui.page_header("Scan History", "Scan history",
                   "Scans run in this browser session. History is kept in memory only and is cleared when the session ends.")
    hist = st.session_state.history
    if not hist:
        ui.empty_state("No scans in this session", "Scans you run will be listed here so you can switch between them.")
        st.columns([1, 1, 1])[1].button("Upload documents", icon=":material/upload_file:", type="primary",
                                        width="stretch", on_click=go, args=("Upload & Scan",))
    else:
        for i, h in enumerate(hist):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 3, 1.3], vertical_alignment="center")
                if h["ok"]:
                    a = h["analysis"]
                    state, _ = scan_outcome(a)
                    s = a["summary"]
                    p = {"complete": ui.pill("Complete", ui.GREEN), "partial": ui.pill("Partial", ui.AMBER),
                         "failed": ui.pill("Failed", ui.RED)}[state]
                    detail = (f"{s.get('scanned_files', 0)}/{s.get('total_files', 0)} documents · "
                              f"{s.get('total_findings', 0)} findings · risk {a.get('risk_score', 0)}/100 "
                              f"({a.get('risk_level', '')})")
                else:
                    p, detail = ui.pill("Failed", ui.RED), (h.get("error") or "")[:160]
                current = " · viewing" if h["id"] == st.session_state.active_id else ""
                c1.html(f'<div class="gt-row-title">{esc(h["label"])}</div>'
                        f'<div class="gt-row-meta">{fmt_time(h["time"], with_date=True)}{current}</div>')
                c2.html(f'{p}<div class="gt-row-meta" style="margin-top:0.25rem">{esc(detail)}</div>')
                if h["ok"]:
                    c3.button("View", key=f"hist_{i}", width="stretch",
                              disabled=h["id"] == st.session_state.active_id,
                              on_click=lambda e=h: (set_active(e), go("Overview")))
