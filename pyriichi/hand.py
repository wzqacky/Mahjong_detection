"""
手牌管理系統 - Hand and Meld implementation

提供手牌操作、副露管理和和牌判定功能。
"""

from enum import Enum
from typing import List, Optional, Tuple

from pyriichi.enum_utils import TranslatableEnum
from pyriichi.tiles import Suit, Tile


class CombinationType(Enum):
    """和牌組合類型"""

    PAIR = "pair"
    TRIPLET = "triplet"
    SEQUENCE = "sequence"
    KAN = "kan"


class Combination:
    """和牌組合"""

    def __init__(self, combination_type: CombinationType, tiles: List[Tile]):
        if combination_type == CombinationType.PAIR:
            if len(tiles) != 2:
                raise ValueError("對子必須是 2 張牌")
        elif combination_type == CombinationType.TRIPLET:
            if len(tiles) != 3:
                raise ValueError("刻子必須是 3 張牌")
        elif combination_type == CombinationType.SEQUENCE:
            if len(tiles) != 3:
                raise ValueError("順子必須是 3 張牌")
        elif combination_type == CombinationType.KAN:
            if len(tiles) != 4:
                raise ValueError("槓子必須是 4 張牌")

        self._type = combination_type
        self._tiles = tiles
        self._is_open = False

    def set_open(self, is_open: bool):
        self._is_open = is_open

    @property
    def is_open(self) -> bool:
        return self._is_open

    @property
    def type(self) -> CombinationType:
        return self._type

    @property
    def tiles(self) -> List[Tile]:
        return self._tiles


def make_combination(combo_type: CombinationType, suit: Suit, rank: int) -> Combination:
    """
    根據給定類型與花色/數值快速建立 `Combination`。

    Args:
        combo_type (CombinationType): 組合類型。
        suit (Suit): 牌的花色。
        rank (int): 數牌的點數或字牌編號。

    Returns:
        Combination: 對應的 `Combination` 實例。

    Raises:
        ValueError: 當組合類型不支援或順子參數無效時。
    """

    if combo_type == CombinationType.SEQUENCE:
        if suit == Suit.JIHAI:
            raise ValueError("字牌不能組成順子")
        if not (1 <= rank <= 7):
            raise ValueError("順子起始點數必須介於 1 到 7 之間")
        tiles = [Tile(suit, rank + i) for i in range(3)]
    elif combo_type == CombinationType.TRIPLET:
        tiles = [Tile(suit, rank) for _ in range(3)]
    elif combo_type == CombinationType.KAN:
        tiles = [Tile(suit, rank) for _ in range(4)]
    elif combo_type == CombinationType.PAIR:
        tiles = [Tile(suit, rank) for _ in range(2)]
    else:
        raise ValueError(f"不支援的組合類型：{combo_type}")

    return Combination(combo_type, tiles)


class MeldType(TranslatableEnum):
    """副露類型"""

    CHI = ("chi", "吃", "チー", "Chi")
    PON = ("pon", "碰", "ポン", "Pon")
    KAN = ("kan", "明槓", "カン", "Kan")
    ANKAN = ("ankan", "暗槓", "暗槓", "Ankan")


class Meld:
    """副露（明刻、明順、明槓、暗槓）"""

    def __init__(
        self, meld_type: MeldType, tiles: List[Tile], called_tile: Optional[Tile] = None
    ):
        """
        初始化副露。

        Args:
            meld_type (MeldType): 副露類型。
            tiles (List[Tile]): 副露的牌列表。
            called_tile (Optional[Tile]): 被鳴的牌（吃/碰時需要）。

        Raises:
            ValueError: 如果牌數不符合要求。
        """
        if meld_type == MeldType.CHI and len(tiles) != 3:
            raise ValueError("吃必須是 3 張牌")
        if meld_type == MeldType.PON and len(tiles) != 3:
            raise ValueError("碰必須是 3 張牌")
        if meld_type in [MeldType.KAN, MeldType.ANKAN] and len(tiles) != 4:
            raise ValueError("槓必須是 4 張牌")

        self._type = meld_type
        self._tiles = sorted(tiles)
        self._called_tile = called_tile

    @property
    def type(self) -> MeldType:
        return self._type

    @property
    def tiles(self) -> List[Tile]:
        return self._tiles.copy()

    @property
    def called_tile(self) -> Optional[Tile]:
        return self._called_tile

    def is_concealed(self) -> bool:
        return self._type == MeldType.ANKAN

    def is_open(self) -> bool:
        return not self.is_concealed()

    def __str__(self) -> str:
        tiles_str = "".join(str(t) for t in self._tiles)
        return f"{self._type.value}({tiles_str})"

    def __repr__(self) -> str:
        return f"Meld({self._type.value}, {self._tiles})"


