import sys
from PySide6.QtCore import QFile, QIODeviceBase, QObject, Signal, Slot
from PySide6.QtWidgets import QApplication
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView


class ConsolePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        level_str = {
            QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel: "INFO",
            QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel: "WARNING",
            QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel: "ERROR",
        }.get(level, "DEBUG")
        print(f"[JS {level_str}] {source}:{line}: {message}")


def read_qwebchannel_js():
    """Read the bundled qwebchannel.js from Qt resources."""
    f = QFile(":/qtwebchannel/qwebchannel.js")
    if not f.open(QIODeviceBase.OpenModeFlag.ReadOnly):
        raise RuntimeError("Failed to open qwebchannel.js from Qt resources")
    content = f.readAll().data().decode("utf-8")
    f.close()
    return content

class Backend(QObject):
    dataReceived = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    @Slot(str)
    def sendData(self, data):
        print("Backend received data:", data)
        # Emit signal which can be picked up by the other JS world
        self.dataReceived.emit(f"From Qt: {data.upper()}")

# Set up the QApplication, QWebEngineView and QWebChannel
app = QApplication(sys.argv)
page = ConsolePage()
view = QWebEngineView()
view.setPage(page)
channel = QWebChannel()
backend = Backend()
channel.registerObject("backend", backend)
# Register the channel for UserWorld (qt.webChannelTransport is only injected
# into the world you specify here; default is MainWorld)
view.page().setWebChannel(channel, QWebEngineScript.ScriptWorldId.UserWorld)

# Inject qwebchannel.js into UserWorld so `new QWebChannel(...)` is available
qwebchannel_js = read_qwebchannel_js()

qwc_script = QWebEngineScript()
qwc_script.setName("qwebchannel")
qwc_script.setWorldId(QWebEngineScript.ScriptWorldId.UserWorld)
qwc_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
qwc_script.setSourceCode(qwebchannel_js)
view.page().scripts().insert(qwc_script)

# Script for UserWorld
script_user = QWebEngineScript()
script_user.setName("user_world_script")
script_user.setWorldId(QWebEngineScript.ScriptWorldId.UserWorld)
script_user.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
script_user.setSourceCode(
    """
    new QWebChannel(qt.webChannelTransport, function(channel) {
        window.backend = channel.objects.backend;
        window.backend.dataReceived.connect(function(data) {
            console.log("UserWorld received from Qt:", data);
        });
        window.backend.sendData("Hello from UserWorld!");
    });
    """
)
view.page().scripts().insert(script_user)

view.setHtml("<html><body><h1>WebChannel Test</h1></body></html>")
view.show()
sys.exit(app.exec())