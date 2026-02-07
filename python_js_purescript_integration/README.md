Check that the xcode command line tools are installed:
```shell
xcode-select -p
```

We use [uv](https://docs.astral.sh/uv/) for dependency management. From the repo root:

```shell
uv sync
```

Run the smoke-test programs:
```shell
uv run python python_js_purescript_integration/qt_browser_widget.py
uv run python python_js_purescript_integration/folium_test.py
uv run python python_js_purescript_integration/pdf_test.py
```

Note: we assume Python installed from python.org (`/usr/local/bin/python3`). Avoid brew/pyenv Python on Mac — caused segfaults historically.
