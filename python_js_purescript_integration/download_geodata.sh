#!/bin/sh
# Download sample boundary GeoJSON files for testing with map_bridge.py
set -e

cd "$(dirname "$0")"

echo "Downloading Scottish council area boundaries..."
curl -fLO https://raw.githubusercontent.com/martinjc/UK-GeoJSON/master/json/administrative/sco/lad.json
mv lad.json scottish_council_areas.geojson

echo "Downloading Catalan comarca boundaries..."
curl -fLo catalan_comarques.geojson https://raw.githubusercontent.com/sirisacademic/catalonia-cartography/master/shapefiles_catalunya_comarcas.geojson

echo "Done."
ls -lh scottish_council_areas.geojson catalan_comarques.geojson
