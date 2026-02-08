"""
PureScript ↔ Qt WebEngine Bridge launcher.

Adapted from map_bridge.py — same architecture (ConsolePage, Backend,
QWebChannel in UserWorld, script injection) but application-agnostic.

Usage:
    python ps_bridge.py <html_file> <bridge_js_file> [--auto-respond]

Example:
    uv run python purescript-bridge-demo/ps_bridge.py \
        purescript-bridge-demo/public/stage1.html \
        purescript-bridge-demo/ps_bridge.js

Once running, type JSON command strings at the prompt:
    {"command": "set-status", "text": "Hello from Python!"}

Ctrl+D (EOF) quits cleanly.
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
    # Signal for Python → JS communication via QWebChannel
    commandRequested = Signal(str)

    def __init__(self, auto_respond=False, parent=None):
        super().__init__(parent)
        self.ready = False
        self.auto_respond = auto_respond

    @Slot(str)
    def log(self, message):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"  [bridge {ts}] {message}", flush=True)
        if "ready" in message.lower():
            self.ready = True

    @Slot(str)
    def onPsEvent(self, event_json):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            evt = json.loads(event_json)
        except json.JSONDecodeError:
            print(f"  [PS {ts}] {event_json}", flush=True)
            return

        etype = evt.get("type", "?")
        print(f"  [PS {ts}] {etype}: {json.dumps(evt)}", flush=True)

        # Auto-respond mode: echo back matching commands
        if self.auto_respond:
            self._auto_respond(evt)

    def _auto_respond(self, evt):
        """Generate automatic responses for testing."""
        etype = evt.get("type", "")

        if etype == "click":
            color = evt.get("color", "unknown")
            self.commandRequested.emit(json.dumps({
                "command": "set-status",
                "text": f"Python saw click on {color}",
            }))
        elif etype == "counter":
            value = evt.get("value", 0)
            self.commandRequested.emit(json.dumps({
                "command": "set-status",
                "text": f"Python saw counter = {value}",
            }))
        elif etype == "item-clicked":
            label = evt.get("label", "?")
            self.commandRequested.emit(json.dumps({
                "command": "set-color",
                "color": "#ff6600",
            }))
        elif etype == "pong":
            print("  [PS] Pong received!", flush=True)
        elif etype == "node-hover":
            path = evt.get("path", "")
            self.commandRequested.emit(json.dumps({
                "command": "highlight",
                "path": path,
            }))
        elif etype == "node-click":
            self.commandRequested.emit(json.dumps({
                "command": "set-status",
                "text": f"Python saw node click: {evt.get('name', '?')}",
            }))


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
    """Background thread: read JSON command strings from stdin, emit via signal."""
    while True:
        try:
            line = input("\n> ").strip()
        except EOFError:
            print("\n  EOF — quitting.", flush=True)
            app.quit()
            return
        if not line:
            continue
        # Validate JSON
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            print(f"  Invalid JSON: {e}", flush=True)
            continue
        backend.commandRequested.emit(line)
        print(f"  Sent: {line}", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="PureScript ↔ Qt WebEngine Bridge launcher."
    )
    parser.add_argument("page_url", help="URL or file path of the HTML page to display")
    parser.add_argument("extension_js", help="Path to the JS bridge file to inject into UserWorld")
    parser.add_argument(
        "--auto-respond", action="store_true",
        help="Automatically respond to PureScript events with matching commands"
    )
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

    # Allow file:// pages to load remote CDN scripts if needed
    settings = page.settings()
    settings.setAttribute(
        QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
    )

    # --- QWebChannel in UserWorld ----------------------------------------
    channel = QWebChannel()
    backend = Backend(auto_respond=args.auto_respond)
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

    # 2. Bridge JS at DocumentReady (DOM must exist)
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
