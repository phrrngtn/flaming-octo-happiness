-- | Stage 4: Hylograph tree visualization with bidirectional bridge
-- |
-- | Uses hylograph-layout for tree layout computation.
-- | Renders as pure Halogen SVG (no D3 CDN).
-- | Node hover/click dispatches events to Python.
-- | Python can send highlight/set-status commands back.
module Stage4.Component where

import Prelude

import Bridge (dispatchPsEvent, subscribeQtCommands)
import Control.Comonad.Cofree (head, tail)
import Data.Argonaut.Core (Json, stringify)
import Data.Argonaut.Core as J
import Data.Array as Array
import Data.Int (toNumber) as Int
import Data.Maybe (Maybe(..))
import Data.String (contains)
import Data.String.Pattern (Pattern(..))
import Data.Tree (Tree)
import Data.Tuple (Tuple(..))
import DataViz.Layout.Hierarchy.Link as Link
import DataViz.Layout.Hierarchy.Tree as TreeLayout
import Effect.Class (class MonadEffect, liftEffect)
import Effect.Console (log)
import Foreign.Object as FO
import Halogen as H
import Halogen.HTML as HH
import Halogen.HTML.Events as HE
import Halogen.HTML.Properties as HP
import Halogen.Subscription as HS
import Stage4.TreeData (TreeNode, sampleTree)

-- SVG namespace helpers (same pattern as Gallery/Render.purs)
svgNS :: String
svgNS = "http://www.w3.org/2000/svg"

svg :: forall r w i. Array (HH.IProp r i) -> Array (HH.HTML w i) -> HH.HTML w i
svg = HH.elementNS (HH.Namespace svgNS) (HH.ElemName "svg")

g :: forall r w i. Array (HH.IProp r i) -> Array (HH.HTML w i) -> HH.HTML w i
g = HH.elementNS (HH.Namespace svgNS) (HH.ElemName "g")

circle :: forall r w i. Array (HH.IProp r i) -> HH.HTML w i
circle props = HH.elementNS (HH.Namespace svgNS) (HH.ElemName "circle") props []

path :: forall r w i. Array (HH.IProp r i) -> HH.HTML w i
path props = HH.elementNS (HH.Namespace svgNS) (HH.ElemName "path") props []

text :: forall r w i. Array (HH.IProp r i) -> Array (HH.HTML w i) -> HH.HTML w i
text = HH.elementNS (HH.Namespace svgNS) (HH.ElemName "text")

-- Constants
colorForestGreen :: String
colorForestGreen = "#2d5a27"

colorHighlight :: String
colorHighlight = "#c9a227"

type State =
  { hovered :: Maybe String  -- path of hovered node
  , status :: String
  }

data Action
  = Initialize
  | HoverNode String
  | LeaveNode
  | ClickNode { name :: String, path :: String }
  | ReceiveCommand Json

component :: forall q i o m. MonadEffect m => H.Component q i o m
component = H.mkComponent
  { initialState: \_ ->
      { hovered: Nothing
      , status: "Hover or click nodes. Python can send highlight commands."
      }
  , render
  , eval: H.mkEval H.defaultEval
      { handleAction = handleAction
      , initialize = Just Initialize
      }
  }

render :: forall m. State -> H.ComponentHTML Action () m
render state =
  let
    config = TreeLayout.defaultTreeConfig
      { size = { width: 500.0, height: 400.0 }
      , minSeparation = 1.0
      }
    laidOut = TreeLayout.tree config sampleTree
  in
    HH.div
      [ HP.style "font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 800px; margin: 20px auto; padding: 0 20px;" ]
      [ HH.h1
          [ HP.style "color: #2d5a27; font-size: 1.5rem;" ]
          [ HH.text "Stage 4: Hylograph Tree Visualization" ]
      , HH.p_
          [ HH.text "Pure PureScript layout + Halogen SVG. No D3 CDN." ]
      , svg
          [ HP.attr (HH.AttrName "viewBox") "0 0 600 500"
          , HP.attr (HH.AttrName "preserveAspectRatio") "xMidYMid meet"
          , HP.attr (HH.AttrName "width") "100%"
          , HP.attr (HH.AttrName "height") "450"
          ]
          [ g [ HP.attr (HH.AttrName "transform") "translate(50, 30)" ]
              ( renderVerticalLinks laidOut state.hovered
                <> renderVerticalNodes laidOut state.hovered
              )
          ]
      , HH.div
          [ HP.style "margin-top: 12px; padding: 12px; background: white; border: 1px solid #ddd; border-radius: 6px; color: #555; font-size: 0.9rem;" ]
          [ HH.text state.status ]
      ]

-- | Render bezier links for vertical (top-down) tree layout
renderVerticalLinks
  :: forall w
   . Tree TreeNode
  -> Maybe String
  -> Array (HH.HTML w Action)
