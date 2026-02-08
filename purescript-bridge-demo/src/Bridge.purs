-- | Shared CustomEvent helpers for PureScript ↔ Qt WebEngine bridge.
-- |
-- | PS code dispatches `__ps_event__` (picked up by UserWorld bridge → Python)
-- | and listens for `__qt_command__` (dispatched by UserWorld bridge from Python).
module Bridge
  ( dispatchPsEvent
  , subscribeQtCommands
  ) where

import Prelude

import Data.Argonaut.Core (Json)
import Effect (Effect)

-- | Dispatch a `__ps_event__` CustomEvent on document with the given JSON detail.
-- | The UserWorld bridge picks this up and forwards to Python via QWebChannel.
foreign import dispatchPsEvent :: Json -> Effect Unit

-- | Listen for `__qt_command__` CustomEvents dispatched by the UserWorld bridge.
-- | Returns an unsubscribe effect.
foreign import subscribeQtCommands :: (Json -> Effect Unit) -> Effect (Effect Unit)
