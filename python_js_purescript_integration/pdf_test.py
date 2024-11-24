import sys
from PySide6 import QtCore, QtWidgets, QtWebEngineWidgets
from PySide6.QtWebEngineCore import QWebEngineSettings


def main():

    print(f"PySide6 version: {QtCore.qVersion()}")

    app = QtWidgets.QApplication(sys.argv)
    filename, _ = QtWidgets.QFileDialog.getOpenFileName(None, filter="PDF (*.pdf)")
    if not filename:
        print("please select the .pdf file")
        sys.exit(0)
    view = QtWebEngineWidgets.QWebEngineView()
    settings = view.settings()
    settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
    url = QtCore.QUrl.fromLocalFile(filename)
    view.load(url)
    view.resize(640, 480)
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
