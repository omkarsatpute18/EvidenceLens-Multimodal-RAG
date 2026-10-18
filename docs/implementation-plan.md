# Implementation plan

## User-visible outcome

A user uploads a mixed evidence bundle, asks a cross-modal question, and receives a cited answer with confidence, contradiction warnings, inspectable evidence, and a high-level workflow trace.

## MVP acceptance criteria

- Parse PDF/TXT/Markdown/CSV/XLSX/PNG/JPG without losing source provenance.
- Route only relevant retrieval modes for each query.
- Return structured citations and an explicit no-evidence response.
- Surface possible numeric conflicts and uncertain visual interpretation.
- Provide browser UI, JSON API, offline tests, demo data, and Docker packaging.

## Architecture and data flow

FastAPI serves the browser UI and JSON endpoints. The ingestion agent routes files to text, table, or image parsers. Parsers emit Pydantic `EvidenceItem` records. A deterministic local hybrid index ranks token overlap and filters by content type. The orchestrator plans modes, synthesis creates cited findings, contradiction checking compares numeric claims, verification checks support, and the formatter returns the final response.

## Technology choices

Python 3.11–3.13, FastAPI, Pydantic, PyMuPDF, openpyxl, Pillow, pytest, and a local lexical index. The model adapter is replaceable; mock mode is deterministic and offline-first.

## Test plan

Unit tests cover supported/unsupported/empty files, PDF page metadata, spreadsheet rows, image uncertainty, retrieval ranking, selective routing, contradictions, verification, and API behavior. `pytest -q` is the single check command.

## Deployment plan

Run directly with Uvicorn or with `docker compose up --build`. `/health` provides a readiness check. The local Docker path is complete; a hosted deployment remains a manual account/credential step.

## Risks and boundaries

The MVP does not promise OCR or exact chart digitization, uses lexical rather than embedding retrieval, and has no authentication or tenant isolation. These are explicitly documented rather than hidden behind fabricated model output. PDF rendering, hosted providers, and audio/video are optional follow-ups.
