"""
牌組系統 - Tile and TileSet implementation

提供牌的表示、牌組管理和發牌功能。
"""

import itertools
import random
from typing import Dict, List, Optional

from pyriichi.enum_utils import TranslatableEnum


class Suit(TranslatableEnum):
    """花色"""

    MANZU = ("m", "萬子", "萬子", "Manzu")
    PINZU = ("p", "筒子", "筒子", "Pinzu")
    SOZU = ("s", "索子", "索子", "Souzu")
    JIHAI = ("z", "字牌", "字牌", "Honors")


class Tile:
    """單張麻將牌"""

    _NUMERAL_MAP: Dict[str, Dict[int, str]] = {
        "zh": {
            1: "一",
            2: "二",
            3: "三",
            4: "四",
            5: "五",
            6: "六",
            7: "七",
            8: "八",
            9: "九",
        },
        "ja": {
            1: "一",
            2: "二",
            3: "三",
            4: "四",
            5: "五",
            6: "六",
            7: "七",
            8: "八",
            9: "九",
        },
        "en": {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9"},
    }

    _SUIT_SUFFIX_MAP: Dict[str, Dict[Suit, str]] = {
        "zh": {Suit.MANZU: "萬", Suit.PINZU: "筒", Suit.SOZU: "索"},
        "ja": {Suit.MANZU: "萬", Suit.PINZU: "筒", Suit.SOZU: "索"},
        "en": {Suit.MANZU: "Man", Suit.PINZU: "Pin", Suit.SOZU: "Sou"},
    }

    _HONOR_NAME_MAP: Dict[str, Dict[int, str]] = {
        "zh": {1: "東", 2: "南", 3: "西", 4: "北", 5: "白", 6: "發", 7: "中"},
        "ja": {1: "東", 2: "南", 3: "西", 4: "北", 5: "白", 6: "發", 7: "中"},
        "en": {
            1: "East",
            2: "South",
            3: "West",
            4: "North",
            5: "White",
            6: "Green",
            7: "Red",
        },
    }

    _RED_PREFIX_MAP: Dict[str, str] = {"zh": "赤", "ja": "赤", "en": "Red "}

    def __init__(self, suit: Suit, rank: int, is_red: bool = False):
        """
        初始化一張牌。

        Args:
            suit (Suit): 花色。
            rank (int): 數字（1-9 對數牌，1-7 對字牌）。
            is_red (bool): 是否為紅寶牌（默認 False）。

        Raises:
            ValueError: 如果 rank 超出範圍。
        """
        if suit == Suit.JIHAI:
            if not (1 <= rank <= 7):
                raise ValueError(f"字牌 rank 必須在 1-7 之間，得到 {rank}")
        elif not (1 <= rank <= 9):
            raise ValueError(f"數牌 rank 必須在 1-9 之間，得到 {rank}")

        self._suit = suit
        self._rank = rank
        self._is_red = is_red

    @property
    def suit(self) -> Suit:
        return self._suit

    @property
    def rank(self) -> int:
        return self._rank

    @property
    def is_red(self) -> bool:
        return self._is_red

    @property
    def is_honor(self) -> bool:
        return self._suit == Suit.JIHAI

    @property
    def is_terminal(self) -> bool:
        return False if self._suit == Suit.JIHAI else self._rank in [1, 9]

    @property
    def is_simple(self) -> bool:
        return False if self._suit == Suit.JIHAI else 2 <= self._rank <= 8

    def __eq__(self, other) -> bool:
        """
        比較兩張牌是否相同（不考慮紅寶牌）。

        Args:
            other (Any): 要比較的對象。

        Returns:
            bool: 如果花色和數字相同則返回 True。
        """
        if not isinstance(other, Tile):
            return False
        return self._suit == other._suit and self._rank == other._rank

    def __hash__(self) -> int:
        return hash((self._suit, self._rank))

    def __lt__(self, other) -> bool:
        if not isinstance(other, Tile):
            return NotImplemented
        if self._suit.value != other._suit.value:
            return self._suit.value < other._suit.value
        return self._rank < other._rank

    def __str__(self) -> str:
        """
        獲取牌的字符串表示（例如：1m, 5p, r5m 表示紅寶牌）。

        Returns:
            str: 牌的字符串表示。
        """
        suit_map = {
            Suit.MANZU: "m",
            Suit.PINZU: "p",
            Suit.SOZU: "s",
            Suit.JIHAI: "z",
        }
        if self._is_red:
            return f"r{self._rank}{suit_map[self._suit]}"
        return f"{self._rank}{suit_map[self._suit]}"

    def __repr__(self) -> str:
        return f"Tile({self._suit.name}, {self._rank}, red={self._is_red})"

    @property
    def is_yaochuu(self) -> bool:
        """
        判斷是否為幺九牌（1, 9, 字牌）。

        Returns:
            bool: 如果是幺九牌則返回 True。
        """
        if self._suit == Suit.JIHAI:
            return True
        return self._rank == 1 or self._rank == 9

    def _format_name(self, locale: str) -> str:
        if locale not in {"zh", "ja", "en"}:
            raise ValueError(f"Unsupported locale: {locale}")

        prefix = self._RED_PREFIX_MAP[locale] if self._is_red else ""

        if self._suit == Suit.JIHAI:
            return f"{prefix}{self._HONOR_NAME_MAP[locale][self._rank]}"

        numeral = self._NUMERAL_MAP[locale][self._rank]
        suffix = self._SUIT_SUFFIX_MAP[locale][self._suit]

        if locale == "en":
            return f"{prefix}{numeral} {suffix}".strip()

        return f"{prefix}{numeral}{suffix}"

    def get_name(self, locale: str = "zh") -> str:
        """
        獲取牌的本地化名稱。

        Args:
            locale (str): 語言代碼 ("zh", "ja", "en")。

        Returns:
            str: 本地化名稱。
        """
        return self._format_name(locale)


def create_tile(id: str, is_red: bool = False) -> Tile:
    """
    創建一張牌（便捷函數）。

    Args:
        id (str): the sequence obtained from YOLO prediction
        is_red (bool): 是否為紅寶牌。

    Returns:
        Tile: 創建的 Tile 對象。

    Raises:
        ValueError: 如果 suit 無效。
    """
    # TODO: Add suit for flowers (pyriichi default no flower, but this is required when expanding to other mahjong types)
    suit_map = {
        "C": Suit.MANZU,
        "D": Suit.PINZU,
        "B": Suit.SOZU,
        "W": Suit.JIHAI,
    }

    jihai_id_map = {
        "EW": 1,
        "SW": 2,
        "WW": 3,
        "NW": 4,
        "WD": 5,
        "GD": 6,
        "RD": 7,
    }
    suit = id[-1]
    rank = jihai_id_map[id] if id in jihai_id_map else int(id[0])

    if suit not in suit_map:
        print(f"無效的花色: {suit}")
    return Tile(suit_map[suit], rank, is_red)


class TileSet:
    """牌組管理器"""

    def __init__(self, tiles: Optional[List[Tile]] = None):
        """
        初始化牌組。

        Args:
            tiles (Optional[List[Tile]]): 初始牌列表（如果為 None，則創建標準 136 張牌）。
        """
        if tiles is None:
            tiles = self._create_standard_set()
        self._tiles = tiles.copy()
        self._wall = []
        self._dora_indicators = []

    @staticmethod
    def _create_standard_set() -> List[Tile]:
        tiles = []
        # 數牌：萬、筒、條各 36 張（1-9 各 4 張）
        for suit in [Suit.MANZU, Suit.PINZU, Suit.SOZU]:
            for rank in range(1, 10):
                if rank == 5:
                    tiles.extend(Tile(suit, rank) for _ in range(3))
                    tiles.append(Tile(suit, rank, is_red=True))
                else:
                    tiles.extend(Tile(suit, rank) for _ in range(4))
        # 字牌：風牌 16 張（東南西北各 4 張），三元牌 12 張（白發中各 4 張）
        tiles.extend(
            Tile(Suit.JIHAI, rank)
            for rank, _ in itertools.product(range(1, 8), range(4))
        )
        return tiles

    def shuffle(self) -> None:
        random.shuffle(self._tiles)
        # 初始化王牌區（最後 14 張）
        self._wall = self._tiles[-14:]
        self._tiles = self._tiles[:-14]

        self._rinshan_tiles = self._wall[:4]

        self._dora_indicators = self._wall[4:8]

        self._ura_dora_indicators = self._wall[8:12]

    def deal(self, num_players: int = 4) -> List[List[Tile]]:
        """
        發牌。

        Args:
            num_players (int): 玩家數量（默認 4）。

        Returns:
            List[List[Tile]]: 每個玩家的手牌列表（13 張），莊家為 14 張。
        """
        hands = [[] for _ in range(num_players)]

        for _, player in itertools.product(range(13), range(num_players)):
            if self._tiles:
                hands[player].append(self._tiles.pop(0))

        # 莊家多發 1 張（第 14 張）
        if self._tiles:
            hands[0].append(self._tiles.pop(0))

        for hand in hands:
            hand.sort()

        return hands

    def draw(self) -> Optional[Tile]:
        """
        從牌山頂端摸一張牌。

        Returns:
            Optional[Tile]: 摸到的牌，如果牌山為空則返回 None。
        """
        return self._tiles.pop(0) if self._tiles else None

    def draw_rinshan(self) -> Optional[Tile]:
        """
        從嶺上牌摸一張牌（用於槓後摸牌）。

        Returns:
            Optional[Tile]: 摸到的牌，如果嶺上牌為空則返回 None。
        """
        return self._rinshan_tiles.pop(0) if self._rinshan_tiles else None

    @property
    def remaining(self) -> int:
        return len(self._tiles)

    @property
    def wall_remaining(self) -> int:
        return len(self._wall)

    def is_exhausted(self) -> bool:
        return len(self._tiles) == 0

    def get_dora_indicators(self, count: Optional[int] = None) -> List[Tile]:
        """
        獲取寶牌指示牌。

        Args:
            count (Optional[int]): 指示牌數量（如果為 None，則依照嶺上牌數量推斷）。

        Returns:
            List[Tile]: 指示牌列表。

        Raises:
            ValueError: 如果指示牌不足。
        """
        if count is None:
            count = 5 - len(self._rinshan_tiles)
        if count > len(self._dora_indicators):
            raise ValueError(
                f"寶牌指示牌不足，需要 {count} 張，只有 {len(self._dora_indicators)} 張"
            )
        return self._dora_indicators[:count]

    def get_ura_dora_indicators(self, count: Optional[int] = None) -> List[Tile]:
        """
        獲取裡寶牌指示牌。

        Args:
            count (Optional[int]): 指示牌數量（如果為 None，則依照嶺上牌數量推斷）。

        Returns:
            List[Tile]: 指示牌列表。

        Raises:
            ValueError: 如果指示牌不足。
        """
        if count is None:
            count = 5 - len(self._rinshan_tiles)
        if count > len(self._ura_dora_indicators):
            raise ValueError(
                f"裡寶牌指示牌不足，需要 {count} 張，只有 {len(self._ura_dora_indicators)} 張"
            )
        return self._ura_dora_indicators[:count]

    def get_dora(self, indicator: Tile) -> Tile:
        """
        根據指示牌獲取寶牌。

        Args:
            indicator (Tile): 指示牌。

        Returns:
            Tile: 對應的寶牌。
        """
        if indicator.suit == Suit.JIHAI:
            # 字牌：東→南→西→北→白→發→中→東
            if indicator.rank == 4:  # 北
                return Tile(Suit.JIHAI, 1)  # 東
            elif indicator.rank == 5:  # 白
                return Tile(Suit.JIHAI, 6)  # 發
            elif indicator.rank == 6:  # 發
                return Tile(Suit.JIHAI, 7)  # 中
            elif indicator.rank == 7:  # 中
                return Tile(Suit.JIHAI, 1)  # 東
            else:
                return Tile(Suit.JIHAI, indicator.rank + 1)
        else:
            # 數牌：1-8→+1，9→1
            if indicator.rank == 9:
                return Tile(indicator.suit, 1)
            else:
                return Tile(indicator.suit, indicator.rank + 1)
