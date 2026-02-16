"""
PyRiichi - Python 日本麻將引擎

日本麻將（立直麻將）規則引擎的完整實作。
"""

__version__ = "0.1.0"

# 核心類別
from pyriichi.game_state import GameState, Wind
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import (
    ActionResult,
    GameAction,
    GamePhase,
    RuleEngine,
    RyuukyokuResult,
    RyuukyokuType,
    WinResult,
)
from pyriichi.rules_config import RulesetConfig
from pyriichi.scoring import ScoreCalculator, ScoreResult
from pyriichi.tiles import Suit, Tile, TileSet

# 便利函數
from pyriichi.utils import format_tiles, is_winning_hand, parse_tiles
from pyriichi.yaku import Yaku, YakuChecker, YakuResult

__all__ = [
    # 核心類別
    "Tile",
    "Suit",
    "TileSet",
    "Hand",
    "Meld",
    "MeldType",
    "GameState",
    "Wind",
    "RuleEngine",
    "GameAction",
    "GamePhase",
    "ActionResult",
    "WinResult",
    "RyuukyokuResult",
    "RyuukyokuType",
    "YakuChecker",
    "YakuResult",
    "Yaku",
    "ScoreCalculator",
    "ScoreResult",
    "RulesetConfig",
    # 工具函數
    "parse_tiles",
    "format_tiles",
    "is_winning_hand",
]
