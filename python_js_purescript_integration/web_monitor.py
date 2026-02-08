"""
Load an arbitrary web page and observe DOM mutations via a UserWorld-injected
MutationObserver, bridged back to Python through QWebChannel.

Works like a browser extension: the injected JS runs in an isolated world so
it cannot be seen or tampered with by the page's own scripts, but it can
observe the full DOM.

Usage:
    uv run python python_js_purescript_integration/web_monitor.py https://example.com
"""

import argparse
import sys
from datetime import datetime

from PySide6.QtCore import QFile, QIODeviceBase, QObject, QUrl, Signal, Slot
from PySide6.QtWidgets import QApplication
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView


# ---------------------------------------------------------------------------
# ConsolePage – route JS console.log/warn/error to Python stdout
# ---------------------------------------------------------------------------
class ConsolePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        level_str = {
            QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel: "INFO",
            QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel: "WARNING",
            QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel: "ERROR",
        }.get(level, "DEBUG")
        print(f"[JS {level_str}] {source}:{line}: {message}", flush=True)


# ---------------------------------------------------------------------------
# Backend – Python object exposed to the UserWorld JS via QWebChannel
# ---------------------------------------------------------------------------
class Backend(QObject):
    """Receives log messages and DOM mutation reports from injected JS."""

    dataReceived = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    @Slot(str)
    def log(self, message):
        """General-purpose log forwarding from JS → Python."""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[JS→Py  {ts}] {message}", flush=True)

    @Slot(str)
    def onMutation(self, summary):
        """Called by the MutationObserver bridge whenever the DOM changes."""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[MUTATE {ts}] {summary}", flush=True)


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


# ---------------------------------------------------------------------------
# The JS injected into UserWorld – acts like a browser extension content script
# ---------------------------------------------------------------------------
USERWORLD_JS = """\
(function() {
    "use strict";

    new QWebChannel(qt.webChannelTransport, function(channel) {
        var backend = channel.objects.backend;
        backend.log("QWebChannel connected in UserWorld – setting up MutationObserver");

        // --- MutationObserver -------------------------------------------
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(m) {
                var parts = [];

                // What kind of mutation?
                parts.push("type=" + m.type);

                // Which element?
                if (m.target) {
                    var tag = m.target.nodeName || "";
                    var id  = m.target.id ? "#" + m.target.id : "";
                    var cls = m.target.className && typeof m.target.className === "string"
                              ? "." + m.target.className.trim().split(/\\s+/).join(".")
                              : "";
                    parts.push("target=" + tag + id + cls);
                }

                if (m.type === "attributes") {
                    parts.push("attr=" + m.attributeName);
                    var newVal = m.target.getAttribute(m.attributeName);
                    if (newVal !== null && newVal.length < 120) {
                        parts.push("value=" + newVal);
                    }
                }

                if (m.type === "childList") {
                    if (m.addedNodes.length)   parts.push("added=" + m.addedNodes.length);
                    if (m.removedNodes.length)  parts.push("removed=" + m.removedNodes.length);
                }

                if (m.type === "characterData") {
                    var text = (m.target.textContent || "").substring(0, 80);
                    parts.push("text=" + JSON.stringify(text));
                }

                backend.onMutation(parts.join(" | "));
            });
        });

        // Observe everything on <body> (or documentElement if body isn't ready)
        var root = document.body || document.documentElement;
        observer.observe(root, {
            childList: true,
            attributes: true,
            characterData: true,
            subtree: true
        });

        backend.log("MutationObserver attached to <" + root.nodeName + ">");
    });
})();
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Load a web page and log DOM mutations to Python via QWebChannel."
    )
    parser.add_argument("url", help="URL to load (e.g. https://example.com)")
    args = parser.parse_args()

    url = QUrl.fromUserInput(args.url)
    if not url.isValid():
        print(f"Invalid URL: {args.url}", file=sys.stderr)
        sys.exit(1)

    app = QApplication(sys.argv)

    # --- Page & view -----------------------------------------------------
    page = ConsolePage()
    view = QWebEngineView()
    view.setPage(page)

    # --- QWebChannel in UserWorld ----------------------------------------
    channel = QWebChannel()
    backend = Backend()
    channel.registerObject("backend", backend)
    page.setWebChannel(channel, QWebEngineScript.ScriptWorldId.UserWorld)

    # Inject qwebchannel.js into UserWorld at DocumentCreation so it is
    # available before our observer script runs.
    qwc_script = QWebEngineScript()
    qwc_script.setName("qwebchannel")
    qwc_script.setWorldId(QWebEngineScript.ScriptWorldId.UserWorld)
    qwc_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    qwc_script.setSourceCode(read_qwebchannel_js())
    page.scripts().insert(qwc_script)

    # Inject our MutationObserver bridge into UserWorld at DocumentReady
    # (the DOM needs to exist before we can attach the observer).
    observer_script = QWebEngineScript()
    observer_script.setName("mutation_observer")
    observer_script.setWorldId(QWebEngineScript.ScriptWorldId.UserWorld)
    observer_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
    observer_script.setSourceCode(USERWORLD_JS)
    page.scripts().insert(observer_script)

    # --- Load the target URL ---------------------------------------------
    print(f"Loading {url.toString()} ...", flush=True)
    view.load(url)
    view.resize(1024, 768)
    view.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
