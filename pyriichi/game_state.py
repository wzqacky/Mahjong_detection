"""
遊戲狀態管理 - GameState implementation

管理局數、風、點數等遊戲狀態。
"""

from typing import List, Optional

from pyriichi.enum_utils import TranslatableEnum
from pyriichi.rules_config import RulesetConfig
from pyriichi.tiles import Suit, Tile


class Wind(TranslatableEnum):
    """風"""

    EAST = ("e", "東", "東", "East")
    SOUTH = ("s", "南", "南", "South")
    WEST = ("w", "西", "西", "West")
    NORTH = ("n", "北", "北", "North")

    @property
    def tile(self) -> Tile:
        if self == Wind.EAST:
            return Tile(Suit.JIHAI, 1)
        elif self == Wind.SOUTH:
            return Tile(Suit.JIHAI, 2)
        elif self == Wind.WEST:
            return Tile(Suit.JIHAI, 3)
        elif self == Wind.NORTH:
            return Tile(Suit.JIHAI, 4)
        else:
            raise ValueError(f"Invalid wind: {self}")


class GameState:
    """遊戲狀態管理器"""

    def __init__(
        self,
        initial_scores: Optional[List[int]] = None,
        num_players: int = 4,
        ruleset: Optional[RulesetConfig] = None,
    ):
        """
        初始化遊戲狀態。

        Args:
            initial_scores (Optional[List[int]]): 初始點數列表（默認每人 25000）。
            num_players (int): 玩家數量。
            ruleset (Optional[RulesetConfig]): 規則配置（默認使用標準競技規則）。
        """
        if initial_scores is None:
            initial_scores = [25000] * num_players

        self._scores = initial_scores.copy()
        self._round_wind = Wind.EAST
        self._round_number = 1
        self._dealer = 0
        self._honba = 0
        self._riichi_sticks = 0
        self._num_players = num_players
        self._ruleset = ruleset if ruleset is not None else RulesetConfig.standard()

    @property
    def round_wind(self) -> Wind:
        return self._round_wind

    @property
    def round_number(self) -> int:
        return self._round_number

    @property
    def player_winds(self) -> List[Wind]:
        winds = [Wind.EAST, Wind.SOUTH, Wind.WEST, Wind.NORTH]
        return [
            winds[(i - self._dealer) % self._num_players]
            for i in range(self._num_players)
        ]

    @property
    def dealer(self) -> int:
        return self._dealer

    @property
    def honba(self) -> int:
        return self._honba

    @property
    def riichi_sticks(self) -> int:
        return self._riichi_sticks

    @property
    def scores(self) -> List[int]:
        return self._scores.copy()

    def set_round(self, round_wind: Wind, round_number: int) -> None:
        """
        設置局數。

        Args:
            round_wind (Wind): 場風。
            round_number (int): 局數。
        """
        self._round_wind = round_wind
        self._round_number = round_number

    def set_dealer(self, dealer: int) -> None:
        """
        設置莊家。

        Args:
            dealer (int): 莊家位置。

        Raises:
            ValueError: 如果位置無效。
        """
        if not (0 <= dealer < self._num_players):
            raise ValueError(f"莊家位置必須在 0-{self._num_players - 1} 之間")
        self._dealer = dealer

    def add_honba(self, count: int = 1) -> None:
        """
        增加本場數。

        Args:
            count (int): 增加的數量（默認 1）。
        """
        self._honba += count

    def reset_honba(self) -> None:
        """重置本場數為 0。"""
        self._honba = 0

    def add_riichi_stick(self) -> None:
        """增加供託棒（立直棒）。"""
        self._riichi_sticks += 1

    def clear_riichi_sticks(self) -> None:
        """清除供託棒。"""
        self._riichi_sticks = 0

    @property
    def ruleset(self) -> RulesetConfig:
        return self._ruleset

    def update_score(self, player: int, points: int) -> None:
        """
        更新玩家點數。

        Args:
            player (int): 玩家位置。
            points (int): 點數變動（正數增加，負數減少）。

        Raises:
            ValueError: 如果玩家位置無效。
        """
        if not (0 <= player < self._num_players):
            raise ValueError(f"玩家位置必須在 0-{self._num_players - 1} 之間")
        self._scores[player] += points

    def transfer_points(self, from_player: int, to_player: int, points: int) -> None:
        """
        轉移點數。

        Args:
            from_player (int): 支付點數的玩家。
            to_player (int): 接收點數的玩家。
            points (int): 轉移的點數。
        """
        self.update_score(from_player, -points)
        self.update_score(to_player, points)

    def next_round(self) -> bool:
        """
        進入下一局。

        Returns:
            bool: 是否還有下一局（遊戲是否結束）。
        """
        # 西入後的突然死亡（Sudden Death）規則
        # 如果在西場，且有人達到目標分數（通常是30000），遊戲結束
        if self._round_wind == Wind.WEST:
            max_score = max(self._scores)
            if max_score >= self.ruleset.return_score:
                return False

        self._round_number += 1

        # 如果完成了 4 局，進入下一風
        if self._round_number > 4:
            if self._round_wind == Wind.EAST:
                self._round_wind = Wind.SOUTH
                self._round_number = 1
            elif self._round_wind == Wind.SOUTH:
                max_score = max(self._scores)
                if (
                    self.ruleset.west_round_extension
                    and max_score < self.ruleset.return_score
                ):
                    self._round_wind = Wind.WEST
                    self._round_number = 1
                else:
                    # 達到目標分數或未啟用西入，遊戲結束
                    return False
            elif self._round_wind == Wind.WEST:
                # 西場結束（強制結束）
                return False

        return True

    def next_dealer(self, dealer_won: bool) -> None:
        """
        下一局莊家。

        Args:
            dealer_won (bool): 莊家是否獲勝。
        """
        if not dealer_won:
            self._dealer = (self._dealer + 1) % self._num_players
            self.reset_honba()
        else:
            self.add_honba()
