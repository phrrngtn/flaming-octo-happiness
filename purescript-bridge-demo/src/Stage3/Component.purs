-- | Stage 3: Bidirectional command/event component
-- |
-- | Typed commands and events with a colored item list.
-- | Python can send: set-color, add-item, remove-item, ping
-- | PS sends: item-clicked, counter-changed, pong
module Stage3.Component where

import Prelude

import Bridge (dispatchPsEvent, subscribeQtCommands)
import Data.Argonaut.Core (Json, stringify)
import Data.Argonaut.Core as J
import Data.Array as Array
import Data.Int (toNumber, floor) as Int
import Data.Maybe (Maybe(..), fromMaybe)
import Data.String (toLower)
import Data.Tuple (Tuple(..))
import Effect.Class (class MonadEffect, liftEffect)
import Effect.Console (log)
import Foreign.Object as FO
import Halogen as H
import Halogen.HTML as HH
import Halogen.HTML.Events as HE
import Halogen.HTML.Properties as HP
import Halogen.Subscription as HS

type Item =
  { id :: Int
  , label :: String
  , color :: String
  }

type State =
  { items :: Array Item
  , nextId :: Int
  , accentColor :: String
  , counter :: Int
  , status :: String
  , lastEvent :: String
  }

data Action
  = Initialize
  | ClickItem Item
  | IncrementCounter
  | DecrementCounter
  | AddDefaultItem
  | ReceiveCommand Json

component :: forall q i o m. MonadEffect m => H.Component q i o m
component = H.mkComponent
  { initialState: \_ ->
      { items:
          [ { id: 1, label: "Apple", color: "#c23b22" }
          , { id: 2, label: "Forest", color: "#2d5a27" }
          , { id: 3, label: "Ocean", color: "#1e3a5f" }
          ]
      , nextId: 4
      , accentColor: "#0d6e6e"
      , counter: 0
      , status: "Waiting..."
      , lastEvent: ""
      }
  , render
  , eval: H.mkEval H.defaultEval
      { handleAction = handleAction
      , initialize = Just Initialize
      }
  }

render :: forall m. State -> H.ComponentHTML Action () m
render state =
  HH.div
    [ HP.style "font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px;" ]
    [ HH.h1
        [ HP.style ("color: " <> state.accentColor <> "; font-size: 1.5rem;") ]
        [ HH.text "Stage 3: Bidirectional Control" ]
    , HH.p_
        [ HH.text "Typed commands & events. Click items, Python responds." ]

    -- Counter row
    , HH.div
        [ HP.style "display: flex; align-items: center; gap: 12px; margin: 16px 0;" ]
        [ HH.button [ HE.onClick \_ -> DecrementCounter, HP.style (btnStyle state.accentColor) ] [ HH.text "-" ]
        , HH.span [ HP.style "font-size: 1.5rem; min-width: 40px; text-align: center;" ] [ HH.text (show state.counter) ]
        , HH.button [ HE.onClick \_ -> IncrementCounter, HP.style (btnStyle state.accentColor) ] [ HH.text "+" ]
        , HH.button [ HE.onClick \_ -> AddDefaultItem, HP.style (btnStyle "#666") ] [ HH.text "+ Item" ]
        ]

    -- Items list
    , HH.div [ HP.style "margin: 16px 0;" ] $
        state.items <#> \item ->
          HH.div
            [ HE.onClick \_ -> ClickItem item
            , HP.style $ "padding: 10px 16px; margin: 4px 0; background: " <> item.color
                <> "; color: white; border-radius: 6px; cursor: pointer; transition: opacity 0.2s;"
            ]
            [ HH.text $ item.label <> " (id: " <> show item.id <> ")" ]

    -- Status area
    , HH.div [ HP.style "font-size: 0.85rem; color: #888; margin-top: 16px;" ] [ HH.text "Status:" ]
    , HH.div
        [ HP.style "padding: 12px; background: white; border: 1px solid #ddd; border-radius: 6px; color: #555;" ]
        [ HH.text state.status ]

    -- Last event
    , HH.div [ HP.style "font-size: 0.85rem; color: #888; margin-top: 12px;" ] [ HH.text "Last event sent:" ]
    , HH.div
        [ HP.style "padding: 8px 12px; background: #eee; border-radius: 4px; font-family: monospace; font-size: 0.85rem;" ]
        [ HH.text (if state.lastEvent == "" then "(none)" else state.lastEvent) ]
    ]

