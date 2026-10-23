import argparse
import json
import os
import time
import uuid
from pathlib import Path

from scanner import scan_files
from extractors.text_extractor import extract_text
from extractors.sqlite_extractor import extract_browser_cookies
from extractors.pdf_extractor import extract_pdf_text
from extractors.docx_extractor import extract_docx_text
from extractors.image_extractor import extract_image_metadata
from patterns import (
    EMAIL_REGEX,
    PHONE_REGEX,
    AADHAAR_REGEX,
    URL_REGEX,
    TOKEN_REGEX,
    PAN_REGEX,
)

from classifier import classify_finding
from scorer import calculate_privacy_score
from graph_builder import build_graph
from timeline_builder import build_timeline
from remediation import build_remediations


ROOT = Path(__file__).resolve().parent
SHARED_DIR = ROOT.parent / "shared"

SCAN_JSON = SHARED_DIR / "scan.json"
ANALYSIS_JSON = SHARED_DIR / "analysis.json"


def find_matches(text, source_file):
    findings = []

    pattern_map = [
        ("email", EMAIL_REGEX),
        ("phone", PHONE_REGEX),
        ("aadhaar", AADHAAR_REGEX),
        ("url", URL_REGEX),
        ("pan", PAN_REGEX),
        ("token", TOKEN_REGEX),
    ]

    for kind, regex in pattern_map:
        for value in regex.findall(text):
            findings.append(
                {
                    "source_file": source_file,
                    "kind": kind,
                    "value": value,
                }
            )

    return findings


def risk_level_for(score):
    if score >= 70:
        return "High"
    elif score >= 40:
        return "Medium"
    return "Low"


def write_json_atomic(path, payload):
    # Write to a temp file and swap it in, so a reader never sees a
    # half-written scan.json / analysis.json.
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with tmp_path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2)
    os.replace(tmp_path, path)