class Hand:
    """手牌管理器"""

    def __init__(self, tiles: List[Tile]):
        """
        初始化手牌。

        Args:
            tiles (List[Tile]): 初始手牌列表（13 或 14 張）。
        """
        self._tiles = tiles.copy()
        self._melds: List[Meld] = []
        self._discards: List[Tile] = []
        self._is_riichi = False
        self._riichi_turn: Optional[int] = None
        self._tile_counts_cache: Optional[dict] = None
        self._tenpai_discards: Optional[List[Tile]] = None
        self._last_drawn_tile: Optional[Tile] = None

    def add_tile(self, tile: Tile) -> None:
        self._tiles.append(tile)
        self._tile_counts_cache = None
        self._tenpai_discards = self.calculate_tenpai_discards()
        self._last_drawn_tile = tile

    def discard(self, tile: Tile) -> bool:
        """
        打出一張牌。

        Args:
            tile (Tile): 要打出的牌。

        Returns:
            bool: 是否成功打出。
        """
        try:
            self._tiles.remove(tile)
            self._discards.append(tile)
            self._tile_counts_cache = None
            self._tenpai_discards = None
            return True
        except ValueError:
            return False

    def remove_last_discard(self, tile: Tile) -> None:
        """
        移除最後一張捨牌（鳴牌時取回）。

        Args:
            tile (Tile): 預期移除的牌（用於校驗）。

        Raises:
            ValueError: 如果沒有捨牌或最後一張捨牌不匹配。
        """

        if not self._discards:
            raise ValueError("沒有可移除的捨牌")
        last_tile = self._discards[-1]
        if last_tile != tile:
            raise ValueError("最後一張捨牌與指定牌不符")
        self._discards.pop()

    def total_tile_count(self) -> int:
        """
        獲取手牌總數（包含副露的牌）。

        Returns:
            int: 手牌總數。
        """

        meld_count = sum(len(meld.tiles) for meld in self._melds)
        return len(self._tiles) + meld_count

    def can_chi(self, tile: Tile, from_player: int) -> List[List[Tile]]:
        """
        檢查是否可以吃。

        Args:
            tile (Tile): 被吃的牌。
            from_player (int): 出牌玩家位置（0=上家，1=對家，2=下家）。

        Returns:
            List[List[Tile]]: 可以組成的順子列表（每個順子包含 3 張牌）。
        """
        if from_player != 0:  # 只能吃上家的牌
            return []

        if tile.is_honor:  # 字牌不能組成順子
            return []

        results = []
        for i in range(-2, 1):  # 檢查 -2, -1, 0 三種情況
            needed_ranks = [tile.rank + i, tile.rank + i + 1, tile.rank + i + 2]
            if all(1 <= r <= 9 for r in needed_ranks):
                sequence = []
                for rank in needed_ranks:
                    if rank == tile.rank:
                        continue
                    needed_tile = Tile(tile.suit, rank)
                    if needed_tile not in self._tiles:
                        continue
                    sequence.append(needed_tile)
                if len(sequence) == 2:
                    results.append(sequence)

        return results

    def chi(self, tile: Tile, sequence: List[Tile]) -> Meld:
        """
        執行吃操作。

        Args:
            tile (Tile): 被吃的牌。
            sequence (List[Tile]): 手牌中的兩張牌（與被吃的牌組成順子）。

        Returns:
            Meld: 創建的 Meld 對象。

        Raises:
            ValueError: 如果不能吃。
        """
        if not self.can_chi(tile, 0):
            raise ValueError("不能吃這張牌")

        for t in sequence:
            self._tiles.remove(t)

        all_tiles = sequence + [tile]
        meld = Meld(MeldType.CHI, all_tiles, called_tile=tile)
        self._melds.append(meld)
        self._tile_counts_cache = None
        self._tenpai_discards = self.calculate_tenpai_discards()
        self._last_drawn_tile = None
        return meld

    def can_pon(self, tile: Tile) -> bool:
        """
        檢查是否可以碰。

        Args:
            tile (Tile): 被碰的牌。

        Returns:
            bool: 是否可以碰。
        """

        count = self._tiles.count(tile)
        return count >= 2

    def pon(self, tile: Tile) -> Meld:
        """
        執行碰操作。

        Args:
            tile (Tile): 被碰的牌。

        Returns:
            Meld: 創建的 Meld 對象。

        Raises:
            ValueError: 如果不能碰。
        """
        if not self.can_pon(tile):
            raise ValueError("不能碰這張牌")

        removed = 0
        tiles_to_remove = []
        for t in self._tiles:
            if t == tile and removed < 2:
                tiles_to_remove.append(t)
                removed += 1

        for t in tiles_to_remove:
            self._tiles.remove(t)

        meld_tiles = tiles_to_remove + [tile]
        meld = Meld(MeldType.PON, meld_tiles, called_tile=tile)
        self._melds.append(meld)
        self._tile_counts_cache = None
        self._tenpai_discards = self.calculate_tenpai_discards()
        self._last_drawn_tile = None
        return meld

    def can_kan(self, tile: Optional[Tile] = None) -> List[Meld]:
        """
        檢查是否可以槓。

        Args:
            tile (Optional[Tile]): 被槓的牌（明槓時需要，暗槓時為 None）。

        Returns:
            List[Meld]: 可以槓的組合列表。
        """
        results = []

        if tile is None:
            tile_counts = self._get_tile_counts(self._tiles)
            for tile, count in tile_counts.items():
                if count == 4:
                    kan_tiles = [t for t in self._tiles if t == tile]
                    results.append(Meld(MeldType.ANKAN, kan_tiles))
            for meld in self._melds:
                if (
                    meld.type == MeldType.PON
                    and meld.called_tile is not None
                    and self._tiles.count(meld.called_tile) > 0
                ):
                    kan_tiles = meld.tiles + [meld.called_tile]
                    results.append(
                        Meld(MeldType.KAN, kan_tiles, called_tile=meld.called_tile)
                    )
        elif self._tiles.count(tile) == 3:
            kan_tiles = []
            for t in self._tiles:
                if t == tile and len(kan_tiles) < 3:
                    kan_tiles.append(t)
            kan_tiles.append(tile)
            results.append(Meld(MeldType.KAN, kan_tiles, called_tile=tile))
        elif self._tiles.count(tile) == 4:
            # 指定牌的暗槓
            kan_tiles = [t for t in self._tiles if t == tile]
            results.append(Meld(MeldType.ANKAN, kan_tiles))
        elif self._tiles.count(tile) == 1:
            # 指定牌的加槓
            for meld in self._melds:
                if (
                    meld.type == MeldType.PON
                    and meld.called_tile is not None
                    and meld.called_tile == tile
                ):
                    kan_tiles = meld.tiles + [tile]
                    results.append(Meld(MeldType.KAN, kan_tiles, called_tile=tile))

        return results

    def kan(self, tile: Optional[Tile]) -> Meld:
        """
        執行槓操作。

        Args:
            tile (Optional[Tile]): 被槓的牌（明槓時需要，暗槓時為 None）。

        Returns:
            Meld: 創建的 Meld 對象。

        Raises:
            ValueError: 如果不能槓。
        """
        possible_kan = self.can_kan(tile)
        if not possible_kan:
            raise ValueError("不能槓這張牌")

        # 使用第一個可能的槓組合
        meld = possible_kan[0]

        if meld.type == MeldType.ANKAN:
            for t in meld.tiles:
                self._tiles.remove(t)
        elif meld.type == MeldType.KAN:
            if tile is None:
                called_tile = meld.called_tile
                if called_tile is None or self._tiles.count(called_tile) == 0:
                    raise ValueError("沒有可用的牌升級為加槓")
                for existing_meld in self._melds:
                    if (
                        existing_meld.type == MeldType.PON
                        and existing_meld.called_tile == called_tile
                    ):
                        self._melds.remove(existing_meld)
                        self._tiles.remove(called_tile)
                        break
            else:
                for t in meld.tiles:
                    if t in self._tiles:
                        self._tiles.remove(t)

        self._melds.append(meld)
        self._tile_counts_cache = None
        self._tenpai_discards = self.calculate_tenpai_discards()
        self._last_drawn_tile = None
        return meld

    @property
    def tiles(self) -> List[Tile]:
        """獲取當前手牌"""
        return self._tiles.copy()

    @property
    def melds(self) -> List[Meld]:
        """獲取所有副露"""
        return self._melds.copy()

    @property
    def discards(self) -> List[Tile]:
        """獲取所有舍牌"""
        return self._discards.copy()

    @property
    def is_concealed(self) -> bool:
        """是否門清（無副露）"""
        return len(self._melds) == 0

    @property
    def is_riichi(self) -> bool:
        """是否立直"""
        return self._is_riichi

    @property
    def tenpai_discards(self) -> List[Tile]:
        """獲取可以聽牌的牌"""
        return [] if self._tenpai_discards is None else self._tenpai_discards.copy()

    def set_riichi(self, is_riichi: bool = True, turn: Optional[int] = None) -> None:
        """
        設置立直狀態。

        Args:
            is_riichi (bool): 是否立直。
            turn (Optional[int]): 立直的回合數。
        """
        self._is_riichi = is_riichi
        self._riichi_turn = turn

    @property
    def last_drawn_tile(self) -> Optional[Tile]:
        """獲取最後摸到的牌"""
        return self._last_drawn_tile

    def reset_last_drawn_tile(self) -> None:
        """重置最後摸到的牌"""
        self._last_drawn_tile = None

    def _get_tile_counts(self, tiles: Optional[List[Tile]] = None) -> dict[Tile, int]:
        """
        獲取牌的計數字典。

        Args:
            tiles (Optional[List[Tile]]): 牌列表（如果為 None，則使用當前手牌並使用緩存）。

        Returns:
            Dict[Tile, int]: 牌計數字典 {Tile: count}。
        """
        # 如果使用當前手牌且緩存存在，直接返回緩存
        if tiles is None:
            if self._tile_counts_cache is not None:
                return self._tile_counts_cache
            tiles = self._tiles

        counts = {}
        for tile in tiles:
            counts[tile] = counts.get(tile, 0) + 1

        # 如果使用當前手牌，更新緩存
        if tiles is self._tiles:
            self._tile_counts_cache = counts

        return counts

    def _remove_triplet(self, counts: dict[Tile, int], tile: Tile, count: int) -> bool:
        """
        從計數中移除一個刻子（三張相同）。

        Args:
            counts (Dict[Tile, int]): 牌計數字典。
            tile (Tile): 牌。
            count (int): 牌的數量。

        Returns:
            bool: 是否成功移除。
        """
        if counts.get(tile, 0) >= count:
            counts[tile] -= count
            return True
        return False

    def _remove_sequence(self, counts: dict[Tile, int], suit: Suit, rank: int) -> bool:
        """
        從計數中移除一個順子（三張連續）。

        Args:
            counts (Dict[Tile, int]): 牌計數字典。
            suit (Suit): 花色。
            rank (int): 順子的起始數字。

        Returns:
            bool: 是否成功移除。
        """
        if suit == Suit.JIHAI:  # 字牌不能組成順子
            return False

        for i in range(3):
            r = rank + i
            tile = Tile(suit, r)
            if counts.get(tile, 0) == 0:
                return False

        for i in range(3):
            r = rank + i
            tile = Tile(suit, r)
            counts[tile] -= 1
        return True

    def _remove_pair(self, counts: dict[Tile, int], tile: Tile) -> bool:
        """
        從計數中移除一個對子（兩張相同）。

        Args:
            counts (Dict[Tile, int]): 牌計數字典。
            tile (Tile): 牌。

        Returns:
            bool: 是否成功移除。
        """
        if counts.get(tile, 0) >= 2:
            counts[tile] -= 2
            return True
        return False

    def _is_standard_winning(
        self, tiles: List[Tile], existing_melds: Optional[List[Combination]] = None
    ) -> Tuple[bool, List[List[Combination]]]:
        """
        檢查標準和牌型（4組面子 + 1對子）。

        Args:
            tiles (List[Tile]): 牌列表（門清部分）。
            existing_melds (Optional[List[Combination]]): 已有的面子列表（副露）。

        Returns:
            Tuple[bool, List[List[Combination]]]: (是否和牌, 所有可能的和牌組合列表)。
        """
        melds = existing_melds or []
        total_tiles_count = len(tiles) + sum(len(m.tiles) for m in melds)
        if total_tiles_count < 14:
            return False, []

        counts = self._get_tile_counts(tiles)
        combinations = []

        for _, count in counts.items():
            if count > 4:
                return False, []

        # 嘗試所有可能的對子
        pair_candidates = [tile for tile, count in counts.items() if count >= 2]

        for pair_tile in pair_candidates:
            test_counts = counts.copy()

            if not self._remove_pair(test_counts, pair_tile):
                continue

            # 遞迴尋找剩餘的面子
            # 注意：existing_melds 已經佔用了部分面子名額
            if results := self._find_melds(
                test_counts,
                melds,
                Combination(CombinationType.PAIR, [pair_tile, pair_tile]),
            ):
                combinations.extend(results)

        return len(combinations) > 0, combinations

    def _find_melds(
        self,
        counts: dict[Tile, int],
        current_combinations: List[Combination],
        pair_combination: Combination,
    ) -> List[List[Combination]]:
        """
        遞迴尋找所有可能的面子組合。

        Args:
            counts (Dict[Tile, int]): 剩餘牌的計數字典。
            current_combinations (List[Combination]): 已找到的面子列表。
            pair_combination (Combination): 對子組合。

        Returns:
            List[List[Combination]]: 所有可能的面子組合列表。
        """

        remaining_count = sum(counts.values())
        if remaining_count == 0:
            return (
                [current_combinations + [pair_combination]]
                if len(current_combinations) == 4
                else []
            )

        # 如果已經找到4個面子但還有剩餘牌，說明不匹配
        if len(current_combinations) == 4:
            return []

        # 如果剩餘牌數不足以組成更多面子，返回
        if remaining_count < 3:
            return []

        results = []
        results.extend(
            self._search_triplet_melds(counts, current_combinations, pair_combination)
        )
        results.extend(
            self._search_sequence_melds(counts, current_combinations, pair_combination)
        )
        return results

    def _search_triplet_melds(
        self,
        counts: dict[Tile, int],
        current_combinations: List[Combination],
        pair_combination: Combination,
    ) -> List[List[Combination]]:
        results = []
        for tile, count in counts.items():
            if count < 3 or not self._remove_triplet(counts, tile, count):
                continue
            if count == 3:
                combination = Combination(CombinationType.TRIPLET, [tile, tile, tile])
            elif count == 4:
                combination = Combination(CombinationType.KAN, [tile, tile, tile, tile])
            else:
                raise ValueError(f"Invalid count: {count} for tile: {tile}")
            new_combinations = current_combinations + [combination]
            if result := self._find_melds(counts, new_combinations, pair_combination):
                results.extend(result)
            counts[tile] += count
        return results

    def _search_sequence_melds(
        self,
        counts: dict[Tile, int],
        current_combinations: List[Combination],
        pair_combination: Combination,
    ) -> List[List[Combination]]:
        results = []
        for suit in [Suit.MANZU, Suit.PINZU, Suit.SOZU]:
            for rank in range(1, 8):
                if any(counts.get(Tile(suit, rank + i), 0) <= 0 for i in range(3)):
                    continue
                original_values = {
                    Tile(suit, rank + i): counts.get(Tile(suit, rank + i), 0)
                    for i in range(3)
                }
                if not self._remove_sequence(counts, suit, rank):
                    continue
                new_combinations = current_combinations + [
                    Combination(
                        CombinationType.SEQUENCE,
                        [Tile(suit, rank), Tile(suit, rank + 1), Tile(suit, rank + 2)],
                    )
                ]
                if result := self._find_melds(
                    counts, new_combinations, pair_combination
                ):
                    results.extend(result)
                for i in range(3):
                    counts[Tile(suit, rank + i)] = original_values[Tile(suit, rank + i)]
        return results

    def _is_seven_pairs(self, tiles: List[Tile]) -> bool:
        """
        檢查是否為七對子。

        Args:
            tiles (List[Tile]): 牌列表（14張）。

        Returns:
            bool: 是否為七對子。
        """
        if len(tiles) != 14:
            return False

        counts = self._get_tile_counts(tiles)
        pairs = 0

        for count in counts.values():
            if count == 2:
                pairs += 1
            elif count != 0:
                return False  # 有不是2的數量

        return pairs == 7

    def _is_kokushi_musou(self, tiles: List[Tile]) -> bool:
        """
        檢查是否為國士無雙。

        Args:
            tiles (List[Tile]): 牌列表（14張）。

        Returns:
            bool: 是否為國士無雙。
        """
        if len(tiles) != 14:
            return False

        # 國士無雙需要的13種幺九牌
        required_tiles = [
            (Suit.MANZU, 1),
            (Suit.MANZU, 9),
            (Suit.PINZU, 1),
            (Suit.PINZU, 9),
            (Suit.SOZU, 1),
            (Suit.SOZU, 9),
            (Suit.JIHAI, 1),
            (Suit.JIHAI, 2),
            (Suit.JIHAI, 3),
            (Suit.JIHAI, 4),
            (Suit.JIHAI, 5),
            (Suit.JIHAI, 6),
            (Suit.JIHAI, 7),
        ]

        found_tiles = set()
        duplicate = None

        for tile in tiles:
            key = (tile.suit, tile.rank)
            if key in required_tiles and key in found_tiles and duplicate is None:
                duplicate = key
            elif (
                key in required_tiles
                and key in found_tiles
                and duplicate != key
                or key not in required_tiles
            ):
                return False  # 有多個重複
            elif key not in found_tiles:
                found_tiles.add(key)
        # 必須有13種各1張，加上1張重複
        return len(found_tiles) == 13 and duplicate is not None

    def is_tenpai(self) -> bool:
        """
        是否聽牌（優化版本：只檢查可能相關的牌）。

        Returns:
            bool: 是否聽牌。
        """
        return len(self.get_waiting_tiles()) > 0

    def calculate_tenpai_discards(self) -> List[Tile]:
        """
        獲取打出後可以聽牌的牌列表。

        Returns:
            List[Tile]: 打出後可以聽牌的牌列表。
        """

        valid_discards = []
        original_tiles = list(self._tiles)
        unique_tiles = set(original_tiles)

        for tile_to_discard in unique_tiles:
            # 暫時移除一張牌
            try:
                self._tiles.remove(tile_to_discard)
                self._tile_counts_cache = None

                if self.is_tenpai():
                    valid_discards.append(tile_to_discard)

                # 恢復手牌
                self._tiles.append(tile_to_discard)
                self._tile_counts_cache = None
            except ValueError:
                continue

        return valid_discards

    def get_waiting_tiles(self) -> List[Tile]:
        """
        獲取聽牌列表（優化版本：只檢查可能相關的牌）。

        Returns:
            List[Tile]: 所有可以和的牌列表。
        """
        # 收集所有可能的聽牌候選（與手牌相關的牌）
        candidates = set[Tile]()

        for tile in self._tiles:
            suit, rank = tile.suit, tile.rank
            # 添加相同牌
            candidates.add(tile)
            # 如果是數牌，添加相鄰牌
            if suit != Suit.JIHAI:
                if rank > 1:
                    candidates.add(Tile(suit, rank - 1))
                if rank < 9:
                    candidates.add(Tile(suit, rank + 1))
                # 對於順子，還需要檢查更遠的牌
                if rank > 2:
                    candidates.add(Tile(suit, rank - 2))
                if rank < 8:
                    candidates.add(Tile(suit, rank + 2))

        # 如果候選太少，回退到檢查所有牌（確保不遺漏）
        if len(candidates) < 10:
            for suit in Suit:
                max_rank = 7 if suit == Suit.JIHAI else 9
                for rank in range(1, max_rank + 1):
                    candidates.add(Tile(suit, rank))

        for suit in [Suit.MANZU, Suit.PINZU, Suit.SOZU]:
            for rank in [1, 9]:
                candidates.add(Tile(suit, rank))
        for rank in range(1, 8):
            candidates.add(Tile(Suit.JIHAI, rank))

        return [
            test_tile for test_tile in candidates if self.is_winning_hand(test_tile)
        ]

    def is_winning_hand(self, winning_tile: Tile, is_tsumo: bool = False) -> bool:
        """
        檢查是否可以和牌。

        Args:
            winning_tile (Tile): 和牌牌。
            is_tsumo (bool): 是否自摸（默認 False）。

        Returns:
            bool: 是否可以和牌。
        """

        concealed_tiles = self._tiles.copy()

        if not is_tsumo:
            concealed_tiles.append(winning_tile)

        existing_melds = []
        for meld in self._melds:
            combo_type = CombinationType.SEQUENCE
            if meld.type == MeldType.PON:
                combo_type = CombinationType.TRIPLET
            elif meld.type in [MeldType.KAN, MeldType.ANKAN]:
                combo_type = CombinationType.KAN

            combo = Combination(combo_type, meld.tiles)
            combo.set_open(meld.is_open())
            existing_melds.append(combo)

        # 檢查標準和牌型
        is_winning, _ = self._is_standard_winning(concealed_tiles, existing_melds)
        if is_winning:
            return True

        # 檢查七對子（必須門清）
        # 七對子不允許任何副露（包括暗槓）
        if self.is_concealed:
            if self._is_seven_pairs(concealed_tiles):
                return True
            if self._is_kokushi_musou(concealed_tiles):
                return True

        return False

    def get_winning_combinations(
        self, winning_tile: Tile, is_tsumo: bool = False
    ) -> List[List[Combination]]:
        """
        獲取和牌組合（用於役種判定）。

        Args:
            winning_tile (Tile): 和牌牌。
            is_tsumo (bool): 是否自摸（默認 False）。

        Returns:
            List[List[Combination]]: 所有可能的和牌組合（每種組合包含 4 組面子和 1 對子）。
        """
        # 加上和牌牌（門清部分）
        concealed_tiles = self._tiles.copy()

        if not is_tsumo:
            concealed_tiles.append(winning_tile)

        # 轉換副露為 Combination
        existing_melds = []
        for meld in self._melds:
            combo_type = CombinationType.SEQUENCE
            if meld.type == MeldType.PON:
                combo_type = CombinationType.TRIPLET
            elif meld.type in [MeldType.KAN, MeldType.ANKAN]:
                combo_type = CombinationType.KAN

            combo = Combination(combo_type, meld.tiles)
            combo.set_open(meld.is_open())
            existing_melds.append(combo)

        # 檢查標準和牌型
        is_winning, combinations = self._is_standard_winning(
            concealed_tiles, existing_melds
        )

        return combinations if is_winning else []
