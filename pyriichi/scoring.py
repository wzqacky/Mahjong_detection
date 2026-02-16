"""
得分計算系統 - ScoreCalculator implementation

提供符數、翻數和點數計算功能。
"""

from dataclasses import dataclass
from typing import List, Optional

from pyriichi.game_state import GameState
from pyriichi.hand import Combination, CombinationType, Hand
from pyriichi.tiles import Suit, Tile
from pyriichi.yaku import WaitingType, Yaku, YakuResult


@dataclass
class ScoreResult:
    """得分計算結果"""

    han: int  # 翻數
    fu: int  # 符數
    base_points: int  # 基本點
    total_points: int  # 總點數（自摸時為每人支付，榮和時為總支付）
    payment_from: int  # 支付者位置（榮和時）
    payment_to: int  # 獲得者位置
    is_yakuman: bool  # 是否役滿
    yakuman_count: int  # 役滿倍數
    is_tsumo: bool = False  # 是否自摸
    dealer_payment: int = 0  # 莊家支付（自摸時）
    non_dealer_payment: int = 0  # 閒家支付（自摸時）
    honba_bonus: int = 0  # 本場獎勵
    riichi_sticks_bonus: int = 0  # 供託分配
    kiriage_mangan_enabled: bool = False  # 是否啟用切上滿貫
    pao_player: Optional[int] = None  # 包牌者位置
    pao_payment: int = 0  # 包牌者支付金額

    def __post_init__(self):
        """計算最終得分。"""
        if self.is_yakuman:
            self.total_points = 8000 * self.yakuman_count
        elif self.han >= 13:
            self.total_points = 8000  # 役滿
        elif self.han >= 11:
            self.total_points = 6000  # 三倍滿
        elif self.han >= 8:
            self.total_points = 4000  # 倍滿
        elif self.han >= 6:
            self.total_points = 3000  # 跳滿
        elif self.han >= 5 or (self.han == 4 and self.fu >= 40):
            self.total_points = 2000  # 滿貫
        elif self.kiriage_mangan_enabled and (
            (self.han == 4 and self.fu == 30) or (self.han == 3 and self.fu == 60)
        ):
            # 切上滿貫：30符4翻 或60符3翻 計為滿貫
            self.total_points = 2000  # 滿貫
        else:
            base = self.fu * (2 ** (self.han + 2))
            self.base_points = base
            # 點數不進位，留待 calculate_payments 處理
            self.total_points = base

    def calculate_payments(self, game_state: GameState) -> None:
        """
        計算支付方式。

        自摸支付：
        - 莊家自摸：每個閒家支付 base_payment + honba，總共獲得 3 * (base_payment + honba)
        - 閒家自摸：莊家支付 2 * (base_payment + honba)，其他閒家支付 base_payment + honba，總共獲得 2 * (base_payment + honba) + (base_payment + honba) * 2

        榮和支付：
        - 支付者支付全部 total_points（包含本場）

        包牌支付（役滿）：
        - 自摸：包牌者支付全部
        - 榮和（包牌者放銃）：包牌者支付全部
        - 榮和（非包牌者放銃）：包牌者與放銃者各支付一半

        本場獎勵：
        - 每個本場 +300 點（自摸時每人支付，榮和時放銃者支付）

        供託分配：
        - 所有供託棒給和牌者

        Args:
            game_state (GameState): 遊戲狀態（用於獲取本場數和供託棒）。
        """

        self.honba_bonus = game_state.honba * 300

        self.riichi_sticks_bonus = game_state.riichi_sticks * 1000

        base_payment = self.total_points

        if self.pao_player is not None and self.is_yakuman:
            if self.is_tsumo:
                if self.payment_to == game_state.dealer:
                    # 莊家自摸：16000 all -> 48000
                    total_win = (base_payment * 6 + 99) // 100 * 100
                else:
                    # 閒家自摸：8000/16000 -> 32000
                    total_win = (base_payment * 4 + 99) // 100 * 100

                # 加上本場 (自摸時本場是每人支付 100*honba，共 300*honba)
                total_honba = game_state.honba * 300

                self.total_points = total_win + total_honba + self.riichi_sticks_bonus

                self.pao_payment = total_win + total_honba
                self.dealer_payment = 0
                self.non_dealer_payment = 0
                return

            else:
                if self.payment_to == game_state.dealer:
                    total_win = (base_payment * 6 + 99) // 100 * 100
                else:
                    total_win = (base_payment * 4 + 99) // 100 * 100

                total_honba = game_state.honba * 300
                self.total_points = total_win + total_honba + self.riichi_sticks_bonus

                if self.payment_from != self.pao_player:
                    # 包牌者與放銃者分擔 (折半)

                    total_pay = total_win + total_honba
                    half_pay = total_pay // 2

                    self.pao_payment = half_pay
                    # 放銃者支付剩下的 (通常也是一半)
                    pass
                else:
                    # 包牌者放銃：正常支付
                    self.pao_payment = (
                        0  # 由 payment_from (即 pao_player) 支付，不視為額外包牌支付
                    )

                self.dealer_payment = 0
                self.non_dealer_payment = 0
                return

        if self.is_tsumo:
            # 每人需要支付：base_payment + honba_bonus
            honba_per_person = game_state.honba * 100

            if self.payment_to == game_state.dealer:
                self.dealer_payment = 0
                self.non_dealer_payment = (
                    2 * base_payment + 99
                ) // 100 * 100 + honba_per_person
                self.total_points = (
                    self.non_dealer_payment * 3 + self.riichi_sticks_bonus
                )
            else:
                self.dealer_payment = (
                    2 * base_payment + 99
                ) // 100 * 100 + honba_per_person
                self.non_dealer_payment = (
                    base_payment + 99
                ) // 100 * 100 + honba_per_person
                self.total_points = (
                    self.dealer_payment
                    + self.non_dealer_payment * 2
                    + self.riichi_sticks_bonus
                )
        else:
            # 閒家榮和：4 * Basic + 300 * honba
            # 莊家榮和：6 * Basic + 300 * honba

            total_honba = game_state.honba * 300

            if self.payment_to == game_state.dealer:
                win_points = (6 * base_payment + 99) // 100 * 100
            else:
                win_points = (4 * base_payment + 99) // 100 * 100

            self.total_points = win_points + total_honba + self.riichi_sticks_bonus
            self.dealer_payment = 0
            self.non_dealer_payment = (
                0  # 榮和時由 payment_from 支付，這裡不設置 dealer/non_dealer payment
            )


