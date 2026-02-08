-- | Stage 1: Vanilla PureScript + web-uievents
-- |
-- | Minimal proof that PureScript code can talk to Python via the bridge.
-- | Renders colored buttons and a status area using web-dom.
-- | Click handlers dispatch __ps_event__, listens for __qt_command__.
module Stage1.Main where

import Prelude

import Bridge (dispatchPsEvent, subscribeQtCommands)
import Data.Argonaut.Core (Json, stringify)
import Data.Argonaut.Core as J
import Data.Maybe (Maybe(..))
import Data.Tuple (Tuple(..))
import Effect (Effect)
import Effect.Console (log)
import Foreign.Object as FO
import Web.DOM.Element as Elem
import Web.DOM.Node (setTextContent)
import Web.DOM.NonElementParentNode (getElementById)
import Web.Event.Event (Event)
import Web.Event.EventTarget (addEventListener, eventListener)
import Web.HTML (window)
import Web.HTML.HTMLDocument (toNonElementParentNode)
import Web.HTML.Window (document)
import Web.UIEvent.MouseEvent.EventTypes (click) as MouseEventType

main :: Effect Unit
main = do
  log "Stage 1: Vanilla PureScript bridge demo"

  w <- window
  htmlDoc <- document w
  let doc = toNonElementParentNode htmlDoc

  -- Get elements
  mStatus <- getElementById "status" doc
  mRed <- getElementById "btn-red" doc
  mGreen <- getElementById "btn-green" doc
  mBlue <- getElementById "btn-blue" doc

  -- Wire up click handlers
  case mRed of
    Just el -> addClickHandler el "red"
    Nothing -> log "btn-red not found"

  case mGreen of
    Just el -> addClickHandler el "green"
    Nothing -> log "btn-green not found"

  case mBlue of
    Just el -> addClickHandler el "blue"
    Nothing -> log "btn-blue not found"

  -- Subscribe to commands from Python
  _ <- subscribeQtCommands \json -> do
    log $ "Received command: " <> stringify json
    case mStatus of
      Just statusEl -> handleCommand statusEl json
      Nothing -> log "status element not found"

  log "Stage 1 initialized"

addClickHandler :: Elem.Element -> String -> Effect Unit
addClickHandler el color = do
  listener <- eventListener (handleClick color)
  addEventListener MouseEventType.click listener false (Elem.toEventTarget el)

handleClick :: String -> Event -> Effect Unit
handleClick color _ = do
  log $ "Click: " <> color
  dispatchPsEvent $ mkJson
    [ Tuple "type" (J.fromString "click")
    , Tuple "color" (J.fromString color)
    ]

handleCommand :: Elem.Element -> Json -> Effect Unit
handleCommand statusEl json = do
  let obj = J.toObject json
  case obj of
    Nothing -> log "Command is not a JSON object"
    Just o -> do
      let cmd = FO.lookup "command" o >>= J.toString
      case cmd of
        Just "set-status" -> do
          let txt = FO.lookup "text" o >>= J.toString
          case txt of
            Just t -> setTextContent t (Elem.toNode statusEl)
            Nothing -> pure unit
        _ -> log $ "Unknown command: " <> stringify json

-- | Helper to build a JSON object from key-value pairs
mkJson :: Array (Tuple String Json) -> Json
mkJson pairs = J.fromObject (FO.fromFoldable pairs)
