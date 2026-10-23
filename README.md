# GhostTrace — Privacy Intelligence & Data Exposure Analysis

**GhostTrace** is a privacy intelligence platform designed to identify potentially sensitive information in documents, assess data exposure risks, and provide actionable remediation recommendations through an interactive dashboard.

The platform combines document extraction, sensitive-data classification, risk scoring, and remediation guidance into a unified scanning workflow.

---

## Overview

Sensitive information can unintentionally remain embedded in documents and digital files. Identifying these exposures manually can be time-consuming and error-prone.

GhostTrace streamlines this process by allowing users to upload multiple documents, analyse their contents or metadata, identify potential sensitive-data exposures, and review findings through a centralised dashboard.

## Key Features

- **Multi-File Scanning:** Upload and analyse multiple supported files in a single workflow.
- **Sensitive-Data Detection:** Identify supported patterns of potentially sensitive information in extracted document content and metadata.
- **Risk Scoring:** Evaluate detected findings using a rule-based risk assessment system.
- **Document-Level Analysis:** Review findings and processing statuses for individual documents.
- **Interactive Dashboard:** Explore scan summaries, findings, and risk analytics through a Streamlit interface.
- **Remediation Guidance:** Present recommendations to help users investigate and address potential data exposures.
- **Error Handling:** Distinguish files that were successfully processed from files that failed extraction.
- **Local Processing:** Run the analysis pipeline locally without requiring document uploads to an external analysis service.

---

## System Architecture

GhostTrace follows a modular architecture that separates the user interface from the document-analysis pipeline.

```text
                  ┌─────────────────────────┐
                  │          User           │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │    Streamlit Frontend   │
                  │   Upload & Dashboard    │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │    Upload Management    │
                  │ Validation & Handling   │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │   Document Extraction  │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ Sensitive-Data          │
                  │ Classification          │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ Rule-Based Risk Scoring │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ Remediation Guidance   │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ Scan Results &          │
                  │ Dashboard Analytics     │
                  └─────────────────────────┘
```

---

## Supported File Types

The current upload workflow supports the following formats:

| Format | Analysis |
|---|---|
| `.txt` | Text extraction and sensitive-data detection |
| `.csv` | Text-based data analysis |
| `.json` | Text-based data analysis |
| `.pdf` | Embedded text extraction; scanned-image OCR is not included |
| `.docx` | Document text extraction |
| `.jpg`, `.jpeg`, `.png` | Image metadata analysis |

**Limitations:** PDF analysis does not currently include OCR for scanned pages. Image analysis focuses on metadata rather than detecting text inside images. SQLite and other database files are not currently supported by the upload-and-scan workflow.

---

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Frontend & Dashboard | Streamlit |
| Data Processing | Python-based extraction and analysis modules |
| Risk Assessment | Rule-based scoring |
| Results Storage | JSON-based scan results |
| Version Control | Git and GitHub |

---

## Project Structure

The project separates the frontend interface from the backend analysis pipeline.

```text
GhostTrace-Hack4Soc/
├── backend/
│   ├── config.py
│   ├── report.py
│   └── extractors/
├── frontend/
│   ├── app.py
│   ├── upload_scan.py
│   └── dashboard.py
├── shared/
├── demo_data/
├── main.py
├── frontend.py
├── README.md
└── .gitignore
```

*Note: This is a representative structure. Update it if your repository uses different file or folder names.*

---

## Getting Started

### Prerequisites

- Python installed on your system.
- Git.
- Visual Studio Code or another Python development environment.

### 1. Clone the Repository

```bash
git clone https://github.com/nandhinithangaraj1411/GhostTrace-Hack4Soc.git
cd GhostTrace-Hack4Soc
```

### 2. Create a Virtual Environment

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

If the repository contains a `requirements.txt` file, install the dependencies with:

```bash
pip install -r requirements.txt
```

If a dependency file is not included, install the required packages according to the project's existing imports and setup instructions.

### 4. Launch GhostTrace

From the project root, run:

```bash
python -m streamlit run frontend/app.py --server.address localhost
```

Open the local address displayed in your terminal. The default Streamlit address is typically:

```text
http://localhost:8501
```

### 5. Scan Documents

1. Open the GhostTrace application.
2. Navigate to the Upload & Scan page.
3. Select one or more supported documents.
4. Start the scan.
5. Review the scan summary and document processing statuses.
6. Explore findings, risk assessments, and remediation recommendations.

---

## Security & Privacy

GhostTrace is designed to support local analysis of potentially sensitive documents.

- Run the application locally and review the source code before analysing confidential files.
- Do not commit real documents, extracted personal information, credentials, or sensitive scan results to version control.
- Use synthetic test documents when demonstrating or testing the platform.
- Treat detected patterns as potential exposures that require contextual review.
- Local processing does not automatically guarantee secure storage, access control, or complete data erasure.

---

## Current Limitations

- Detection quality depends on the implemented extraction and classification rules.
- OCR for scanned PDFs and text embedded in images is not currently included.
- SQLite and other database-file scanning is not available through the current upload workflow.
- Risk scores are heuristic indicators, not probabilities of a data breach.
- Remediation recommendations guide investigation and do not guarantee that sensitive information has been removed.

---

## Future Improvements

Potential areas for further development include:

- OCR-based analysis for scanned documents and images.
- Expanded support for structured database files.
- More configurable sensitive-data detection rules.
- Enhanced risk analytics and historical scan tracking.
- Exportable investigation reports.
- Additional remediation workflow capabilities.

---

## Contributing

Contributions, suggestions, and bug reports are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Submit a pull request describing the changes.

---

## Disclaimer

GhostTrace is intended to assist with privacy analysis and identifying potential sensitive-data exposures. Findings should be validated before taking action. The platform is not a substitute for a comprehensive security audit or legal compliance assessment.

---

**Built with Python and Streamlit.**