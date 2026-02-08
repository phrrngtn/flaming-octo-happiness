-- | Sample tree data for Stage 4 demo
module Stage4.TreeData where

import Prelude

import Data.List (List(..), fromFoldable)
import Data.Tree (Tree, mkTree)

-- | Node record compatible with hylograph-layout tree algorithm
type TreeNode =
  { name :: String
  , path :: String
  , value :: Number
  , x :: Number
  , y :: Number
  , depth :: Int
  , height :: Int
  }

-- | A sample hierarchy representing a small project structure
sampleTree :: Tree TreeNode
sampleTree =
  mkTree (node "Project" "Project") $ fromFoldable
    [ mkTree (node "src" "Project.src") $ fromFoldable
        [ mkTree (node "Main" "Project.src.Main") $ fromFoldable
            [ leaf "App" "Project.src.Main.App"
            , leaf "Router" "Project.src.Main.Router"
            ]
        , mkTree (node "Utils" "Project.src.Utils") $ fromFoldable
            [ leaf "HTTP" "Project.src.Utils.HTTP"
            , leaf "JSON" "Project.src.Utils.JSON"
            , leaf "DOM" "Project.src.Utils.DOM"
            ]
        , mkTree (node "Components" "Project.src.Components") $ fromFoldable
            [ leaf "Button" "Project.src.Components.Button"
            , leaf "Card" "Project.src.Components.Card"
            , leaf "Modal" "Project.src.Components.Modal"
            , leaf "Table" "Project.src.Components.Table"
            ]
        ]
    , mkTree (node "test" "Project.test") $ fromFoldable
        [ leaf "MainSpec" "Project.test.MainSpec"
        , leaf "UtilsSpec" "Project.test.UtilsSpec"
        ]
    , mkTree (node "docs" "Project.docs") $ fromFoldable
        [ leaf "README" "Project.docs.README"
        , leaf "API" "Project.docs.API"
        ]
    ]

node :: String -> String -> TreeNode
node name path =
  { name, path, value: 0.0, x: 0.0, y: 0.0, depth: 0, height: 0 }

leaf :: String -> String -> Tree TreeNode
leaf name path = mkTree (node name path) Nil
