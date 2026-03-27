Receipt Scanner — Project Summary
================================

What this project is
--------------------
A Streamlit web app that extracts text from receipt images (with optional OpenAI OCR/LLM help), parses receipts and product lines, normalizes product names, and persists everything to a local SQLite database. Beyond basic receipt parsing, the project provides product-level parsing and classification that enable domain features such as organic monitoring ("Biokontrolle"), cheese-amount summaries, and a variety of statistics and reporting views.

Core capabilities
-----------------
- Receipt ingestion: upload images, extract text, and parse receipts and line items
- Product parsing & normalization: canonicalize product names, merge duplicates, and support manual edits
- Product classification: assign products to classes (sortiment) and maintain regex-based references for batch classification
- Biokontrolle (organic monitoring): detect and report organic items using product attributes and flags
- Cheese summaries: aggregate and summarize amounts and values for cheese-specific reports (`kaeseinnahmen`)
- Statistics & reports: time-series and categorical stats across products, classes, and receipts
- Persistence & backups: data stored in SQLite with `backup.sh` for scheduled backups


Quick start
-----------
Prerequisites: Python >= 3.12 and a virtual environment. Dependencies are specified in `pyproject.toml`.

Install and run (example):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
streamlit run app.py
```

Notes on config and API usage
----------------------------
- The project can call OpenAI APIs for OCR/LLM tasks; set your API key using environment variables (recommended via a `.env` file). See `pyproject.toml` for required packages like `openai` and `python-dotenv`.
- Data is persisted to a local SQLite database. Use `backup.sh` to create backups (good for cron jobs).

Project structure (high-level)
------------------------------
- `app.py`, `main.py` — Streamlit entry points
- `pages/` — Streamlit pages (upload, overview, detail, analytics)
- `components/` — UI and helper components (input, product helpers)
- `models/` — domain models (`product.py`, `receipt.py`)
- `receipt_parser/` — parsing/LLM helpers
- `repository/` — DB access (receipt repository)
- `scripts/` — maintenance scripts (e.g. `update_schema.py`)
- `assets/`, `saved_images/` — static assets and uploaded images

Important files
---------------
- [README.md](README.md) — user-facing overview
- [FILE_STRUCTURE.md](FILE_STRUCTURE.md) — file layout notes
- [pyproject.toml](pyproject.toml) — dependencies and project metadata
- `backup.sh` — DB backup helper
- `initialize_classification_feature.py` — helper to initialize added classification tables (if present)

Dependencies
------------
See `pyproject.toml` for pinned libraries; highlights:
- `streamlit` — web UI
- `openai` — LLM / OCR assistance
- `sqlalchemy` — DB ORM
- `pydantic`, `pillow-heif`, `pdf2image`, `xlsxwriter`

Privacy & data notes
--------------------
- Uploaded images and parsed receipts are saved locally in SQLite and `saved_images/`.
- If you enable OpenAI API calls, review what data is sent to external services and sanitize or redact PII as needed.

Developer notes / next steps
---------------------------
- Confirm environment variables and `.env` usage for OpenAI keys.
- Run `scripts/update_schema.py` or `initialize_classification_feature.py` if schema migrations are needed after updates.
- If you want a longer, more structured README or additional developer docs (examples, tests, CI), tell me where to expand.

Contact
-------
This file was auto-generated to summarize the repository; ask me to expand any section or adapt it for a specific audience (developer, user, or technical writer).
