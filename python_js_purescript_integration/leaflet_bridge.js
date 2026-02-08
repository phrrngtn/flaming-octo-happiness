/**
 * leaflet_bridge.js — UserWorld extension for Leaflet maps
 *
 * Injected into UserWorld by map_bridge.py.  Mirrors the Chrome-extension
 * content-script / page-script split:
 *
 *   UserWorld  (this file)    — owns QWebChannel to Python; no access to
 *                               the page's JS globals (map, L, etc.)
 *   MainWorld  (helper below) — has access to Leaflet; communicates with
 *                               UserWorld via CustomEvents on the shared DOM
 *
 * Python→JS API (via QWebChannel signals on the Backend object):
 *   addOverlayRequested(geojsonStr, metadataJsonStr)
 *       Add a GeoJSON layer.  metadataJsonStr is a JSON object with:
 *         label   — dataset name (e.g. "scottish_council_areas")
 *         mapping — {canonical: actualPropertyName} for normalizing events
 *                   canonical keys: name, code, type, parent
 *   removeOverlaysRequested()             — remove all previously added overlays
 *   setOverlayStyleRequested(styleJsonStr) — change the default style for new layers
 */
(function () {
    "use strict";

    // ------------------------------------------------------------------
    // 1. Inject a helper <script> into the DOM — runs in MainWorld
    // ------------------------------------------------------------------
    var helper = document.createElement("script");
    helper.textContent = [
        "(function () {",
        "  var layers = [];",
        "  var defaultStyle = {color:'#ff7800', weight:2, fillOpacity:0.2};",
        "",
        "  function getMap() {",
        "    // Leaflet stores a back-reference on the container element.",
        "    var el = document.getElementById('map');",
        "    if (!el) return null;",
        "    // L.map sets el._leaflet_id; the instance lives on the key",
        "    // '_leaflet_map' (Leaflet ≥ 1.9) or we can iterate.",
        "    if (typeof map !== 'undefined') return map;",  // top-level var
        "    for (var k in el) {",
        "      if (el[k] && el[k] instanceof L.Map) return el[k];",
        "    }",
        "    return null;",
        "  }",
        "",
        "  function dispatch(type, detail) {",
        "    document.dispatchEvent(",
        "      new CustomEvent('__map_event__', {detail: Object.assign({type:type}, detail)})",
        "    );",
        "  }",
        "",
        "  // --- Add overlay -----------------------------------------------",
        "  document.addEventListener('__add_overlay__', function (e) {",
        "    var m = getMap();",
        "    if (!m) { dispatch('error', {message:'Leaflet map not found'}); return; }",
        "    try {",
        "      var data = JSON.parse(e.detail.geojson);",
        "    } catch(err) { dispatch('error', {message:'Invalid GeoJSON: '+err}); return; }",
        "",
        "    var meta = e.detail.metadata || {};",
        "    var map_ = meta.mapping || {};",
        "",
        "    // Resolve canonical fields from raw properties using the mapping",
        "    function resolve(props) {",
        "      var out = {};",
        "      for (var canon in map_) {",
        "        var key = map_[canon];",
        "        if (key && props[key] != null) out[canon] = props[key];",
        "      }",
        "      return out;",
        "    }",
        "",
        "    var layer = L.geoJSON(data, {",
        "      style: e.detail.style ? JSON.parse(e.detail.style) : defaultStyle,",
        "      onEachFeature: function (feature, lyr) {",
        "        var props = feature.properties || {};",
        "        var norm = resolve(props);",
        "        var name = norm.name || '';",
        "        var subtitle = norm.type || norm.parent || '';",
        "        if (name) {",
        "          lyr.bindPopup('<strong>' + name + '</strong>' + (subtitle ? '<br>' + subtitle : ''));",
        "          lyr.bindTooltip(name);",
        "        }",
        "        lyr.on('click', function (ev) {",
        "          dispatch('click', Object.assign({}, norm, {lat:ev.latlng.lat, lng:ev.latlng.lng}));",
        "        });",
        "        lyr.on('mouseover', function () {",
        "          dispatch('mouseover', norm);",
        "          lyr.setStyle({weight:4, fillOpacity:0.4});",
        "        });",
        "        lyr.on('mouseout', function () {",
        "          dispatch('mouseout', norm);",
        "          lyr.setStyle(e.detail.style ? JSON.parse(e.detail.style) : defaultStyle);",
        "        });",
        "      }",
        "    }).addTo(m);",
        "",
        "    layers.push(layer);",
        "    m.fitBounds(layer.getBounds());",
        "    dispatch('overlay_added', {",
        "      label: meta.label || '',",
        "      featureCount: data.features ? data.features.length : 0,",
        "      layerIndex: layers.length - 1",
        "    });",
        "  });",
        "",
        "  // --- Remove overlays -------------------------------------------",
        "  document.addEventListener('__remove_overlays__', function () {",
        "    var m = getMap();",
        "    layers.forEach(function (l) { if (m) m.removeLayer(l); });",
        "    layers = [];",
        "    dispatch('overlays_removed', {});",
        "  });",
        "",
        "  // --- Set default style -----------------------------------------",
        "  document.addEventListener('__set_style__', function (e) {",
        "    defaultStyle = JSON.parse(e.detail.style);",
        "  });",
        "",
        "  dispatch('helper_ready', {});",
        "})();"
    ].join("\n");
    document.head.appendChild(helper);

    // ------------------------------------------------------------------
    // 2. Connect QWebChannel and wire up event forwarding
    // ------------------------------------------------------------------
    new QWebChannel(qt.webChannelTransport, function (channel) {
        var backend = channel.objects.backend;
        backend.log("Leaflet bridge connected in UserWorld");

        // Forward map events from MainWorld → Python
        document.addEventListener("__map_event__", function (e) {
            backend.onMapEvent(JSON.stringify(e.detail));
        });

        // Subscribe to Python signals via QWebChannel — no eval needed
        backend.addOverlayRequested.connect(function (geojsonStr, metadataJsonStr) {
            var metadata = {};
            try { metadata = JSON.parse(metadataJsonStr); } catch (e) {}
            document.dispatchEvent(
                new CustomEvent("__add_overlay__", {
                    detail: {
                        geojson: geojsonStr,
                        style: null,
                        metadata: metadata,
                    },
                })
            );
        });

        backend.removeOverlaysRequested.connect(function () {
            document.dispatchEvent(new CustomEvent("__remove_overlays__"));
        });

        backend.setOverlayStyleRequested.connect(function (styleJsonStr) {
            document.dispatchEvent(
                new CustomEvent("__set_style__", { detail: { style: styleJsonStr } })
            );
        });

        backend.log("Leaflet bridge ready — emit addOverlayRequested to add layers");
    });
})();