class ScoreCalculator:
    """得分計算器"""

    @staticmethod
    def _group_combinations(winning_combination: Optional[List[Combination]]) -> dict:
        groups = {
            CombinationType.PAIR: [],
            CombinationType.SEQUENCE: [],
            CombinationType.TRIPLET: [],
            CombinationType.KAN: [],
        }
        if not winning_combination:
            return groups

        for combination in winning_combination:
            if combination is None:
                continue
            groups.setdefault(combination.type, []).append(combination)

        return groups

    @staticmethod
    def _extract_pair(
        winning_combination: Optional[List[Combination]],
    ) -> Optional[Combination]:
        if not winning_combination:
            return None
        for combination in winning_combination:
            if combination.type == CombinationType.PAIR:
                return combination
        return None

    def calculate(
        self,
        hand: Hand,
        winning_tile: Tile,
        winning_combination: List,
        yaku_results: List[YakuResult],
        dora_count: int,
        game_state: GameState,
        is_tsumo: bool,
        player_position: int = 0,
        pao_player: Optional[int] = None,
    ) -> ScoreResult:
        """
        計算得分。

        Args:
            hand (Hand): 手牌。
            winning_tile (Tile): 和牌牌。
            winning_combination (List): 和牌組合。
            yaku_results (List[YakuResult]): 役種列表。
            dora_count (int): 寶牌數量。
            game_state (GameState): 遊戲狀態。
            is_tsumo (bool): 是否自摸。
            player_position (int): 玩家位置。
            pao_player (Optional[int]): 包牌者位置。

        Returns:
            ScoreResult: 得分計算結果。
        """
        # ... (計算 fu, han, yakuman)
        # 計算符數
        fu = self.calculate_fu(
            hand,
            winning_tile,
            winning_combination,
            yaku_results,
            game_state,
            is_tsumo,
            player_position,
        )

        han = self.calculate_han(yaku_results, dora_count)

        is_yakuman = any(r.is_yakuman for r in yaku_results)
        yakuman_count = sum(bool(r.is_yakuman) for r in yaku_results)

        result = ScoreResult(
            han=han,
            fu=fu,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=0,
            is_yakuman=is_yakuman,
            yakuman_count=yakuman_count,
            is_tsumo=is_tsumo,
            kiriage_mangan_enabled=game_state.ruleset.kiriage_mangan,
            pao_player=pao_player,
        )

        result.calculate_payments(game_state)

        return result

    def calculate_fu(
        self,
        hand: Hand,
        winning_tile: Tile,
        winning_combination: List,
        yaku_results: List[YakuResult],
        game_state: GameState,
        is_tsumo: bool,
        player_position: int = 0,
    ) -> int:
        """
        計算符數。

        Args:
            hand (Hand): 手牌。
            winning_tile (Tile): 和牌牌。
            winning_combination (List): 和牌組合。
            yaku_results (List[YakuResult]): 役種列表。
            game_state (GameState): 遊戲狀態。
            is_tsumo (bool): 是否自摸。
            player_position (int): 玩家位置（用於計算自風對子符數）。

        Returns:
            int: 符數。
        """
        if any(r.yaku == Yaku.CHIITOITSU for r in yaku_results):
            return 25  # 七對子固定 25 符

        if any(r.yaku == Yaku.PINFU for r in yaku_results):
            return 30 if is_tsumo else 20  # 平和固定 30 符（自摸）或 20 符（榮和）

        fu = 20  # 基本符

        if hand.is_concealed and not is_tsumo:
            fu += 10
        elif is_tsumo:
            fu += 2

        for combination in winning_combination:
            if combination.type in [
                CombinationType.PAIR,
                CombinationType.SEQUENCE,
            ]:
                continue

            tile = combination.tiles[0]

            is_open = combination.is_open

            # 如果是榮和，且該組合包含和牌牌（且原本是門清），則視為明刻
            # 注意：只有刻子需要這樣判斷（順子符數為0，槓子必定是已形成的）
            if (
                not is_tsumo
                and not is_open
                and combination.type == CombinationType.TRIPLET
            ):
                if tile.suit == winning_tile.suit and tile.rank == winning_tile.rank:
                    is_open = True

            if combination.type == CombinationType.TRIPLET:
                base = 4 if is_open else 8
                fu += base if tile.is_terminal or tile.is_honor else base // 2
            elif combination.type == CombinationType.KAN:
                base = 16 if is_open else 32
                fu += base if tile.is_terminal or tile.is_honor else base // 2

        if pair_combination := self._extract_pair(winning_combination):
            pair_tile = pair_combination.tiles[0]

            # 役牌對子 +2 符
            if pair_tile.suit == Suit.JIHAI:
                if pair_tile.rank in [5, 6, 7]:  # 白、發、中
                    fu += 2

                round_wind_tile = game_state.round_wind.tile
                if round_wind_tile == pair_tile:
                    fu += 2

                player_winds = game_state.player_winds
                if player_position < len(player_winds):
                    player_wind_tile = player_winds[player_position].tile
                    if player_wind_tile == pair_tile:
                        fu += 2

        waiting_type = self._determine_waiting_type(winning_tile, winning_combination)

        if waiting_type in {
            WaitingType.TANKI,
            WaitingType.PENCHAN,
            WaitingType.KANCHAN,
        }:
            fu += 2
        # 兩面聽和雙碰聽不增加符數

        return ((fu + 9) // 10) * 10

    def _determine_waiting_type(
        self, winning_tile: Tile, winning_combination: List
    ) -> WaitingType:
        """
        判斷聽牌類型。

        Args:
            winning_tile (Tile): 和牌牌。
            winning_combination (List): 和牌組合。

        Returns:
            WaitingType: 聽牌類型：'ryanmen'（兩面）、'penchan'（邊張）、'kanchan'（嵌張）、'tanki'（單騎）、'shabo'（雙碰）。
        """
        if not winning_combination:
            return WaitingType.RYANMEN

        pair_combination = self._extract_pair(winning_combination)
        if pair_combination and any(
            tile == winning_tile for tile in pair_combination.tiles
        ):
            return WaitingType.TANKI

        for combination in winning_combination:
            if combination.type != CombinationType.SEQUENCE:
                continue

            if winning_tile not in combination.tiles:
                continue

            tiles = sorted(combination.tiles)
            try:
                index = tiles.index(winning_tile)
            except ValueError:
                index = next(
                    (
                        i
                        for i, tile in enumerate(tiles)
                        if tile.suit == winning_tile.suit
                        and tile.rank == winning_tile.rank
                    ),
                    -1,
                )
                if index == -1:
                    continue

            if index == 1:
                return WaitingType.KANCHAN

            first_rank = tiles[0].rank
            last_rank = tiles[-1].rank
            if index in {0, 2}:
                if first_rank == 1 or last_rank == 9:
                    return WaitingType.PENCHAN
                return WaitingType.RYANMEN

        return WaitingType.RYANMEN

    def calculate_han(self, yaku_results: List[YakuResult], dora_count: int) -> int:
        """
        計算翻數。

        Args:
            yaku_results (List[YakuResult]): 役種列表。
            dora_count (int): 寶牌數量。

        Returns:
            int: 翻數。
        """
        han = sum(r.han for r in yaku_results)
        han += dora_count
        return han
