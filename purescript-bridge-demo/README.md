# PureScript ↔ Qt WebEngine Bridge Demo

Bidirectional communication between PureScript/Halogen apps and Python via Qt WebEngine's QWebChannel — using the same browser-extension-style UserWorld injection pattern as `map_bridge.py`.

4 progressive stages, each adding a layer of complexity.

## Quick Start

```bash
cd purescript-bridge-demo

# Install PureScript deps + build (one time)
spago build

# Bundle whichever stage you want
spago bundle --module Stage1.Main --outfile public/stage1-bundle.js --platform browser
spago bundle --module Stage2.Main --outfile public/stage2-bundle.js --platform browser
spago bundle --module Stage3.Main --outfile public/stage3-bundle.js --platform browser
spago bundle --module Stage4.Main --outfile public/stage4-bundle.js --platform browser

# Launch (from repo root)
cd ..
uv run python purescript-bridge-demo/ps_bridge.py \
    purescript-bridge-demo/public/stage1.html \
    purescript-bridge-demo/ps_bridge.js \
    --auto-respond
```

Close the Qt window to quit.

## Stages

### Stage 1: Vanilla PureScript DOM

Minimal proof of concept — no framework, just `web-dom` and `web-uievents`.

- Three colored buttons (Red, Green, Blue) and a status display
- Click a button → PS dispatches `__ps_event__` → Python logs `{"type":"click","color":"red"}`
- `--auto-respond` sends `set-status` back → status div updates

**Try typing at the prompt:**
```json
{"command": "set-status", "text": "Hello from Python!"}
```

### Stage 2: Halogen App

Same bridge, but Halogen manages all state and rendering.

- Counter with +/- buttons, ON/OFF toggle, status display
- Uses the `HS.create`/`HS.notify` subscription pattern to route bridge events into Halogen actions
- Counter changes dispatch `{"type":"counter","value":5}` to Python
- Toggle dispatches `{"type":"toggle","value":true}`

**Try typing at the prompt:**
```json
{"command": "set-counter", "value": 42}
{"command": "set-toggle", "value": true}
{"command": "set-status", "text": "Controlled from Python"}
```

### Stage 3: Bidirectional Control

Structured command/event protocol with a dynamic item list.

- Colored items that can be clicked, added, removed
- Counter with +/- buttons
- Click an item → PS sends `{"type":"item-clicked","id":1,"label":"Apple"}`
- `--auto-respond` sends `set-color` back, changing the accent color
- The "Last event sent" area shows the raw JSON of each outgoing event

**Try typing at the prompt:**
```json
{"command": "add-item", "label": "Python Item", "color": "#c9a227"}
{"command": "remove-item", "id": 2}
{"command": "set-color", "color": "#c23b22"}
{"command": "ping"}
```

`ping` triggers a `pong` event back from PS.

### Stage 4: Hylograph Tree Visualization

Real `hylograph-layout` tree visualization with pure Halogen SVG rendering — no D3 CDN.

- Renders a sample project tree using the Reingold-Tilford algorithm
- Hover a node → highlights ancestors/descendants, dispatches `{"type":"node-hover","path":"Project.src.Utils"}`
- Click a node → dispatches `{"type":"node-click","name":"Utils","path":"Project.src.Utils"}`
- `--auto-respond` echoes highlight commands back
- Node labels appear above each circle

**Try typing at the prompt:**
```json
{"command": "highlight", "path": "Project.src.Components"}
{"command": "set-status", "text": "Highlighted from Python!"}
{"command": "clear-highlight"}
```

## Architecture

```
PureScript (MainWorld)              UserWorld bridge              Python
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────┐
│ Halogen component    │     │ ps_bridge.js         │     │ ps_bridge.py │
│                      │     │                      │     │              │
│ dispatchPsEvent(json)│────>│ __ps_event__         │     │              │
│   (CustomEvent on    │     │   → backend.onPsEvent│────>│ onPsEvent()  │
│    document)         │     │     (QWebChannel)    │     │   (prints)   │
│                      │     │                      │     │              │
│ subscribeQtCommands()│<────│ __qt_command__        │     │              │
│   (listens for       │     │   ← commandRequested │<────│ stdin / auto │
│    CustomEvent)      │     │     (QWebChannel)    │     │   respond    │
└─────────────────────┘     └──────────────────────┘     └──────────────┘
```

Key insight: the DOM is shared between MainWorld and UserWorld, so `CustomEvent`s on `document` cross the boundary naturally. The UserWorld bridge (`ps_bridge.js`) acts as a relay — forwarding CustomEvents to/from QWebChannel slots/signals. This is the same pattern as `leaflet_bridge.js` but application-agnostic.

### Bridge.purs FFI

PureScript code uses two functions from `Bridge.purs`:

- `dispatchPsEvent :: Json -> Effect Unit` — fires `__ps_event__` CustomEvent
- `subscribeQtCommands :: (Json -> Effect Unit) -> Effect (Effect Unit)` — listens for `__qt_command__`, returns unsubscribe

### Halogen Subscription Pattern

Stages 2-4 wire bridge events into Halogen using `halogen-subscriptions`:

```purescript
Initialize -> do
  { emitter, listener } <- liftEffect HS.create
  _ <- liftEffect $ subscribeQtCommands \json ->
    HS.notify listener (ReceiveCommand json)
  void $ H.subscribe emitter
```

This is the same pattern documented in `hats-halogen-integration.md` and used in `CodeExplorer/type-explorer`.

## Dependencies

PureScript packages from the registry (see `spago.yaml`):

- `hylograph-layout` 0.1.0 — tree layout algorithms (Stage 4)
- `hylograph-graph` 0.1.0 — transitive dependency
- `halogen`, `halogen-subscriptions` — UI framework (Stages 2-4)
- `argonaut-core` — JSON encoding/decoding
- `web-dom`, `web-html`, `web-events`, `web-uievents` — DOM access (Stage 1)
- `tree-rose` — rose tree data structure for layout input

Python: just PySide6 (already in the repo's `pyproject.toml`).

## File Layout

```
purescript-bridge-demo/
├── spago.yaml                    # PureScript project config
├── ps_bridge.js                  # UserWorld bridge (QWebChannel ↔ CustomEvents)
├── ps_bridge.py                  # Python launcher (adapted from map_bridge.py)
├── src/
│   ├── Bridge.purs               # dispatchPsEvent / subscribeQtCommands
│   ├── Bridge.js                 # FFI implementation
│   ├── Stage1/Main.purs          # Vanilla DOM + web-uievents
│   ├── Stage2/Main.purs          # Halogen entry point
│   ├── Stage2/Component.purs     # Counter + toggle + bridge subscription
│   ├── Stage3/Main.purs          # Halogen entry point
│   ├── Stage3/Component.purs     # Typed commands/events + item list
│   ├── Stage4/Main.purs          # Halogen entry point
│   ├── Stage4/Component.purs     # Tree viz + highlight + bridge
│   └── Stage4/TreeData.purs      # Sample tree data
└── public/
    ├── stage1.html
    ├── stage2.html
    ├── stage3.html
    └── stage4.html
```
