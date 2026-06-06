import json
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


def build_reports():
    files = scan_files()

    raw_findings = []

    emails = []
    phones = []
    aadhaars = []
    urls = []
    tokens = []

    documents = []
    photos = []

    # --------------------------------
    # Scan Files
    # --------------------------------

    for f in files:
        ext = f["extension"]

        try:
            # TEXT FILES
            if ext in [".txt", ".csv", ".json"]:
                documents.append(f["path"])

                text = extract_text(f["path"])
                print("\n==========")
                print("FILE:", f["path"])
                print(text)
                print("==========\n")

                findings = find_matches(
                    text,
                    f["path"]
                )

                raw_findings.extend(findings)

            # DOCUMENT FILES
            elif ext == ".pdf":
                print("PDF FOUND:", f["path"])
                documents.append(f["path"])
                try:
                    #text = extract_text(f["path"])
                    text = extract_pdf_text(f["path"])
                    print("PDF TEXT:")
                    print(text)
                    findings = find_matches(
                        text,
                        f["path"] )

                    raw_findings.extend(findings)

                except Exception as e:
                    print("PDF ERROR:", e)
            elif ext == ".docx":
                documents.append(f["path"])

                try:
                    print("DOCX FOUND:", f["path"])
                    print("PATH =", f["path"])
                    text = extract_docx_text(f["path"])

                    print("DOCX TEXT:")
                    print(text)

                    findings = find_matches(
                        text,
                        f["path"]
                    )

                    raw_findings.extend(findings)

                except Exception as e:
                    print("DOCX ERROR:", e)
            # IMAGE FILES
            # IMAGE FILES
            elif ext in [".jpg", ".jpeg", ".png"]:

                photos.append(f["path"])

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

                    # Run regex scanning on metadata
                    findings = find_matches(
                        metadata_text,
                        f["path"]
                    )

                    raw_findings.extend(findings)

                    # EXIF-specific findings

                    if "Artist" in metadata:
                        raw_findings.append({
                            "source_file": f["path"],
                            "kind": "name",
                            "value": metadata["Artist"]
                        })

                    if "DateTimeOriginal" in metadata:
                        raw_findings.append({
                            "source_file": f["path"],
                            "kind": "timestamp",
                            "value": metadata["DateTimeOriginal"]
                        })

                    if "Copyright" in metadata:
                        raw_findings.append({
                            "source_file": f["path"],
                            "kind": "copyright",
                            "value": metadata["Copyright"]
                        })
                    if "Make" in metadata:
                        raw_findings.append({
                            "source_file": f["path"],
                            "kind": "camera_make",
                            "value": metadata["Make"]
                        })

                    if "Model" in metadata:
                        raw_findings.append({
                            "source_file": f["path"],
                            "kind": "camera_model",
                            "value": metadata["Model"]
                        })

                    if "DateTime" in metadata:
                        raw_findings.append({
                            "source_file": f["path"],
                            "kind": "timestamp",
                            "value": metadata["DateTime"]
                        })

                    if "Software" in metadata:
                        raw_findings.append({
                            "source_file": f["path"],
                            "kind": "software",
                            "value": metadata["Software"]
                        })

                except Exception as e:
                    print(
                        f"Error processing image {f['path']}: {e}"
                    )
        except Exception as e:
            print(
                f"Error processing {f['path']}: {e}"
            )

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

        elif kind == "token":
            tokens.append(finding["value"])

    # --------------------------------
    # Cookie Extraction
    # --------------------------------

    try:
        cookies = extract_browser_cookies()
    except Exception as e:
        print("Cookie extraction failed:", e)
        cookies = []

    # --------------------------------
    # Build scan.json
    # --------------------------------

    scan_report = {
        "scan_path": "demo_data",

        "emails": list(set(emails)),
        "phones": list(set(phones)),
        "aadhaars": list(set(aadhaars)),
        "urls": list(set(urls)),
        "tokens": list(set(tokens)),

        "documents": documents,
        "photos": photos,

        "gps": [],

        "cookies": cookies,

        "files": files,
        "raw_findings": raw_findings,
    }

    SHARED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with SCAN_JSON.open(
        "w",
        encoding="utf-8"
    ) as fp:
        json.dump(
            scan_report,
            fp,
            indent=2
        )

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
        files,
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

    if risk_score >= 70:
            risk_level = "High"
    elif risk_score >= 40:
            risk_level = "Medium"
    else:
            risk_level = "Low"


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
    analysis_report = {

        "privacy_score": privacy_score,

        "risk_score": risk_score,
        "risk_level": risk_level,

        "summary": {
            "total_files": len(files),
            "total_findings": len(
                classified_findings
            ),
        },

        "findings": classified_findings,

        "attack_paths": attack_paths,

        "recommendations": recommendations,

        "graph": graph,

        "timeline": timeline,

        "remediations": remediations
    }

    with ANALYSIS_JSON.open(
        "w",
        encoding="utf-8"
    ) as fp:
        json.dump(
            analysis_report,
            fp,
            indent=2
        )

    print("\n=== GhostTrace Scan Complete ===")
    print(f"Files found: {len(files)}")
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


if __name__ == "__main__":
    build_reports()