-- | Stage 2: Halogen component with counter, toggle, and bridge subscription
module Stage2.Component where

import Prelude

import Bridge (dispatchPsEvent, subscribeQtCommands)
import Data.Argonaut.Core (Json, stringify)
import Data.Argonaut.Core as J
import Data.Int (toNumber, floor) as Int
import Data.Maybe (Maybe(..))
import Data.Tuple (Tuple(..))
import Effect.Class (class MonadEffect, liftEffect)
import Effect.Console (log)
import Foreign.Object as FO
import Halogen as H
import Halogen.HTML as HH
import Halogen.HTML.Events as HE
import Halogen.HTML.Properties as HP
import Halogen.Subscription as HS

type State =
  { counter :: Int
  , toggled :: Boolean
  , status :: String
  }

data Action
  = Initialize
  | Increment
  | Decrement
  | Toggle
  | ReceiveCommand Json

component :: forall q i o m. MonadEffect m => H.Component q i o m
component = H.mkComponent
  { initialState: \_ ->
      { counter: 0
      , toggled: false
      , status: "Waiting for commands..."
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
        [ HP.style "color: #2d5a27; font-size: 1.5rem;" ]
        [ HH.text "Stage 2: Halogen Bridge" ]
    , HH.p_
        [ HH.text "Halogen manages state. Events → Python, commands → Halogen." ]

    -- Counter
    , HH.div
        [ HP.style "display: flex; align-items: center; gap: 12px; margin: 20px 0;" ]
        [ HH.button
            [ HE.onClick \_ -> Decrement
            , HP.style btnStyle
            ]
            [ HH.text "-" ]
        , HH.span
            [ HP.style "font-size: 2rem; min-width: 60px; text-align: center;" ]
            [ HH.text (show state.counter) ]
        , HH.button
            [ HE.onClick \_ -> Increment
            , HP.style btnStyle
            ]
            [ HH.text "+" ]
        ]

    -- Toggle
    , HH.div
        [ HP.style "margin: 20px 0;" ]
        [ HH.button
            [ HE.onClick \_ -> Toggle
            , HP.style if state.toggled then toggleOnStyle else toggleOffStyle
            ]
            [ HH.text if state.toggled then "ON" else "OFF" ]
        ]

    -- Status
    , HH.div
        [ HP.style "font-size: 0.85rem; color: #888; margin-bottom: 4px;" ]
        [ HH.text "Status (updated by Python commands):" ]
    , HH.div
        [ HP.style "padding: 16px; background: white; border: 1px solid #ddd; border-radius: 6px; color: #555;" ]
        [ HH.text state.status ]
    ]

btnStyle :: String
btnStyle = "padding: 8px 20px; border: none; border-radius: 6px; background: #2d5a27; color: white; font-size: 1.2rem; cursor: pointer;"

toggleOnStyle :: String
toggleOnStyle = "padding: 10px 24px; border: none; border-radius: 6px; background: #0d6e6e; color: white; font-size: 1rem; cursor: pointer;"

toggleOffStyle :: String
toggleOffStyle = "padding: 10px 24px; border: none; border-radius: 6px; background: #999; color: white; font-size: 1rem; cursor: pointer;"

handleAction :: forall o m. MonadEffect m => Action -> H.HalogenM State Action () o m Unit
handleAction = case _ of
  Initialize -> do
    { emitter, listener } <- liftEffect HS.create
    _ <- liftEffect $ subscribeQtCommands \json ->
      HS.notify listener (ReceiveCommand json)
    void $ H.subscribe emitter
    liftEffect $ log "Stage 2 initialized with bridge subscription"

  Increment -> do
    H.modify_ \s -> s { counter = s.counter + 1 }
    st <- H.get
    liftEffect $ dispatchPsEvent $ mkJson
      [ Tuple "type" (J.fromString "counter")
      , Tuple "value" (J.fromNumber (Int.toNumber st.counter))
      ]

  Decrement -> do
    H.modify_ \s -> s { counter = s.counter - 1 }
    st <- H.get
    liftEffect $ dispatchPsEvent $ mkJson
      [ Tuple "type" (J.fromString "counter")
      , Tuple "value" (J.fromNumber (Int.toNumber st.counter))
      ]

  Toggle -> do
    H.modify_ \s -> s { toggled = not s.toggled }
    st <- H.get
    liftEffect $ dispatchPsEvent $ mkJson
      [ Tuple "type" (J.fromString "toggle")
      , Tuple "value" (J.fromBoolean st.toggled)
      ]

  ReceiveCommand json -> do
    liftEffect $ log $ "Received command: " <> stringify json
    let obj = J.toObject json
    case obj of
      Nothing -> pure unit
      Just o -> do
        let cmd = FO.lookup "command" o >>= J.toString
        case cmd of
          Just "set-status" -> do
            let txt = FO.lookup "text" o >>= J.toString
            case txt of
              Just t -> H.modify_ \s -> s { status = t }
              Nothing -> pure unit
          Just "set-counter" -> do
            let val = FO.lookup "value" o >>= J.toNumber
            case val of
              Just n -> H.modify_ \s -> s { counter = Int.floor n }
              Nothing -> pure unit
          Just "set-toggle" -> do
            let val = FO.lookup "value" o >>= J.toBoolean
            case val of
              Just b -> H.modify_ \s -> s { toggled = b }
              Nothing -> pure unit
          _ -> liftEffect $ log $ "Unknown command: " <> stringify json

-- Helpers
mkJson :: Array (Tuple String Json) -> Json
mkJson pairs = J.fromObject (FO.fromFoldable pairs)
