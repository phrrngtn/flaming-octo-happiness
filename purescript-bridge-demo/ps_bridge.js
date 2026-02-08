/**
 * ps_bridge.js — Generic UserWorld bridge for PureScript ↔ Qt WebEngine
 *
 * Injected into UserWorld by ps_bridge.py.  Application-agnostic:
 *
 *   PS → Python:  Listens for __ps_event__ on document,
 *                  calls backend.onPsEvent(JSON.stringify(detail))
 *
 *   Python → PS:  Subscribes to backend.commandRequested signal,
 *                  dispatches __qt_command__ CustomEvent with parsed JSON detail
 *
 * The DOM is shared between UserWorld and MainWorld, so CustomEvents
 * cross the boundary naturally (same pattern as leaflet_bridge.js).
 */
(function () {
    "use strict";

    new QWebChannel(qt.webChannelTransport, function (channel) {
        var backend = channel.objects.backend;
        backend.log("PureScript bridge connected in UserWorld");

        // PS → Python: forward CustomEvents to Python via QWebChannel slot
        document.addEventListener("__ps_event__", function (e) {
            backend.onPsEvent(JSON.stringify(e.detail));
        });

        // Python → PS: forward signal to CustomEvent on shared DOM
        backend.commandRequested.connect(function (jsonStr) {
            var detail;
            try {
                detail = JSON.parse(jsonStr);
            } catch (err) {
                backend.log("Failed to parse command JSON: " + err);
                return;
            }
            document.dispatchEvent(
                new CustomEvent("__qt_command__", { detail: detail })
            );
        });

        backend.log("PureScript bridge ready");
    });
})();
