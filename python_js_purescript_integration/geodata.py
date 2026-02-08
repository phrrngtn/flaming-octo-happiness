"""Load geographic data files and build normalized metadata for the bridge.

Supports GeoJSON (.geojson, .json), Shapefiles (.shp), and zipped
Shapefiles (.zip).  Shapefiles are reprojected to EPSG:4326 (WGS84)
for use with Leaflet.

build_metadata() inspects feature properties and produces a canonical
mapping so that downstream code (JS bridge, Python event handlers) can
work with consistent field names regardless of the source dataset.
"""

import json
from pathlib import Path


def load_geo_file(path_str):
    """Load a GeoJSON, Shapefile, or zipped Shapefile and return a GeoJSON string.

    Supports .geojson/.json (read as-is), .shp, and .zip (via geopandas).
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
        if gdf.crs and not gdf.crs.equals("EPSG:4326"):
            gdf = gdf.to_crs(epsg=4326)
        return gdf.to_json()
    elif ext == ".zip":
        import geopandas as gpd
        gdf = gpd.read_file(f"zip://{p}")
        if gdf.crs and not gdf.crs.equals("EPSG:4326"):
            gdf = gdf.to_crs(epsg=4326)
        return gdf.to_json()
    else:
        raise ValueError(f"Unsupported format: {ext} (expected .geojson, .json, .shp, or .zip)")


def build_metadata(geojson_str, source_path):
    """Build an overlay metadata dict with a property mapping for normalization.

    Inspects the first feature's properties to map canonical keys to the
    actual attribute names in this dataset.  Canonical keys:

        name   — primary display name  (e.g. county, district, comarca)
        code   — official identifier   (e.g. ISO code, ONS code)
        type   — feature category      (e.g. "County", "City")
        parent — parent admin unit     (e.g. country, province)

    The JS side uses this mapping so that events sent back to Python always
    carry the same canonical keys regardless of the source dataset.
    """
    data = json.loads(geojson_str)
    features = data.get("features", [])
    props = features[0].get("properties", {}) if features else {}
    keys = list(props.keys())
    keys_lower = {k: k.lower() for k in keys}

    def _find(*patterns):
        """Return the first property key whose lowercased form contains any pattern."""
        for pat in patterns:
            for k, kl in keys_lower.items():
                if pat in kl:
                    return k
        return None

    def _find_suffix(*suffixes):
        """Return the first property key whose lowercased form ends with a suffix."""
        for suf in suffixes:
            for k, kl in keys_lower.items():
                if kl.endswith(suf):
                    return k
        return None

    mapping = {}

    # name: the most important — display label for each feature
    mapping["name"] = (
        _find("name", "nom", "nombre")
        or _find_suffix("nm")  # ONS convention: LAD13NM, etc.
        # fall back to first non-null string property
        or next((k for k in keys if isinstance(props[k], str) and props[k].strip()), None)
    )

    # code: administrative/reference identifier
    mapping["code"] = (
        _find("iso", "code", "hasc", "fips")
        or _find_suffix("cd")  # ONS convention: LAD13CD, etc.
    )

    # type: feature classification
    mapping["type"] = _find("type", "tipo", "engtype")

    # parent: containing administrative unit
    mapping["parent"] = _find("country", "province", "provincia", "region", "parent")

    # strip None values
    mapping = {k: v for k, v in mapping.items() if v is not None}

    return {
        "label": Path(source_path).stem,
        "mapping": mapping,
    }
