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
from queue import Empty, Queue

from PySide6.QtCore import QFile, QIODeviceBase, QObject, QTimer, QUrl, Slot
from PySide6.QtWidgets import QApplication
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView


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
        props = evt.get("properties", {})
        name = props.get("NAME_1") or props.get("name") or props.get("NAME", "")
        ftype = props.get("TYPE_1") or props.get("type", "")
        label = f"{name} ({ftype})" if ftype else name

        if etype == "click":
            lat, lng = evt.get("lat", "?"), evt.get("lng", "?")
            if isinstance(lat, float):
                lat, lng = f"{lat:.4f}", f"{lng:.4f}"
            print(f"  [MAP {ts}] click: {label} at {lat}, {lng}", flush=True)
        elif etype in ("mouseover", "mouseout"):
            print(f"  [MAP {ts}] {etype}: {label}", flush=True)
        elif etype == "overlay_added":
            n = evt.get("featureCount", "?")
            print(f"  [MAP {ts}] overlay added ({n} features)", flush=True)
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


def load_geo_file(path_str):
    """Load a GeoJSON or Shapefile and return a GeoJSON string.

    Supports .geojson, .json (read as-is) and .shp (converted via geopandas).
    """
    p = Path(path_str).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    ext = p.suffix.lower()
    if ext in (".geojson", ".json"):
        return p.read_text(encoding="utf-8")
    elif ext == ".shp":
        import geopandas as gpd
        gdf = gpd.read_file(str(p))
        return gdf.to_json()
    else:
        raise ValueError(f"Unsupported format: {ext} (expected .geojson, .json, or .shp)")


def stdin_reader(cmd_queue):
    """Background thread: read file paths from stdin, put on queue."""
    while True:
        try:
            line = input("\n> Enter GeoJSON/Shapefile path: ").strip()
        except EOFError:
            break
        if not line:
            continue
        cmd_queue.put(line)


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
    cmd_queue = Queue()
    reader = threading.Thread(target=stdin_reader, args=(cmd_queue,), daemon=True)
    reader.start()

    # --- QTimer: poll command queue and inject GeoJSON --------------------
    pending = []  # buffer commands until the bridge is ready

    def process_commands():
        # Drain queue into pending list
        while True:
            try:
                pending.append(cmd_queue.get_nowait())
            except Empty:
                break

        if not backend.ready or not pending:
            return

        # Process all pending commands
        while pending:
            path_str = pending.pop(0)
            try:
                geojson_str = load_geo_file(path_str)
                # Call addOverlay() in UserWorld — defined by the extension JS
                js_call = f"addOverlay({json.dumps(geojson_str)})"
                page.runJavaScript(
                    js_call, QWebEngineScript.ScriptWorldId.UserWorld
                )
                print(f"  Injected: {path_str}", flush=True)
            except Exception as e:
                print(f"  Error: {e}", flush=True)

    timer = QTimer()
    timer.timeout.connect(process_commands)
    timer.start(100)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