renderVerticalLinks tree hovered =
  let
    node = head tree
    children = tail tree
  in
    Array.fromFoldable children >>= \child ->
      let
        childNode = head child
        pathD = Link.linkBezierVertical node.x node.y childNode.x childNode.y
        linkClass = highlightClass hovered childNode.path
      in
        [ path
            [ HP.attr (HH.AttrName "d") pathD
            , HP.attr (HH.AttrName "fill") "none"
            , HP.attr (HH.AttrName "stroke") colorForestGreen
            , HP.attr (HH.AttrName "stroke-width") "1.5"
            , HP.attr (HH.AttrName "opacity") "0.6"
            , HP.attr (HH.AttrName "class") ("link " <> linkClass)
            ]
        ] <> renderVerticalLinks child hovered

-- | Render nodes for vertical tree layout with hover/click events
renderVerticalNodes
  :: forall w
   . Tree TreeNode
  -> Maybe String
  -> Array (HH.HTML w Action)
renderVerticalNodes tree hovered =
  let
    node = head tree
    children = tail tree
    radius = max 3.0 (7.0 - Int.toNumber node.depth * 1.0)
    nodeClass = highlightClass hovered node.path
    fillColor = case hovered of
      Just h | h == node.path -> colorHighlight
      _ -> colorForestGreen
  in
    [ circle
        [ HP.attr (HH.AttrName "cx") (show node.x)
        , HP.attr (HH.AttrName "cy") (show node.y)
        , HP.attr (HH.AttrName "r") (show radius)
        , HP.attr (HH.AttrName "fill") fillColor
        , HP.attr (HH.AttrName "class") ("node " <> nodeClass)
        , HE.onMouseEnter \_ -> HoverNode node.path
        , HE.onMouseLeave \_ -> LeaveNode
        , HE.onClick \_ -> ClickNode { name: node.name, path: node.path }
        ]
    , text
        [ HP.attr (HH.AttrName "x") (show node.x)
        , HP.attr (HH.AttrName "y") (show (node.y - radius - 3.0))
        , HP.attr (HH.AttrName "text-anchor") "middle"
        , HP.attr (HH.AttrName "font-size") "10"
        , HP.attr (HH.AttrName "fill") "#333"
        , HP.attr (HH.AttrName "class") nodeClass
        ]
        [ HH.text node.name ]
    ] <> (Array.fromFoldable children >>= \child -> renderVerticalNodes child hovered)

-- Highlight logic (same as Gallery/Render.purs)
isRelated :: String -> String -> Boolean
isRelated a b =
  contains (Pattern (a <> ".")) b ||
  contains (Pattern (b <> ".")) a

highlightClass :: Maybe String -> String -> String
highlightClass Nothing _ = ""
highlightClass (Just hoveredPath) nodePath
  | hoveredPath == nodePath = "highlight-primary"
  | isRelated hoveredPath nodePath = "highlight-related"
  | otherwise = "highlight-dimmed"

handleAction :: forall o m. MonadEffect m => Action -> H.HalogenM State Action () o m Unit
handleAction = case _ of
  Initialize -> do
    { emitter, listener } <- liftEffect HS.create
    _ <- liftEffect $ subscribeQtCommands \json ->
      HS.notify listener (ReceiveCommand json)
    void $ H.subscribe emitter
    liftEffect $ log "Stage 4 initialized"

  HoverNode nodePath -> do
    H.modify_ \s -> s { hovered = Just nodePath }
    liftEffect $ dispatchPsEvent $ mkJson
      [ Tuple "type" (J.fromString "node-hover")
      , Tuple "path" (J.fromString nodePath)
      ]

  LeaveNode -> do
    H.modify_ \s -> s { hovered = Nothing }
    liftEffect $ dispatchPsEvent $ mkJson
      [ Tuple "type" (J.fromString "node-leave")
      ]

  ClickNode { name: nodeName, path: nodePath } -> do
    liftEffect $ dispatchPsEvent $ mkJson
      [ Tuple "type" (J.fromString "node-click")
      , Tuple "name" (J.fromString nodeName)
      , Tuple "path" (J.fromString nodePath)
      ]

  ReceiveCommand json -> do
    liftEffect $ log $ "Command: " <> stringify json
    let obj = J.toObject json
    case obj of
      Nothing -> pure unit
      Just o -> do
        let cmd = FO.lookup "command" o >>= J.toString
        case cmd of
          Just "highlight" -> do
            let mpath = FO.lookup "path" o >>= J.toString
            H.modify_ \s -> s { hovered = mpath }

          Just "clear-highlight" ->
            H.modify_ \s -> s { hovered = Nothing }

          Just "set-status" -> do
            let txt = FO.lookup "text" o >>= J.toString
            case txt of
              Just t -> H.modify_ \s -> s { status = t }
              Nothing -> pure unit

          _ -> liftEffect $ log $ "Unknown command: " <> stringify json

-- Helpers
mkJson :: Array (Tuple String Json) -> Json
mkJson pairs = J.fromObject (FO.fromFoldable pairs)
