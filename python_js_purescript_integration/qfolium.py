import json
import io

from PySide6 import QtCore, QtWidgets, QtWebEngineWidgets, QtWebEngineCore
from PySide6.QtWebEngineCore import (
    QWebEngineSettings,
    QWebEngineUrlSchemeHandler,
    QWebEngineProfile,
)


class FoliumSchemeHandler(QWebEngineUrlSchemeHandler):
    def __init__(self, app):
        super().__init__(app)
        self.m_app = app

    def requestStarted(self, request):
        url = request.requestUrl()
        name = url.host()
        m = self.m_app.process(name, url.query())
        if m is None:
            request.fail(QtWebEngineCore.QWebEngineUrlRequestJob.UrlNotFound)
            return
        data = io.BytesIO()
        m.save(data, close_file=False)
        raw_html = data.getvalue()
        buf = QtCore.QBuffer(parent=self)
        request.destroyed.connect(buf.deleteLater)
        buf.open(QtCore.QIODevice.WriteOnly)
        buf.write(raw_html)
        buf.seek(0)
        buf.close()
        request.reply(b"text/html", buf)


# From https://stackoverflow.com/a/64493467/40387
class FoliumApplication(QtCore.QObject):
    scheme = b"folium"

    def __init__(self, parent=None):
        super().__init__(parent)
        scheme = QtWebEngineCore.QWebEngineUrlScheme(self.scheme)
        QtWebEngineCore.QWebEngineUrlScheme.registerScheme(scheme)
        self.m_functions = dict()

    def init_handler(self, profile=None):
        if profile is None:
            profile = QWebEngineProfile.defaultProfile()
        handler = profile.urlSchemeHandler(self.scheme)
        if handler is not None:
            profile.removeUrlSchemeHandler(handler)

        self.m_handler = FoliumSchemeHandler(self)
        profile.installUrlSchemeHandler(self.scheme, self.m_handler)

    def register(self, name):
        def decorator(f):
            self.m_functions[name] = f
            return f

        return decorator

    def process(self, name, query):
        f = self.m_functions.get(name)
        if f is None:
            print("not found")
            return

        items = QtCore.QUrlQuery(query).queryItems()
        params_json = dict(items).get("json", None)
        if params_json is not None:
            return f(**json.loads(params_json))
        return f()

    def create_url(self, name, params=None):
        url = QtCore.QUrl()
        url.setScheme(self.scheme.decode())
        url.setHost(name)
        if params is not None:
            params_json = json.dumps(params)
            query = QtCore.QUrlQuery()
            query.addQueryItem("json", params_json)
            url.setQuery(query)
        return url
