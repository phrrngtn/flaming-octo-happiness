"""
Load a web page and inject a JS extension into an isolated UserWorld,
bridged to Python via QWebChannel.  Like a browser extension: the page
cannot see or tamper with the extension, but the extension can observe
and manipulate the page's DOM.

Usage:
    python map_bridge.py <page_url> <extension_js_file>

Example — Leaflet map with GeoJSON overlay driven from Python:
    python map_bridge.py folium_test.html leaflet_bridge.js

Once running, type a GeoJSON or Shapefile path at the prompt to push
an overlay onto the map.  Map events (click, mouseover) are logged
back to the terminal.
"""

import argparse
import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QFile, QIODeviceBase, QObject, QUrl, Signal, Slot
from PySide6.QtWidgets import QApplication
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

from geodata import build_metadata, load_geo_file


# ---------------------------------------------------------------------------
# ConsolePage — JS console.log/warn/error → Python stdout
# ---------------------------------------------------------------------------
class ConsolePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        level_str = {
            QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel: "INFO",
            QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel: "WARN",
            QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel: "ERROR",
        }.get(level, "DEBUG")
        print(f"  [JS {level_str}] {source}:{line}: {message}", flush=True)


# ---------------------------------------------------------------------------
# Backend — Python object exposed to UserWorld JS via QWebChannel
# ---------------------------------------------------------------------------
class Backend(QObject):
    # Signals for Python → JS communication via QWebChannel
    addOverlayRequested = Signal(str, str)
    removeOverlaysRequested = Signal()
    setOverlayStyleRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ready = False

    @Slot(str)
    def log(self, message):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"  [bridge {ts}] {message}", flush=True)
        if "ready" in message.lower():
            self.ready = True

    @Slot(str)
    def onMapEvent(self, event_json):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            evt = json.loads(event_json)
        except json.JSONDecodeError:
            print(f"  [MAP {ts}] {event_json}", flush=True)
            return

        etype = evt.get("type", "?")
        name = evt.get("name", "")
        code = evt.get("code", "")
        label = f"{name} [{code}]" if code else name

        if etype == "click":
            lat, lng = evt.get("lat", "?"), evt.get("lng", "?")
            if isinstance(lat, float):
                lat, lng = f"{lat:.4f}", f"{lng:.4f}"
            print(f"  [MAP {ts}] click: {label} at {lat}, {lng}", flush=True)
        elif etype in ("mouseover", "mouseout"):
            print(f"  [MAP {ts}] {etype}: {label}", flush=True)
        elif etype == "overlay_added":
            n = evt.get("featureCount", "?")
            ds = evt.get("label", "")
            desc = f"{ds} ({n} features)" if ds else f"{n} features"
            print(f"  [MAP {ts}] overlay added: {desc}", flush=True)
        elif etype == "error":
            print(f"  [MAP {ts}] ERROR: {evt.get('message', event_json)}", flush=True)
        else:
            print(f"  [MAP {ts}] {etype}: {event_json}", flush=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def read_qwebchannel_js():
    """Read the bundled qwebchannel.js from Qt resources."""
    f = QFile(":/qtwebchannel/qwebchannel.js")
    if not f.open(QIODeviceBase.OpenModeFlag.ReadOnly):
        raise RuntimeError("Failed to open qwebchannel.js from Qt resources")
    content = f.readAll().data().decode("utf-8")
    f.close()
    return content


def stdin_loop(backend, app):
    """Background thread: read file paths from stdin, load and send via signal."""
    while True:
        try:
            line = input("\n> Enter GeoJSON/Shapefile path: ").strip()
        except EOFError:
            print("\n  EOF — quitting.", flush=True)
            app.quit()
            return
        if not line:
            continue
        try:
            geojson_str = load_geo_file(line)
            metadata = build_metadata(geojson_str, line)
            print(f"  Metadata: {json.dumps(metadata)}", flush=True)
            backend.addOverlayRequested.emit(geojson_str, json.dumps(metadata))
            print(f"  Injected: {line}", flush=True)
        except Exception as e:
            print(f"  Error: {e}", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Load a web page with a UserWorld JS extension bridge."
    )
    parser.add_argument("page_url", help="URL or file path of the web page to display")
    parser.add_argument("extension_js", help="Path to the JS file to inject into UserWorld")
    args = parser.parse_args()

    # Resolve page URL
    page_url = QUrl.fromUserInput(args.page_url, os.getcwd())
    if not page_url.isValid():
        print(f"Invalid page URL: {args.page_url}", file=sys.stderr)
        sys.exit(1)

    # Read extension JS
    ext_js_path = Path(args.extension_js).expanduser().resolve()
    if not ext_js_path.exists():
        print(f"Extension JS not found: {ext_js_path}", file=sys.stderr)
        sys.exit(1)
    extension_js = ext_js_path.read_text(encoding="utf-8")

    app = QApplication(sys.argv)

    # --- Page & view -----------------------------------------------------
    page = ConsolePage()
    view = QWebEngineView()
    view.setPage(page)

    # Allow file:// pages to load remote CDN scripts (Leaflet, etc.)
    settings = page.settings()
    settings.setAttribute(
        QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
    )

    # --- QWebChannel in UserWorld ----------------------------------------
    channel = QWebChannel()
    backend = Backend()
    channel.registerObject("backend", backend)
    page.setWebChannel(channel, QWebEngineScript.ScriptWorldId.UserWorld)

    # --- Script injection into UserWorld ---------------------------------
    # 1. qwebchannel.js at DocumentCreation (must be available first)
    qwc_script = QWebEngineScript()
    qwc_script.setName("qwebchannel")
    qwc_script.setWorldId(QWebEngineScript.ScriptWorldId.UserWorld)
    qwc_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    qwc_script.setSourceCode(read_qwebchannel_js())
    page.scripts().insert(qwc_script)

    # 2. Extension JS at DocumentReady (DOM must exist)
    ext_script = QWebEngineScript()
    ext_script.setName("extension")
    ext_script.setWorldId(QWebEngineScript.ScriptWorldId.UserWorld)
    ext_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
    ext_script.setSourceCode(extension_js)
    page.scripts().insert(ext_script)

    # --- Load the page ---------------------------------------------------
    print(f"Loading {page_url.toString()}", flush=True)
    print(f"Extension: {ext_js_path.name}", flush=True)
    view.load(page_url)
    view.resize(1024, 768)
    view.show()

    # --- Stdin reader thread ---------------------------------------------
    reader = threading.Thread(
        target=stdin_loop, args=(backend, app), daemon=True
    )
    reader.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
