import io
import os
import sys


import folium


from PySide6 import QtCore, QtWidgets, QtWebEngineWidgets
import geopandas as gpd

from qfolium import FoliumApplication


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

folium_app = FoliumApplication()


@folium_app.register("load_shapefile")
def load_shapefile(latitude, longitude, zoom_start, shp_filename):
    shp_file = gpd.read_file(shp_filename)
    shp_file_json_str = shp_file.to_json()
    print(shp_file_json_str[:100])
    m = folium.Map(location=[latitude, longitude], zoom_start=zoom_start)
    folium.GeoJson(shp_file_json_str).add_to(m)
    print(m)
    return m


class LeafWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.view = QtWebEngineWidgets.QWebEngineView()

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.view)

        self.resize(640, 480)

        shp_filename = os.path.join(CURRENT_DIR, "ireland_counties.shp")

        params = {
            "shp_filename": shp_filename,
            "latitude": 53,
            "longitude": -7.5,
            "zoom_start": 5,
        }
        url = folium_app.create_url("load_shapefile", params=params)
        self.view.load(url)


def main():
    app = QtWidgets.QApplication([])
    folium_app.init_handler()
    w = LeafWidget()
    w.show()
    app.exec()


if __name__ == "__main__":

    main()
