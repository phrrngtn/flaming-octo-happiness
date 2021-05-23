from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import pyqtSlot
import sys

class BrowserQtWiget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create the browser widget
        self.browser = QWebEngineView(self)
        self.profile = QWebEngineProfile()
        self.page = QWebEnginePage(self.profile, self.browser)

        # Create the channel so JavaScript can talk to Python
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self)
        self.page.setWebChannel(self.channel)

        # Set some html on the page
        self.page.setHtml("""
            <html>
                <head>
                    <meta charset="utf-8"/>        
                    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
                </head>
                <body>
                    <h1>Hello!</h1>
                    <div>
                        <button id="button">Click Me</button>
                    </div>
                    <script>
                        // Hookup the button click event to our Python object
                        var backend;
                        new QWebChannel(qt.webChannelTransport, function (channel) {
                            backend = channel.objects.backend;
                        });
                
                        document.getElementById("button").addEventListener("click", function(){
                            backend.on_button_clicked();
                        });
                    </script>
                </body>
            </html>
            """)

        self.browser.setPage(self.page)

        # Add the browser to the widgets layout
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        self.setLayout(layout)

    @pyqtSlot()
    def on_button_clicked(self):
        print("Button clicked!")


def open_browser(*args):
    app = QApplication.instance()
    if app is None:
        app = QApplication([sys.executable])

    browser = BrowserQtWiget()
    create_ctp(browser)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = BrowserQtWiget()
    widget.show()
    app.exec_()
