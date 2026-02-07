# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A shared experimental repo for Paul (Harrington) and Andrew (Condon) — and occasionally Narit (Trikasemsak) — to prototype Python↔JavaScript↔DOM integration via PySide6/Qt WebEngine. The long-term goal is embedding rich web views (maps, PDFs, HTML tables) inside Excel via PyXLL on Windows, with bidirectional data flow between Python/Excel and the embedded web content.

Development happens primarily on Mac for convenience; Windows/PyXLL/Excel is the deployment target.

It's a scratchpad repo. Dependencies are managed with `uv` and `pyproject.toml`.

## Running the Python/Qt Examples

```bash
uv sync    # install core deps (PySide6, geopandas, folium)
uv run python python_js_purescript_integration/qt_browser_widget.py    # QWebChannel demo
uv run python python_js_purescript_integration/folium_test.py          # Folium map
uv run python python_js_purescript_integration/pdf_test.py             # PDF viewer
```

PyDriller (for the standalone `pydriller_example.py` at repo root):
```bash
uv sync --extra git-mining
uv run python pydriller_example.py
```

Note: avoid brew/pyenv Python on Mac — caused segfaults historically. uv will pick up `/usr/local/bin/python3` (python.org install).

## Key Areas

### Python/Qt/JS integration (`python_js_purescript_integration/`)

The main active area. Three "smoke test" scripts and supporting plumbing:

- **`qt_browser_widget.py`** — QWebEngineView with QWebChannel bridge: JS button clicks invoke Python `@Slot()` methods. This is the minimal bidirectional communication example.
- **`qfolium.py`** — A custom Qt URL scheme handler (`folium://`) that routes URL requests to registered Python callables, renders Folium maps to HTML, and serves them to QWebEngineView. This is the reusable plumbing piece.
- **`folium_test.py`** — Uses `qfolium.py` to load Ireland counties shapefile onto a Leaflet map inside Qt.
- **`pdf_test.py`** — Opens a PDF in QWebEngineView using Qt's built-in PDF plugin.
- **Shapefile data** — `ireland_counties.*` (SHP/DBF/SHX/PRJ/CPG/QMD)

### PyDriller git mining (`pydriller_example.py`)

Traverses git commits from a given SHA, applies `mailmap.txt` to normalize author identities, emits JSON. The extensive comments describe a philosophy of treating git as a log/database and persisting commit chunks as JSON scalars.

### Browser-based PDF annotations (`js_pdf_annotations/`)

A standalone, server-free PDF viewer/annotator. Open `pdf-viewer.html` directly in a browser — no Python or build step needed. Uses PDF.js (rendering/reading annotations) and pdf-lib (creating/modifying annotations) via CDN. Supports highlight, text (sticky note), freetext, link, and stamp annotations. Includes sample PDFs (`glavel_receipt.pdf`, `annotated-document.pdf`).

This is the pure-JS complement to the Qt-based `pdf_test.py` — the eventual goal is driving these annotations programmatically from Python/Excel via the QWebChannel bridge.

### Root-level D3/Angular demo (historical)

`index.html` + `script.js` + `style.css` — AngularJS 1.x directive wrapping a D3 v3 bar chart. The original starting point of the repo.

### PostgreSQL FDW demo (`fdw_demo.sql`)

DDL for a Python-backed Foreign Data Wrapper exposing a financial library as a virtual table, with ipyparallel backend config. Standalone reference.

## Architecture & Design Direction

The core technical problem being explored: **how to bridge Python/Excel ↔ DOM (HTML/CSS/JS) bidirectionally**.

Key architectural decisions and constraints from Paul's design notes:

- **Qt WebEngine does not allow direct DOM access** — DOM manipulation must happen via script injection (`QWebEngineScript`, `QWebEnginePage.runJavaScript`) or QWebChannel.
- **QWebChannel** is the primary Python↔JS bridge mechanism. Python objects registered on the channel are callable from JS, and JS can send data back to Python via signals/slots.
- **Data-centric, not code-centric**: The bridge should use data-only expressions (like jmespath) for DOM↔JSON conversion, not embed executable code. This is deliberate for security.
  - DOM → JSON (Web to Excel): extract data from the DOM using CSS selectors + jmespath-like expressions
  - JSON → DOM (Excel to Web): drive the web view from spreadsheet data
- **Script injection** uses Greasemonkey-like `==UserScript==` attributes to control when scripts run (`@run-at document-start|document-end|document-idle`) and `worldId` to avoid conflicts with page scripts.
- **Target interaction patterns**: map zoom/pan/click events → Excel cells; Excel formula changes → map choroplets/zoom; PDF annotation from spreadsheet data; HTML table ↔ spreadsheet JOINs.
- PocketBase was floated as a possible config/clippings store but not yet implemented.

## Target Data Formats

Each has different interaction model requirements:

| Format | Interaction |
|--------|------------|
| Geospatial maps | Zoom/pan/click events ↔ Python; choropleth driven by spreadsheet data; get/set feature attributes |
| PDF documents | Table extraction matched against spreadsheet structure; LLM-driven annotation with bounding boxes |
| HTML tables | JOIN with spreadsheet tables; extract as JSON; add columns from spreadsheet |
| Emails/tickets | CTP view with metadata editing (prioritization) |