btnStyle :: String -> String
btnStyle bg = "padding: 8px 16px; border: none; border-radius: 6px; background: " <> bg <> "; color: white; font-size: 1rem; cursor: pointer;"

handleAction :: forall o m. MonadEffect m => Action -> H.HalogenM State Action () o m Unit
handleAction = case _ of
  Initialize -> do
    { emitter, listener } <- liftEffect HS.create
    _ <- liftEffect $ subscribeQtCommands \json ->
      HS.notify listener (ReceiveCommand json)
    void $ H.subscribe emitter
    liftEffect $ log "Stage 3 initialized"

  ClickItem item -> do
    let evt = mkJson
          [ Tuple "type" (J.fromString "item-clicked")
          , Tuple "id" (J.fromNumber (Int.toNumber item.id))
          , Tuple "label" (J.fromString item.label)
          ]
    liftEffect $ dispatchPsEvent evt
    H.modify_ \s -> s { lastEvent = stringify evt }

  IncrementCounter -> do
    H.modify_ \s -> s { counter = s.counter + 1 }
    st <- H.get
    let evt = mkJson
          [ Tuple "type" (J.fromString "counter-changed")
          , Tuple "value" (J.fromNumber (Int.toNumber st.counter))
          ]
    liftEffect $ dispatchPsEvent evt
    H.modify_ \s -> s { lastEvent = stringify evt }

  DecrementCounter -> do
    H.modify_ \s -> s { counter = s.counter - 1 }
    st <- H.get
    let evt = mkJson
          [ Tuple "type" (J.fromString "counter-changed")
          , Tuple "value" (J.fromNumber (Int.toNumber st.counter))
          ]
    liftEffect $ dispatchPsEvent evt
    H.modify_ \s -> s { lastEvent = stringify evt }

  AddDefaultItem -> do
    st <- H.get
    let newItem = { id: st.nextId, label: "Item " <> show st.nextId, color: st.accentColor }
    H.modify_ \s -> s { items = s.items <> [newItem], nextId = s.nextId + 1 }

  ReceiveCommand json -> do
    liftEffect $ log $ "Command: " <> stringify json
    let obj = J.toObject json
    case obj of
      Nothing -> pure unit
      Just o -> do
        let cmd = FO.lookup "command" o >>= J.toString
        case cmd of
          Just "set-status" -> do
            let txt = fromMaybe "" $ FO.lookup "text" o >>= J.toString
            H.modify_ \s -> s { status = txt }

          Just "set-color" -> do
            let color = fromMaybe "#0d6e6e" $ FO.lookup "color" o >>= J.toString
            H.modify_ \s -> s { accentColor = toLower color }

          Just "add-item" -> do
            let label = fromMaybe "New" $ FO.lookup "label" o >>= J.toString
            let color = fromMaybe "#666" $ FO.lookup "color" o >>= J.toString
            st <- H.get
            let newItem = { id: st.nextId, label: label, color: color }
            H.modify_ \s -> s { items = s.items <> [newItem], nextId = s.nextId + 1 }

          Just "remove-item" -> do
            let mid = FO.lookup "id" o >>= J.toNumber
            case mid of
              Just n -> H.modify_ \s -> s { items = Array.filter (\i -> i.id /= Int.floor n) s.items }
              Nothing -> pure unit

          Just "ping" -> do
            let pong = mkJson [ Tuple "type" (J.fromString "pong") ]
            liftEffect $ dispatchPsEvent pong
            H.modify_ \s -> s { lastEvent = stringify pong, status = "Pong sent!" }

          _ -> liftEffect $ log $ "Unknown command: " <> stringify json

-- Helpers
mkJson :: Array (Tuple String Json) -> Json
mkJson pairs = J.fromObject (FO.fromFoldable pairs)
