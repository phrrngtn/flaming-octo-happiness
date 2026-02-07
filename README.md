# flaming-octo-happiness

Shared test & learn space for Paul & Andrew to prototype Python↔JavaScript↔DOM integration via PySide6/Qt WebEngine.

The longer-term goal is embedding rich web views (maps, PDFs, HTML tables) inside Excel via PyXLL, with bidirectional data flow between Python/Excel and the embedded web content.

## Quick Start

Requires Python 3.13+ (from [python.org](https://www.python.org/downloads/), not brew/pyenv) and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python python_js_purescript_integration/qt_browser_widget.py   # QWebChannel demo
uv run python python_js_purescript_integration/folium_test.py         # Leaflet map with Ireland counties
uv run python python_js_purescript_integration/pdf_test.py            # PDF viewer
```

For the git-mining script (pydriller):
```bash
uv sync --extra git-mining
uv run python pydriller_example.py
```

## What's Here

| Directory / File | What |
|-----------------|------|
| `python_js_purescript_integration/` | PySide6/Qt WebEngine experiments — embedded maps, PDFs, QWebChannel bridge |
| `pydriller_example.py` | Git commit mining with mailmap normalization, outputs JSON |
| `index.html` + `script.js` + `style.css` | Original AngularJS/D3 bar chart demo ([origin](http://codepen.io/odiseo42/pen/bCwkv)) |
| `fdw_demo.sql` | PostgreSQL Foreign Data Wrapper DDL for a Python-backed virtual table |

See `python_js_purescript_integration/TODO.md` for the design roadmap.