def build_reports(files=None, include_cookies=True, scan_id=None,
                  scan_source="demo_folder"):
    # files: optional list of scan_files()-style dicts. Each may carry a
    # "source" key (e.g. the original upload filename) that is recorded in
    # the output instead of the on-disk path. When omitted, SCAN_ROOT is
    # scanned exactly as before.
    if files is None:
        files = scan_files()

    scan_id = scan_id or uuid.uuid4().hex
    started_at = time.time()

    raw_findings = []
    file_status = {}

    emails = []
    phones = []
    aadhaars = []
    urls = []
    pans = []
    tokens = []

    documents = []
    photos = []

    # --------------------------------
    # Scan Files
    # --------------------------------

    for f in files:
        ext = f["extension"]
        # Name recorded in findings/output. For demo-folder scans this is
        # the path, as before; for uploads it is the original filename.
        src = f.get("source", f["path"])
        status = {"status": "scanned", "error": None, "chars_extracted": None}
        file_status[src] = status

        try:
            # TEXT FILES
            if ext in [".txt", ".csv", ".json"]:
                documents.append(src)

                text = extract_text(f["path"])
                status["chars_extracted"] = len(text)
                print("\n==========")
                print("FILE:", src)
                print(text)
                print("==========\n")

                findings = find_matches(
                    text,
                    src
                )

                raw_findings.extend(findings)

            # DOCUMENT FILES
            elif ext == ".pdf":
                print("PDF FOUND:", src)
                documents.append(src)
                try:
                    #text = extract_text(f["path"])
                    text = extract_pdf_text(f["path"])
                    status["chars_extracted"] = len(text)
                    print("PDF TEXT:")
                    print(text)
                    findings = find_matches(
                        text,
                        src )

                    raw_findings.extend(findings)

                except Exception as e:
                    print("PDF ERROR:", e)
                    status.update(status="failed", error=f"PDF error: {e}")
            elif ext == ".docx":
                documents.append(src)

                try:
                    print("DOCX FOUND:", src)
                    text = extract_docx_text(f["path"])
                    status["chars_extracted"] = len(text)

                    print("DOCX TEXT:")
                    print(text)

                    findings = find_matches(
                        text,
                        src
                    )

                    raw_findings.extend(findings)

                except Exception as e:
                    print("DOCX ERROR:", e)
                    status.update(status="failed", error=f"DOCX error: {e}")
            # IMAGE FILES
            elif ext in [".jpg", ".jpeg", ".png"]:

                photos.append(src)

                try:
                    metadata = extract_image_metadata(
                        f["path"]
                    )

                    print("IMAGE METADATA:")
                    print(metadata)

                    # Convert metadata dict into text
                    metadata_text = " ".join(
                        [f"{k}: {v}" for k, v in metadata.items()]
                    )
                    status["chars_extracted"] = len(metadata_text)

                    # Run regex scanning on metadata
                    findings = find_matches(
                        metadata_text,
                        src
                    )

                    raw_findings.extend(findings)

                    # EXIF-specific findings
                    exif_kinds = [
                        ("Artist", "name"),
                        ("DateTimeOriginal", "timestamp"),
                        ("Copyright", "copyright"),
                        ("Make", "camera_make"),
                        ("Model", "camera_model"),
                        ("DateTime", "timestamp"),
                        ("Software", "software"),
                    ]

                    for tag, kind in exif_kinds:
                        if tag in metadata:
                            raw_findings.append({
                                "source_file": src,
                                "kind": kind,
                                "value": metadata[tag]
                            })

                except Exception as e:
                    print(
                        f"Error processing image {src}: {e}"
                    )
                    status.update(status="failed", error=f"Image error: {e}")
            else:
                # Listed by the scanner (e.g. .sqlite/.db) but no extractor
                # is wired up - report it instead of implying "0 findings".
                status.update(
                    status="unsupported",
                    error=f"No extractor for {ext} files",
                )
        except Exception as e:
            print(
                f"Error processing {src}: {e}"
            )
            status.update(status="failed", error=str(e))

        # Extractor messages can embed the on-disk (temp) path.
        # (Some, like PIL, embed repr(path) with escaped backslashes.)
        if status["error"] and src != f["path"]:
            for variant in (repr(f["path"])[1:-1], f["path"]):
                status["error"] = status["error"].replace(variant, src)

    # --------------------------------
    # Categorise Findings
    # --------------------------------

    for finding in raw_findings:
        kind = finding["kind"]

        if kind == "email":
            emails.append(finding["value"])

        elif kind == "phone":
            phones.append(finding["value"])

        elif kind == "aadhaar":
            aadhaars.append(finding["value"])

        elif kind == "url":
            urls.append(finding["value"])

        elif kind == "pan":
            pans.append(finding["value"])

        elif kind == "token":
            tokens.append(finding["value"])

    # --------------------------------
    # Cookie Extraction
    # --------------------------------

    # Browser cookies come from this machine, not from the scanned files,
    # so upload scans turn this off to keep results about the uploads only.
    cookies = []
    if include_cookies:
        try:
            cookies = extract_browser_cookies()
        except Exception as e:
            print("Cookie extraction failed:", e)
            cookies = []

    # Same shape as scan_files() output, but with the recorded source name
    # as "path" so temp upload paths never land in the JSON.
    output_files = []
    for f in files:
        entry = {k: v for k, v in f.items() if k != "source"}
        entry["path"] = f.get("source", f["path"])
        output_files.append(entry)

    scan_meta = {
        "scan_id": scan_id,
        "source": scan_source,
        "started_at": started_at,
        "include_cookies": include_cookies,
    }

    # --------------------------------
    # Build scan.json
    # --------------------------------

    scan_report = {
        "scan_meta": scan_meta,
        "scan_path": "demo_data" if scan_source == "demo_folder" else "uploaded_documents",

        "emails": list(set(emails)),
        "phones": list(set(phones)),
        "aadhaars": list(set(aadhaars)),
        "urls": list(set(urls)),
        "pans": list(set(pans)),
        "tokens": list(set(tokens)),

        "documents": documents,
        "photos": photos,

        "gps": [],

        "cookies": cookies,

        "files": output_files,
        "raw_findings": raw_findings,
    }

    SHARED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    write_json_atomic(SCAN_JSON, scan_report)

    # --------------------------------
    # Analysis Layer
    # --------------------------------

    classified_findings = [
        classify_finding(
            item["kind"],
            item["value"],
            item["source_file"],
        )

        for item in raw_findings
    ]

    privacy_score = calculate_privacy_score(
        classified_findings
    )

    graph = build_graph(
        classified_findings
    )

    timeline = build_timeline(
        output_files,
        classified_findings,
    )

    remediations = build_remediations(
        classified_findings
    )
        # --------------------------------
    # Risk Score
    # --------------------------------

    risk_score = (
    len(emails) * 2 +
    len(phones) * 1 +
    len(aadhaars) * 8 +
    len(tokens) * 12 +
    len(cookies) * 1
    )

    risk_score = min(risk_score, 100)

    risk_level = risk_level_for(risk_score)

    # --------------------------------
    # Per-document results
    # --------------------------------
    # Document score uses the same rule as privacy_score
    # (calculate_privacy_score over that file's classified findings).

    document_results = []

    for f in output_files:
        src = f["path"]
        status = file_status.get(src, {})
        doc_findings = [
            item for item in classified_findings
            if item["source_file"] == src
        ]
        categories = {}
        for item in doc_findings:
            categories[item["category"]] = categories.get(item["category"], 0) + 1

        ok = status.get("status") == "scanned"
        doc_score = calculate_privacy_score(doc_findings) if ok else None

        warning = None
        if ok and status.get("chars_extracted") == 0:
            if f["extension"] in [".jpg", ".jpeg", ".png"]:
                warning = "No EXIF metadata found"
            else:
                warning = "No text could be extracted"

        document_results.append({
            "source_file": src,
            "name": f["name"],
            "extension": f["extension"],
            "size": f.get("size"),
            "status": status.get("status", "failed"),
            "error": status.get("error"),
            "warning": warning,
            "chars_extracted": status.get("chars_extracted"),
            "total_findings": len(doc_findings),
            "privacy_score": doc_score,
            "risk_level": risk_level_for(doc_score) if ok else None,
            "categories": categories,
        })

    failed_files = sum(
        1 for d in document_results if d["status"] != "scanned"
    )


    # --------------------------------
    # Attack Paths
    # --------------------------------

    attack_paths = []

    if emails:
        attack_paths.append(
            "Email → Phishing → Credential Theft"
        )

    if phones:
        attack_paths.append(
            "Phone → Smishing → Social Engineering"
        )

    if aadhaars:
        attack_paths.append(
            "Aadhaar → Identity Theft → KYC Fraud"
        )

    if tokens:
        attack_paths.append(
            "Token Exposure → Unauthorized Access"
        )

    if cookies:
        attack_paths.append(
            "Cookie Theft → Session Hijacking"
        )


    # --------------------------------
    # Recommendations
    # --------------------------------

    recommendations = []

    if emails:
        recommendations.append({
            "issue": "Email Exposure",
            "action": "Remove email addresses from public documents",
            "reason": "Reduces phishing risk"
        })

    if phones:
        recommendations.append({
            "issue": "Phone Exposure",
            "action": "Redact phone numbers before sharing",
            "reason": "Prevents smishing attacks"
        })

    if aadhaars:
        recommendations.append({
            "issue": "Aadhaar Exposure",
            "action": "Mask Aadhaar numbers",
            "reason": "Prevents identity theft"
        })

    if tokens:
        recommendations.append({
            "issue": "API Token Exposure",
            "action": "Rotate exposed tokens",
            "reason": "Prevents unauthorized access"
        })

    if cookies:
        recommendations.append({
            "issue": "Browser Cookie Exposure",
            "action": "Clear unnecessary cookies",
            "reason": "Reduces tracking and session abuse"
        })
    scan_meta["finished_at"] = time.time()

    analysis_report = {

        "scan_meta": scan_meta,

        "privacy_score": privacy_score,

        "risk_score": risk_score,
        "risk_level": risk_level,

        "summary": {
            "total_files": len(files),
            "total_findings": len(
                classified_findings
            ),
            "scanned_files": len(files) - failed_files,
            "failed_files": failed_files,
        },

        "document_results": document_results,

        "findings": classified_findings,

        "attack_paths": attack_paths,

        "recommendations": recommendations,

        "graph": graph,

        "timeline": timeline,

        "remediations": remediations
    }

    write_json_atomic(ANALYSIS_JSON, analysis_report)

    print("\n=== GhostTrace Scan Complete ===")
    print(f"Scan ID: {scan_id}")
    print(f"Files found: {len(files)}")
    print(f"Files failed: {failed_files}")
    print(
        f"Findings found: {len(raw_findings)}"
    )
    print(
        f"Cookies found: {len(cookies)}"
    )
    print(
        f"scan.json -> {SCAN_JSON}"
    )
    print(
        f"analysis.json -> {ANALYSIS_JSON}"
    )

    return {
        "scan": scan_report,
        "analysis": analysis_report,
    }


def files_from_manifest(manifest):
    # Manifest entries: {"path": <file on disk>, "name": <original filename>}
    files = []
    for entry in manifest.get("files", []):
        path = Path(entry["path"])
        stat = path.stat()
        files.append({
            "path": str(path),
            "name": entry["name"],
            "extension": path.suffix.lower(),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "source": entry["name"],
        })
    return files


if __name__ == "__main__":
    import sys

    # Document text is echoed to stdout; don't let a cp1252 console/pipe
    # turn a non-ASCII character into a silently skipped file.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="GhostTrace scan pipeline")
    parser.add_argument(
        "--manifest",
        help="JSON file listing specific files to scan (used by the upload UI). "
             "Without it, the demo_data folder is scanned.",
    )
    args = parser.parse_args()

    if args.manifest:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        build_reports(
            # No "files" key -> scan SCAN_ROOT as usual.
            files=files_from_manifest(manifest) if "files" in manifest else None,
            include_cookies=manifest.get("include_cookies", False),
            scan_id=manifest.get("scan_id"),
            scan_source=manifest.get("source", "upload"),
        )
    else:
        build_reports()