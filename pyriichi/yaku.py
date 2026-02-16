"""
役種判定系統 - YakuChecker implementation

提供所有役種的判定功能。
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pyriichi.enum_utils import TranslatableEnum
from pyriichi.hand import Combination, Hand, CombinationType
from pyriichi.tiles import Tile, Suit
from pyriichi.game_state import GameState, Wind
from pyriichi.rules_config import RenhouPolicy


__all__ = ["Yaku", "YakuResult", "YakuChecker"]


class Yaku(TranslatableEnum):
    """所有役種枚舉"""

    RIICHI = ("riichi", "立直", "立直", "Riichi")
    DOUBLE_RIICHI = ("double_riichi", "雙立直", "ダブルリーチ", "Double Riichi")
    IPPATSU = ("ippatsu", "一發", "一発", "Ippatsu")
    MENZEN_TSUMO = ("menzen_tsumo", "門清自摸", "門前清自摸和", "Menzen Tsumo")
    TANYAO = ("tanyao", "斷么九", "断么九", "Tanyao")
    PINFU = ("pinfu", "平和", "平和", "Pinfu")
    IIPEIKOU = ("iipeikou", "一盃口", "一盃口", "Iipeikou")
    RYANPEIKOU = ("ryanpeikou", "二盃口", "二盃口", "Ryanpeikou")
    TOITOI = ("toitoi", "對對和", "対々和", "Toitoi")
    SANANKOU = ("sanankou", "三暗刻", "三暗刻", "Sanankou")
    SANKANTSU = ("sankantsu", "三槓子", "三槓子", "Sankantsu")
    SANSHOKU_DOUJUN = ("sanshoku_doujun", "三色同順", "三色同順", "Sanshoku Doujun")
    SANSHOKU_DOUKOU = ("sanshoku_doukou", "三色同刻", "三色同刻", "Sanshoku Doukou")
    ITTSU = ("ittsu", "一氣通貫", "一気通貫", "Ittsu")
    HONITSU = ("honitsu", "混一色", "混一色", "Honitsu")
    CHINITSU = ("chinitsu", "清一色", "清一色", "Chinitsu")
    JUNCHAN = ("junchan", "純全帶么九", "純全帯么九", "Junchan")
    CHANTA = ("chanta", "全帶么九", "全帯么九", "Chanta")
    HONROUTOU = ("honroutou", "混老頭", "混老頭", "Honroutou")
    SHOUSANGEN = ("shousangen", "小三元", "小三元", "Shousangen")
    DAISANGEN = ("daisangen", "大三元", "大三元", "Daisangen")
    SUUANKOU = ("suuankou", "四暗刻", "四暗刻", "Suuankou")
    SUUANKOU_TANKI = ("suuankou_tanki", "四暗刻單騎", "四暗刻単騎", "Suuankou Tanki")
    SUUKANTSU = ("suukantsu", "四槓子", "四槓子", "Suukantsu")
    SHOUSUUSHI = ("shousuushi", "小四喜", "小四喜", "Shousuushi")
    DAISUUSHI = ("daisuushi", "大四喜", "大四喜", "Daisuushi")
    CHINROUTOU = ("chinroutou", "清老頭", "清老頭", "Chinroutou")
    TSUUIISOU = ("tsuuiisou", "字一色", "字一色", "Tsuuiisou")
    RYUIISOU = ("ryuiisou", "綠一色", "緑一色", "Ryuuiisou")
    CHUUREN_POUTOU = ("chuuren_poutou", "九蓮寶燈", "九蓮宝燈", "Chuuren Poutou")
    CHUUREN_POUTOU_PURE = ("chuuren_poutou_pure", "純正九蓮寶燈", "純正九蓮宝燈", "Pure Chuuren Poutou")
    KOKUSHI_MUSOU = ("kokushi_musou", "國士無雙", "国士無双", "Kokushi Musou")
    KOKUSHI_MUSOU_JUUSANMEN = ("kokushi_musou_juusanmen", "國士無雙十三面", "国士無双十三面", "Kokushi Musou Juusanmen")
    TENHOU = ("tenhou", "天和", "天和", "Tenhou")
    CHIHOU = ("chihou", "地和", "地和", "Chihou")
    RENHOU = ("renhou", "人和", "人和", "Renhou")
    HAITEI = ("haitei", "海底撈月", "海底撈月", "Haitei")
    HOUTEI = ("houtei", "河底撈魚", "河底撈魚", "Houtei")
    RINSHAN = ("rinshan", "嶺上開花", "嶺上開花", "Rinshan Kaihou")
    CHANKAN = ("chankan", "搶槓", "槍槓", "Chankan")
    CHIITOITSU = ("chiitoitsu", "七對子", "七対子", "Chiitoitsu")
    HAKU = ("haku", "白", "白", "Haku")
    HATSU = ("hatsu", "發", "發", "Hatsu")
    CHUN = ("chun", "中", "中", "Chun")
    ROUND_WIND_EAST = ("round_wind_east", "場風東", "場風東", "Round Wind East")
    ROUND_WIND_SOUTH = ("round_wind_south", "場風南", "場風南", "Round Wind South")
    ROUND_WIND_WEST = ("round_wind_west", "場風西", "場風西", "Round Wind West")
    ROUND_WIND_NORTH = ("round_wind_north", "場風北", "場風北", "Round Wind North")
    SEAT_WIND_EAST = ("seat_wind_east", "自風東", "自風東", "Seat Wind East")
    SEAT_WIND_SOUTH = ("seat_wind_south", "自風南", "自風南", "Seat Wind South")
    SEAT_WIND_WEST = ("seat_wind_west", "自風西", "自風西", "Seat Wind West")
    SEAT_WIND_NORTH = ("seat_wind_north", "自風北", "自風北", "Seat Wind North")


class WaitingType(Enum):
    """聽牌類型"""

    RYANMEN = "ryanmen"
    PENCHAN = "penchan"
    KANCHAN = "kanchan"
    TANKI = "tanki"
    SHABO = "shabo"


@dataclass(frozen=True)
class YakuResult:
    """役種判定結果"""

    yaku: Yaku
    han: int
    is_yakuman: bool

    def __eq__(self, other):
        return self.yaku == other.yaku if isinstance(other, YakuResult) else False

    def __hash__(self):
        return hash(self.yaku)


class YakuChecker:
    """役種判定器"""

    def _group_combinations(
        self, winning_combination: Optional[List[Combination]]
    ) -> Dict[CombinationType, List[Combination]]:
        """
        將和牌組合依 CombinationType 分組。

        Args:
            winning_combination (Optional[List[Combination]]): 和牌組合。

        Returns:
            Dict[CombinationType, List[Combination]]: 分組後的組合字典。
        """
        groups: Dict[CombinationType, List[Combination]] = {
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
    def _get_combination_key(combination: Combination) -> Tuple[Suit, int]:
        """
        取得組合代表鍵值（花色、最小牌的數字）。

        對於順子，使用起始牌作為鍵；對於刻子/槓子/對子，因牌皆相同，取任一張即可。

        Args:
            combination (Combination): 組合。

        Returns:
            Tuple[Suit, int]: (花色, 數字)。
        """
        tiles = sorted(combination.tiles)
        tile = tiles[0]
        return tile.suit, tile.rank

    @staticmethod
    def _flatten_tiles(winning_combination: Optional[List[Combination]]) -> List[Tile]:
        """
        將全部組合中的牌攤平成單一列表。

        Args:
            winning_combination (Optional[List[Combination]]): 和牌組合。

        Returns:
            List[Tile]: 所有牌的列表。
        """
        if not winning_combination:
            return []
        tiles: List[Tile] = []
        for combination in winning_combination:
            tiles.extend(combination.tiles)
        return tiles

    def _extract_pair(self, winning_combination: Optional[List[Combination]]) -> Optional[Combination]:
        """
        從組合中找出對子（若存在）。

        Args:
            winning_combination (Optional[List[Combination]]): 和牌組合。

        Returns:
            Optional[Combination]: 對子組合，若不存在則返回 None。
        """
        if not winning_combination:
            return None
        for combination in winning_combination:
            if combination.type == CombinationType.PAIR:
                return combination
        return None

    def check_all(
        self,
        hand: Hand,
        winning_tile: Tile,
        winning_combination: List[Combination],
        game_state: GameState,
        is_tsumo: bool = False,
        is_ippatsu: bool = False,
        is_first_turn: bool = False,
        is_last_tile: bool = False,
        player_position: int = 0,
        is_rinshan: bool = False,
        is_chankan: bool = False,
    ) -> List[YakuResult]:
        """
        檢查所有符合的役種。

        Args:
            hand (Hand): 手牌。
            winning_tile (Tile): 和牌牌。
            winning_combination (List[Combination]): 和牌組合（標準型）或 None（特殊型如七對子）。
            game_state (GameState): 遊戲狀態。
            is_tsumo (bool): 是否自摸。
            is_ippatsu (bool): 是否為一發。
            is_first_turn (bool): 是否為第一巡。
            is_last_tile (bool): 是否為最後一張牌（海底撈月/河底撈魚）。
            player_position (int): 玩家位置（用於判定自風）。
            is_rinshan (bool): 是否為嶺上開花。
            is_chankan (bool): 是否為搶槓和。

        Returns:
            List[YakuResult]: 所有符合的役種列表。
        """
        # 天和、地和、人和判定（優先檢查，因為是役滿）
        if result := self.check_tenhou(hand, is_tsumo, is_first_turn, player_position, game_state):
            return [result]
        if result := self.check_chihou(hand, is_tsumo, is_first_turn, player_position, game_state):
            return [result]
        if result := self.check_renhou(hand, is_tsumo, is_first_turn, player_position, game_state):
            return [result]

        # 國士無雙判定（優先檢查，因為是役滿）
        if result := self.check_kokushi_musou(hand, winning_tile):
            results = [result]
            # 國士無雙可以與立直複合
            is_double_riichi = is_first_turn and hand.is_concealed
            results.extend(self.check_riichi(hand, game_state, is_ippatsu, is_double_riichi))
            return results

        # 七對子判定
        if result := self.check_chiitoitsu(hand, winning_tile):
            results = [result]
            if hand.is_riichi:
                # 雙立直優先於普通立直
                is_double_riichi = is_first_turn and hand.is_concealed
                if is_double_riichi:
                    results.insert(0, YakuResult(Yaku.DOUBLE_RIICHI, 2, False))
                else:
                    results.insert(0, YakuResult(Yaku.RIICHI, 1, False))
                if is_ippatsu:
                    results.insert(1, YakuResult(Yaku.IPPATSU, 1, False))
            return results

        # 其他役滿檢查（優先檢查，因為役滿會覆蓋其他役種）
        # 注意：某些役滿可以同時存在（如四暗刻+字一色）
        yakuman_results = []
        if result := self.check_daisangen(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_suukantsu(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_suuankou(hand, winning_combination, winning_tile, game_state):
            yakuman_results.append(result)

        if result := self.check_shousuushi(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_daisuushi(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_chinroutou(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_tsuuiisou(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_ryuuiisou(hand, winning_combination):
            yakuman_results.append(result)
        if result := self.check_chuuren_poutou(hand, winning_tile, game_state):
            yakuman_results.append(result)

        # 如果有役滿，只返回役滿（役滿不與其他役種複合，但可以多個役滿複合）
        if yakuman_results:
            # 役滿可以與立直複合
            is_double_riichi = is_first_turn and hand.is_concealed
            yakuman_results.extend(self.check_riichi(hand, game_state, is_ippatsu, is_double_riichi))
            return yakuman_results

        results = []

        # 基本役
        is_double_riichi = is_first_turn and hand.is_concealed
        results.extend(self.check_riichi(hand, game_state, is_ippatsu, is_double_riichi))
        if result := self.check_menzen_tsumo(hand, game_state, is_tsumo):
            results.append(result)
        if result := self.check_haitei_raoyue(hand, is_tsumo, is_last_tile):
            results.append(result)
        if result := self.check_rinshan_kaihou(hand, is_rinshan):
            results.append(result)
        if result := self.check_chankan(hand, is_chankan):
            results.append(result)
        if result := self.check_tanyao(hand, winning_combination):
            results.append(result)
        if result := self.check_pinfu(hand, winning_combination, game_state, winning_tile, player_position):
            results.append(result)

        if result := self.check_iipeikou(hand, winning_combination):
            results.append(result)
        if result := self.check_toitoi(hand, winning_combination):
            results.append(result)
        if result := self.check_sankantsu(hand, winning_combination):
            results.append(result)

        # 役牌（可能有多個）
        yakuhai_results = self.check_yakuhai(hand, winning_combination, game_state, player_position)
        results.extend(yakuhai_results)

        # 特殊役（2-3翻）
        if result := self.check_sanshoku_doujun(hand, winning_combination):
            results.append(result)
        if result := self.check_ittsu(hand, winning_combination):
            results.append(result)
        if result := self.check_sanankou(hand, winning_combination):
            results.append(result)
        if result := self.check_chinitsu(hand, winning_combination):
            results.append(result)
        if result := self.check_honitsu(hand, winning_combination):
            results.append(result)
        if result := self.check_sanshoku_doukou(hand, winning_combination):
            results.append(result)
        if result := self.check_shousangen(hand, winning_combination):
            results.append(result)
        if result := self.check_honroutou(hand, winning_combination):
            results.append(result)

        # 高級役（3翻以上）
        if result := self.check_junchan(hand, winning_combination, game_state):
            results.append(result)
        if result := self.check_honchan(hand, winning_combination, game_state):
            results.append(result)
        if result := self.check_ryanpeikou(hand, winning_combination):
            results.append(result)

        # 役種衝突檢測和過濾
        results = self._filter_conflicting_yaku(results, winning_combination, game_state)

        return results

    def _filter_conflicting_yaku(
        self, results: List[YakuResult], winning_combination: List[Combination], game_state: GameState
    ) -> List[YakuResult]:
        """
        過濾衝突的役種。

        Args:
            results (List[YakuResult]): 役種結果列表。
            winning_combination (List[Combination]): 和牌組合。
            game_state (GameState): 遊戲狀態。

        Returns:
            List[YakuResult]: 過濾後的役種列表。
        """
        filtered = []
        yaku_set = {r.yaku for r in results}

        for result in results:
            should_include = True

            # 1. 平和與役牌衝突
            if result.yaku == Yaku.TOITOI:
                sequence_yaku = {
                    Yaku.SANSHOKU_DOUJUN,
                    Yaku.ITTSU,
                    Yaku.IIPEIKOU,
                    Yaku.RYANPEIKOU,
                }
                if yaku_set & sequence_yaku:
                    should_include = False

            elif result.yaku == Yaku.PINFU:
                yakuhai_set = {
                    Yaku.HAKU,
                    Yaku.HATSU,
                    Yaku.CHUN,
                    Yaku.ROUND_WIND_EAST,
                    Yaku.ROUND_WIND_SOUTH,
                    Yaku.ROUND_WIND_WEST,
                    Yaku.ROUND_WIND_NORTH,
                }
                if yaku_set & yakuhai_set:
                    should_include = False

            elif result.yaku == Yaku.TANYAO:
                # 包含幺九的役種
                terminal_yaku = {
                    Yaku.ITTSU,  # 包含1和9的順子
                    Yaku.JUNCHAN,
                    Yaku.CHANTA,
                    Yaku.HONROUTOU,
                    Yaku.CHINROUTOU,
                }
                if yaku_set & terminal_yaku:
                    should_include = False

            # 4. 一盃口與二盃口互斥
            if result.yaku == Yaku.IIPEIKOU and Yaku.RYANPEIKOU in yaku_set:
                should_include = False

            # 5. 清一色與混一色互斥
            if result.yaku == Yaku.CHINITSU and Yaku.HONITSU in yaku_set:
                should_include = False
            if result.yaku == Yaku.HONITSU and Yaku.CHINITSU in yaku_set:
                should_include = False

            # 6. 純全帶与混全帶互斥
            if result.yaku == Yaku.JUNCHAN and Yaku.CHANTA in yaku_set:
                should_include = False
            if result.yaku == Yaku.CHANTA and Yaku.JUNCHAN in yaku_set:
                should_include = False

            # 7. 平和與對對和衝突（結構上互斥）
            if result.yaku == Yaku.PINFU and Yaku.TOITOI in yaku_set:
                should_include = False
            if result.yaku == Yaku.TOITOI and Yaku.PINFU in yaku_set:
                should_include = False

            # 8. 平和與一盃口、二盃口衝突（平和只能有一個對子）
            if result.yaku == Yaku.PINFU and (Yaku.IIPEIKOU in yaku_set or Yaku.RYANPEIKOU in yaku_set):
                should_include = False

            if should_include:
                filtered.append(result)

        return filtered

    def check_riichi(self, hand: Hand, game_state: GameState, is_ippatsu: Optional[bool] = None, is_double_riichi: bool = False) -> List[YakuResult]:
        """
        檢查立直、雙立直與一發。

        立直：聽牌時宣告立直（1翻）。
        雙立直：第一巡宣告立直（2翻，取代普通立直）。
        一發：立直後一巡內和牌（立直後的第一個自己的回合）。

        Args:
            hand (Hand): 手牌。
            game_state (GameState): 遊戲狀態。
            is_ippatsu (Optional[bool]): 是否為一發。
            is_double_riichi (bool): 是否為雙立直。

        Returns:
            List[YakuResult]: 符合的役種列表。
        """
        results: List[YakuResult] = []

        if not hand.is_riichi:
            return results

        # 雙立直優先於普通立直
        if is_double_riichi:
            results.append(YakuResult(Yaku.DOUBLE_RIICHI, 2, False))
        else:
            results.append(YakuResult(Yaku.RIICHI, 1, False))

        if is_ippatsu:
            results.append(YakuResult(Yaku.IPPATSU, 1, False))

        return results

    def check_menzen_tsumo(self, hand: Hand, game_state: GameState, is_tsumo: bool = False) -> Optional[YakuResult]:
        """
        檢查門清自摸。

        門清自摸：門清狀態下自摸和牌。

        Args:
            hand (Hand): 手牌。
            game_state (GameState): 遊戲狀態。
            is_tsumo (bool): 是否自摸。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not hand.is_concealed:
            return None

        return YakuResult(Yaku.MENZEN_TSUMO, 1, False) if is_tsumo else None

    def check_tanyao(self, hand: Hand, winning_combination: List[Combination]) -> Optional[YakuResult]:
        """
        檢查斷么九。

        斷么九：全部由中張牌（2-8）組成，無幺九牌（1、9、字牌）。

        Args:
            hand (Hand): 手牌。
            winning_combination (List[Combination]): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None


        for combination in winning_combination:
            for tile in combination.tiles:
                if tile.is_honor or tile.is_terminal:
                    return None

        return YakuResult(Yaku.TANYAO, 1, False)

    def check_pinfu(
        self,
        hand: Hand,
        winning_combination: List[Combination],
        game_state: Optional[GameState] = None,
        winning_tile: Optional[Tile] = None,
        player_position: int = 0,
    ) -> Optional[YakuResult]:
        """
        檢查平和。

        平和：
        1. 門清。
        2. 全部由順子組成（雀頭除外）。
        3. 雀頭不能是役牌（場風、自風、三元牌）。
        4. 聽牌必須是兩面聽（根據規則配置）。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。
            game_state (Optional[GameState]): 遊戲狀態。
            winning_tile (Optional[Tile]): 和牌牌。
            player_position (int): 玩家位置（用於檢查自風）。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        pair_combination = self._extract_pair(winning_combination)
        sequences = groups[CombinationType.SEQUENCE]
        triplets = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]

        # 必須有4個順子且沒有刻子/槓子，並且存在對子
        if pair_combination is None or len(sequences) != 4 or triplets:
            return None

        # 對子不能是役牌（檢查場風、自風、三元牌）
        pair_tile = sorted(pair_combination.tiles)[0]
        if pair_tile.suit == Suit.JIHAI:

            sangen = [5, 6, 7]  # 白、發、中
            if pair_tile.rank in sangen:
                return None  # 三元牌對子，不能是平和


            if game_state is not None:
                round_wind = game_state.round_wind
                wind_mapping = {
                    1: Wind.EAST,
                    2: Wind.SOUTH,
                    3: Wind.WEST,
                    4: Wind.NORTH,
                }
                if round_wind == wind_mapping.get(pair_tile.rank):
                    return None  # 場風對子，不能是平和

            # 檢查是否是自風
            if game_state:
                player_wind = game_state.player_winds[player_position]
                if player_wind.tile == pair_tile:
                    return None  # 自風對子，不能是平和

        # 檢查聽牌類型（兩面聽）- 根據規則配置
        ruleset = game_state.ruleset if game_state else None
        if ruleset and ruleset.pinfu_require_ryanmen and winning_tile is not None:
            waiting_type = self._determine_waiting_type(winning_tile, winning_combination)
            if waiting_type != WaitingType.RYANMEN:
                return None  # 不是兩面聽，不能是平和

        return YakuResult(Yaku.PINFU, 1, False)

    def check_iipeikou(self, hand: Hand, winning_combination: List[Combination]) -> Optional[YakuResult]:
        """
        檢查一盃口。

        一盃口：門清狀態下，有兩組相同的順子。

        Args:
            hand (Hand): 手牌。
            winning_combination (List[Combination]): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        sequences = [self._get_combination_key(seq) for seq in groups[CombinationType.SEQUENCE]]

        # 檢查是否有兩組相同的順子
        if len(sequences) >= 2:
            for i in range(len(sequences)):
                for j in range(i + 1, len(sequences)):
                    if sequences[i] == sequences[j]:
                        return YakuResult(Yaku.IIPEIKOU, 1, False)

        return None

    def check_toitoi(self, hand: Hand, winning_combination: List[Combination]) -> Optional[YakuResult]:
        """
        檢查對對和。

        對對和：全部由刻子組成（4個刻子 + 1個對子）。

        Args:
            hand (Hand): 手牌。
            winning_combination (List[Combination]): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        pair_combination = self._extract_pair(winning_combination)
        sequences = groups[CombinationType.SEQUENCE]
        triplet_like = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]

        # 有順子則不符合，必須有4個刻子/槓子以及對子
        if sequences:
            return None

        if pair_combination is not None and len(triplet_like) == 4:
            return YakuResult(Yaku.TOITOI, 2, False)

        return None

    def check_sankantsu(self, hand: Hand, winning_combination: List[Combination]) -> Optional[YakuResult]:
        """
        檢查三槓子。

        三槓子：有三組槓子。

        Args:
            hand (Hand): 手牌。
            winning_combination (List[Combination]): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        kan_count = len(groups[CombinationType.KAN])

        # 三個槓子
        return YakuResult(Yaku.SANKANTSU, 2, False) if kan_count == 3 else None

    def check_yakuhai(
        self, hand: Hand, winning_combination: List[Combination], game_state: GameState, player_position: int = 0
    ) -> List[YakuResult]:
        """
        檢查役牌（場風、自風、三元牌刻子）。

        Args:
            hand (Hand): 手牌。
            winning_combination (List[Combination]): 和牌組合。
            game_state (GameState): 遊戲狀態。
            player_position (int): 玩家位置。

        Returns:
            List[YakuResult]: 役牌列表（可能有多個）。
        """
        results = []
        if not winning_combination:
            return results

        # 三元牌
        sangen = [5, 6, 7]  # 白、發、中
        wind_rank_mapping = {
            1: (Wind.EAST, Yaku.ROUND_WIND_EAST, Yaku.SEAT_WIND_EAST),
            2: (Wind.SOUTH, Yaku.ROUND_WIND_SOUTH, Yaku.SEAT_WIND_SOUTH),
            3: (Wind.WEST, Yaku.ROUND_WIND_WEST, Yaku.SEAT_WIND_WEST),
            4: (Wind.NORTH, Yaku.ROUND_WIND_NORTH, Yaku.SEAT_WIND_NORTH),
        }
        round_wind = game_state.round_wind
        player_wind = (
            game_state.player_winds[player_position] if 0 <= player_position < len(game_state.player_winds) else None
        )

        groups = self._group_combinations(winning_combination)
        honor_sets = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]

        for combination in honor_sets:
            tile = sorted(combination.tiles)[0]
            if tile.suit != Suit.JIHAI:
                continue

            rank = tile.rank
            if rank in sangen:
                if rank == 5:
                    results.append(YakuResult(Yaku.HAKU, 1, False))
                elif rank == 6:
                    results.append(YakuResult(Yaku.HATSU, 1, False))
                elif rank == 7:
                    results.append(YakuResult(Yaku.CHUN, 1, False))

            if rank in wind_rank_mapping:
                target_wind, round_yaku, seat_yaku = wind_rank_mapping[rank]
                if round_wind == target_wind:
                    results.append(YakuResult(round_yaku, 1, False))
                if player_wind == target_wind:
                    results.append(YakuResult(seat_yaku, 1, False))

        return results

    def check_sanshoku_doujun(self, hand: Hand, winning_combination: List[Combination]) -> Optional[YakuResult]:
        """
        檢查三色同順。

        三色同順：三種數牌（萬、筒、條）都有相同數字的順子。

        Args:
            hand (Hand): 手牌。
            winning_combination (List[Combination]): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        # 統計順子
        sequences_by_suit = {Suit.MANZU: [], Suit.PINZU: [], Suit.SOZU: []}

        groups = self._group_combinations(winning_combination)
        for sequence in groups[CombinationType.SEQUENCE]:
            suit, rank = self._get_combination_key(sequence)
            if suit in sequences_by_suit:
                sequences_by_suit[suit].append(rank)

        # 檢查三種花色是否有相同數字的順子
        for rank in range(1, 8):  # 順子最多到7
            has_manzu = rank in sequences_by_suit[Suit.MANZU]
            has_pinzu = rank in sequences_by_suit[Suit.PINZU]
            has_sozu = rank in sequences_by_suit[Suit.SOZU]

            if has_manzu and has_pinzu and has_sozu:
                return YakuResult(Yaku.SANSHOKU_DOUJUN, 2, False)

        return None

    def check_ittsu(self, hand: Hand, winning_combination: List[Combination]) -> Optional[YakuResult]:
        """
        檢查一氣通貫。

        一氣通貫：同一花色有 1-3、4-6、7-9 的順子。

        Args:
            hand (Hand): 手牌。
            winning_combination (List[Combination]): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        # 按花色統計順子
        sequences_by_suit = {Suit.MANZU: [], Suit.PINZU: [], Suit.SOZU: []}

        groups = self._group_combinations(winning_combination)
        for sequence in groups[CombinationType.SEQUENCE]:
            suit, rank = self._get_combination_key(sequence)
            if suit in sequences_by_suit:
                sequences_by_suit[suit].append(rank)

        # 檢查每種花色是否有一氣通貫
        for suit in [Suit.MANZU, Suit.PINZU, Suit.SOZU]:
            sequences = sequences_by_suit[suit]
            # 需要 1-3、4-6、7-9 各一個順子
            has_123 = 1 in sequences
            has_456 = 4 in sequences
            has_789 = 7 in sequences

            if has_123 and has_456 and has_789:
                return YakuResult(Yaku.ITTSU, 2, False)

        return None

    def check_sanankou(self, hand: Hand, winning_combination: List[Combination]) -> Optional[YakuResult]:
        """
        檢查三暗刻。

        三暗刻：有三組暗刻（門清狀態下的刻子）。

        Args:
            hand (Hand): 手牌。
            winning_combination (List[Combination]): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        triplets = len(groups[CombinationType.TRIPLET])

        return YakuResult(Yaku.SANANKOU, 2, False) if triplets >= 3 else None

    def check_chinitsu(self, hand: Hand, winning_combination: List[Combination]) -> Optional[YakuResult]:
        """
        檢查清一色。

        清一色：全部由同一種數牌組成（萬、筒、條）。

        Args:
            hand (Hand): 手牌。
            winning_combination (List[Combination]): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        suits = set()
        for tile in self._flatten_tiles(winning_combination):
            if tile.suit == Suit.JIHAI:
                return None
            suits.add(tile.suit)

        # 只有一種數牌花色
        return YakuResult(Yaku.CHINITSU, 6, False) if len(suits) == 1 else None

    def check_honitsu(self, hand: Hand, winning_combination: List[Combination]) -> Optional[YakuResult]:
        """
        檢查混一色。

        混一色：由一種數牌和字牌組成。

        Args:
            hand (Hand): 手牌。
            winning_combination (List[Combination]): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        # 檢查數牌花色和字牌
        number_suits = set()
        has_honor = False

        for tile in self._flatten_tiles(winning_combination):
            if tile.suit == Suit.JIHAI:
                has_honor = True
            else:
                number_suits.add(tile.suit)

        # 只有一種數牌花色，且包含字牌
        if len(number_suits) == 1 and has_honor:
            return YakuResult(Yaku.HONITSU, 3, False)

        return None

    def check_chiitoitsu(self, hand: Hand, winning_tile: Optional[Tile] = None) -> Optional[YakuResult]:
        """
        檢查七對子。

        七對子：七組對子（特殊和牌型）。
        注意：七對子不會有標準的和牌組合，需要特殊處理。

        Args:
            hand (Hand): 手牌。
            winning_tile (Optional[Tile]): 和牌牌。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        all_tiles = hand.tiles + [winning_tile] if winning_tile else hand.tiles
        if not hand.is_concealed or len(all_tiles) != 14:
            return None

        counts: Dict[Tile, int] = {}
        for tile in all_tiles:
            counts[tile] = counts.get(tile, 0) + 1
            if counts[tile] > 2:
                return None

        pairs = [count for count in counts.values() if count == 2]
        return None if len(pairs) != 7 else YakuResult(Yaku.CHIITOITSU, 2, False)

    def check_junchan(
        self, hand: Hand, winning_combination: List[Combination], game_state: Optional[GameState] = None
    ) -> Optional[YakuResult]:
        """
        檢查純全帶么九。

        純全帶么九：全部由順子組成，且每個順子都包含1或9。
        無字牌，對子可以是任何數牌（但實際上通常是1或9）。
        根據門清/副露狀態決定翻數（標準競技規則）。

        Args:
            hand (Hand): 手牌。
            winning_combination (List[Combination]): 和牌組合。
            game_state (Optional[GameState]): 遊戲狀態。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        # 檢查是否包含字牌
        for tile in self._flatten_tiles(winning_combination):
            if tile.is_honor:
                return None

        groups = self._group_combinations(winning_combination)
        sequences = groups[CombinationType.SEQUENCE]
        triplets = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]

        # 必須為 4 個順子且每個順子包含 1 或 9
        if triplets:
            return None

        if len(sequences) == 4:
            for combination in sequences:
                tiles = sorted(combination.tiles)
                start_rank = tiles[0].rank
                if start_rank not in [1, 7]:
                    return None

            # 根據規則配置決定翻數
            ruleset = game_state.ruleset if game_state else None
            if ruleset:
                han = ruleset.junchan_closed_han if hand.is_concealed else ruleset.junchan_open_han
            else:
                # 默認：門清3翻，副露2翻
                han = 3 if hand.is_concealed else 2
            return YakuResult(Yaku.JUNCHAN, han, False)

        return None

    def check_honchan(
        self, hand: Hand, winning_combination: List, game_state: Optional[GameState] = None
    ) -> Optional[YakuResult]:
        """
        檢查全帶么九（Chanta）。

        全帶么九：全部由順子和對子組成，且每個面子都包含1或9或字牌。
        可以有字牌，根據門清/副露狀態決定翻數（標準競技規則）。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。
            game_state (Optional[GameState]): 遊戲狀態。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        ruleset = game_state.ruleset if game_state else None
        if ruleset and not ruleset.chanta_enabled:
            return None

        if not winning_combination:
            return None

        # 檢查是否有字牌
        has_honor = False
        all_terminals = True

        for combination in winning_combination:
            tiles = combination.tiles
            if any(tile.is_honor for tile in tiles):
                has_honor = True

            if combination.type == CombinationType.SEQUENCE:
                sorted_tiles = sorted(tiles)
                start_rank = sorted_tiles[0].rank
                if start_rank not in [1, 7]:
                    all_terminals = False
                    break
            else:
                representative_tile = sorted(tiles)[0]
                if not (representative_tile.is_terminal or representative_tile.is_honor):
                    all_terminals = False
                    break

        # 必須有字牌，且所有數牌都是幺九牌
        if has_honor and all_terminals:
            # 根據規則配置決定翻數
            if ruleset:
                han = ruleset.chanta_closed_han if hand.is_concealed else ruleset.chanta_open_han
            else:
                # 默認：門清2翻，副露1翻
                han = 2 if hand.is_concealed else 1
            return YakuResult(Yaku.CHANTA, han, False)

        return None

    def check_ryanpeikou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查二盃口。

        二盃口：門清狀態下，有兩組不同的相同順子（兩組1-2-3和兩組4-5-6）。
        注意：二盃口會覆蓋一盃口，所以需要先檢查二盃口。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        sequences = [self._get_combination_key(seq) for seq in groups[CombinationType.SEQUENCE]]

        # 必須有4個順子
        if len(sequences) != 4:
            return None

        # 檢查是否有兩組不同的相同順子
        sequence_counts = {}
        for seq in sequences:
            sequence_counts[seq] = sequence_counts.get(seq, 0) + 1

        # 計算有多少組不同的順子各出現兩次
        paired_sequences = [seq for seq, count in sequence_counts.items() if count >= 2]

        # 二盃口需要兩組不同的順子各出現兩次（總共4個順子）
        if len(paired_sequences) == 2:
            # 檢查是否每組都恰好出現兩次
            for seq in paired_sequences:
                if sequence_counts[seq] != 2:
                    return None
            return YakuResult(Yaku.RYANPEIKOU, 3, False)

        return None

    def check_sanshoku_doukou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查三色同刻。

        三色同刻：三種數牌（萬、筒、條）都有相同數字的刻子。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        # 統計刻子
        triplets_by_suit = {Suit.MANZU: [], Suit.PINZU: [], Suit.SOZU: []}

        groups = self._group_combinations(winning_combination)
        for triplet in groups[CombinationType.TRIPLET]:
            suit, rank = self._get_combination_key(triplet)
            if suit in triplets_by_suit:
                triplets_by_suit[suit].append(rank)

        # 檢查三種花色是否有相同數字的刻子
        for rank in range(1, 10):
            has_manzu = rank in triplets_by_suit[Suit.MANZU]
            has_pinzu = rank in triplets_by_suit[Suit.PINZU]
            has_sozu = rank in triplets_by_suit[Suit.SOZU]

            if has_manzu and has_pinzu and has_sozu:
                return YakuResult(Yaku.SANSHOKU_DOUKOU, 2, False)

        return None

    def check_shousangen(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查小三元。

        小三元：有兩個三元牌刻子，一個三元牌對子。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        sangen = [5, 6, 7]  # 白、發、中
        sangen_triplets = []
        sangen_pair = None

        groups = self._group_combinations(winning_combination)
        triplet_like = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]
        for combination in triplet_like:
            tile = sorted(combination.tiles)[0]
            if tile.suit == Suit.JIHAI and tile.rank in sangen:
                sangen_triplets.append(tile.rank)

        pair_combination = self._extract_pair(winning_combination)
        if pair_combination:
            pair_tile = sorted(pair_combination.tiles)[0]
            if pair_tile.suit == Suit.JIHAI and pair_tile.rank in sangen:
                sangen_pair = pair_tile.rank

        # 兩個三元牌刻子 + 一個三元牌對子
        if len(sangen_triplets) == 2 and sangen_pair is not None:
            return YakuResult(Yaku.SHOUSANGEN, 2, False)

        return None

    def check_honroutou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查混老頭。

        混老頭：全部由幺九牌（1、9、字牌）組成。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        # 檢查所有牌是否都是幺九牌或字牌
        for combination in winning_combination:
            for tile in combination.tiles:
                if not (tile.is_terminal or tile.is_honor):
                    return None

        return YakuResult(Yaku.HONROUTOU, 2, False)

    def check_daisangen(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查大三元。

        大三元：有三組三元牌刻子（白、發、中）。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        sangen = [5, 6, 7]  # 白、發、中
        sangen_triplets = []

        groups = self._group_combinations(winning_combination)
        triplet_like = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]
        for combination in triplet_like:
            tile = sorted(combination.tiles)[0]
            if tile.suit == Suit.JIHAI and tile.rank in sangen:
                sangen_triplets.append(tile.rank)

        # 三個三元牌刻子
        if len(sangen_triplets) == 3:
            return YakuResult(Yaku.DAISANGEN, 13, True)

        return None

    def check_suukantsu(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查四槓子。

        四槓子：有四組槓子。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        kan_count = len(groups[CombinationType.KAN])

        # 四個槓子
        return YakuResult(Yaku.SUUKANTSU, 13, True) if kan_count == 4 else None

    def check_suuankou(
        self,
        hand: Hand,
        winning_combination: List,
        winning_tile: Optional[Tile] = None,
        game_state: Optional[GameState] = None,
    ) -> Optional[YakuResult]:
        """
        檢查四暗刻。

        四暗刻：門清狀態下，有四組暗刻（或四暗刻單騎）。
        根據規則配置，四暗刻單騎可能為雙倍役滿。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。
            winning_tile (Optional[Tile]): 和牌牌。
            game_state (Optional[GameState]): 遊戲狀態。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not hand.is_concealed:
            return None

        if not winning_combination:
            return None

        groups = self._group_combinations(winning_combination)
        triplet_like = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]
        triplets = len(triplet_like)

        is_tanki = False
        pair_combination = self._extract_pair(winning_combination)
        if pair_combination and winning_tile:
            pair_tile = sorted(pair_combination.tiles)[0]
            if pair_tile.suit == winning_tile.suit and pair_tile.rank == winning_tile.rank:
                is_tanki = True

        # 四個暗刻
        if triplets == 4:
            ruleset = game_state.ruleset if game_state else None
            if ruleset and ruleset.suuankou_tanki_double and is_tanki:
                return YakuResult(Yaku.SUUANKOU_TANKI, 26, True)
            return YakuResult(Yaku.SUUANKOU, 13, True)

        return None

    def check_kokushi_musou(self, hand: Hand, winning_tile: Optional[Tile] = None) -> Optional[YakuResult]:
        """
        檢查國士無雙。

        國士無雙：13種幺九牌各一張，再有一張幺九牌（13面聽）。
        國士無雙十三面：13種幺九牌各一張，再有一張幺九牌，且該牌為聽牌。

        Args:
            hand (Hand): 手牌。
            winning_tile (Optional[Tile]): 和牌牌。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not hand.is_concealed:
            return None

        tiles = hand.tiles + [winning_tile] if winning_tile else hand.tiles
        if len(tiles) != 14:
            return None

        # 需要的13種幺九牌
        required_tiles = [
            Tile(Suit.MANZU, 1),
            Tile(Suit.MANZU, 9),
            Tile(Suit.PINZU, 1),
            Tile(Suit.PINZU, 9),
            Tile(Suit.SOZU, 1),
            Tile(Suit.SOZU, 9),
            Tile(Suit.JIHAI, 1),
            Tile(Suit.JIHAI, 2),
            Tile(Suit.JIHAI, 3),
            Tile(Suit.JIHAI, 4),
            Tile(Suit.JIHAI, 5),
            Tile(Suit.JIHAI, 6),
            Tile(Suit.JIHAI, 7),
        ]

        # 統計每種牌
        counts = {}
        for tile in tiles:
            counts[tile] = counts.get(tile, 0) + 1

        # 檢查是否只有一張重複
        pairs = 0
        for key, count in counts.items():
            if key not in required_tiles:
                return None  # 有非幺九牌
            if count == 2:
                if pairs != 0:
                    return None  # 有兩張重複
                pairs += 1

        if hand.tiles == required_tiles:
            return YakuResult(Yaku.KOKUSHI_MUSOU_JUUSANMEN, 26, True)
        else:
            return YakuResult(Yaku.KOKUSHI_MUSOU, 13, True)

    def check_shousuushi(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查小四喜。

        小四喜：有三組風牌刻子，一個風牌對子。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        kaze = [1, 2, 3, 4]  # 東、南、西、北
        kaze_triplets = []
        kaze_pair = None

        groups = self._group_combinations(winning_combination)
        triplet_like = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]
        for combination in triplet_like:
            tile = sorted(combination.tiles)[0]
            if tile.suit == Suit.JIHAI and tile.rank in kaze:
                kaze_triplets.append(tile.rank)

        pair_combination = self._extract_pair(winning_combination)
        if pair_combination:
            pair_tile = sorted(pair_combination.tiles)[0]
            if pair_tile.suit == Suit.JIHAI and pair_tile.rank in kaze:
                kaze_pair = pair_tile.rank

        # 三個風牌刻子 + 一個風牌對子
        if len(kaze_triplets) == 3 and kaze_pair is not None:
            return YakuResult(Yaku.SHOUSUUSHI, 13, True)

        return None

    def check_daisuushi(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查大四喜。

        大四喜：有四組風牌刻子。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        kaze = [1, 2, 3, 4]  # 東、南、西、北
        kaze_triplets = []

        groups = self._group_combinations(winning_combination)
        triplet_like = groups[CombinationType.TRIPLET] + groups[CombinationType.KAN]
        for combination in triplet_like:
            tile = sorted(combination.tiles)[0]
            if tile.suit == Suit.JIHAI and tile.rank in kaze:
                kaze_triplets.append(tile.rank)

        # 四個風牌刻子
        if len(kaze_triplets) == 4:
            return YakuResult(Yaku.DAISUUSHI, 13, True)

        return None

    def check_chinroutou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查清老頭。

        清老頭：全部由幺九牌刻子組成（無字牌）。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        for combination in winning_combination:
            tiles = combination.tiles

            # 有字牌就不是清老頭
            if any(tile.is_honor for tile in tiles):
                return None

            if combination.type not in {CombinationType.TRIPLET, CombinationType.KAN, CombinationType.PAIR}:
                return None

            if any(not tile.is_terminal for tile in tiles):
                return None
        return YakuResult(Yaku.CHINROUTOU, 13, True)

    def check_tsuuiisou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查字一色。

        字一色：全部由字牌組成。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        for tile in self._flatten_tiles(winning_combination):
            if not tile.is_honor:
                return None

        return YakuResult(Yaku.TSUUIISOU, 13, True)

    def check_ryuuiisou(self, hand: Hand, winning_combination: List) -> Optional[YakuResult]:
        """
        檢查綠一色。

        綠一色：全部由綠牌組成（2、3、4、6、8條、發）。

        Args:
            hand (Hand): 手牌。
            winning_combination (List): 和牌組合。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not winning_combination:
            return None

        # 綠牌：2、3、4、6、8條、發
        green_tiles = [
            (Suit.SOZU, 2),
            (Suit.SOZU, 3),
            (Suit.SOZU, 4),
            (Suit.SOZU, 6),
            (Suit.SOZU, 8),
            (Suit.JIHAI, 6),  # 發
        ]

        green_tile_set = set(green_tiles)
        for tile in self._flatten_tiles(winning_combination):
            if (tile.suit, tile.rank) not in green_tile_set:
                return None

        return YakuResult(Yaku.RYUIISOU, 13, True)

    def check_chuuren_poutou(
        self, hand: Hand, winning_tile: Tile, game_state: Optional[GameState] = None
    ) -> Optional[YakuResult]:
        """
        檢查九蓮寶燈。

        九蓮寶燈：同一種花色（萬、筒、條）有 1112345678999 + 任意一張相同花色。
        純正九蓮寶燈：九蓮寶燈且聽牌為九面聽。
        根據規則配置，純正九蓮寶燈可能為雙倍役滿。

        Args:
            hand (Hand): 手牌。
            winning_tile (Tile): 和牌牌。
            game_state (Optional[GameState]): 遊戲狀態。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not hand.is_concealed:
            return None

        all_tiles = hand.tiles + [winning_tile] if winning_tile else hand.tiles

        if len(all_tiles) != 14:
            return None

        # 檢查是否為同一種數牌花色
        suits = set[Suit]()
        for tile in all_tiles:
            if tile.suit != Suit.JIHAI:  # 只檢查數牌
                suits.add(tile.suit)
            else:
                return None  # 有字牌就不是九蓮寶燈

        # 必須只有一種花色
        if len(suits) != 1:
            return None

        suit = suits.pop()

        # 統計該花色的牌數
        counts: Dict[int, int] = {}
        for tile in all_tiles:
            if tile.suit == suit:
                counts[tile.rank] = counts.get(tile.rank, 0) + 1

        # 檢查 1 & 9 至少 3 張，其他至少 1 張
        for rank, count in counts.items():
            if (rank in {1, 9} and count < 3) or (rank not in {1, 9} and count < 1):
                return None

        # 檢查總數是否為14張（1-9各至少要求的數量，加上額外的1張）
        total = sum(counts.values())
        if total != 14:
            return None

        # 檢查是否為純正九蓮寶燈
        is_pure = True
        hand_counts: Dict[int, int] = {}
        for tile in hand.tiles:
            hand_counts[tile.rank] = hand_counts.get(tile.rank, 0) + 1
            if (tile.rank in {1, 9} and hand_counts[tile.rank] > 3) or (
                tile.rank not in {1, 9} and hand_counts[tile.rank] > 1
            ):
                is_pure = False
                break

        if is_pure:
            ruleset = game_state.ruleset if game_state else None
            if ruleset and ruleset.chuuren_pure_double:
                return YakuResult(Yaku.CHUUREN_POUTOU_PURE, 26, True)
            else:
                return YakuResult(Yaku.CHUUREN_POUTOU_PURE, 13, True)

        return YakuResult(Yaku.CHUUREN_POUTOU, 13, True)

    def check_tenhou(
        self, hand: Hand, is_tsumo: bool, is_first_turn: bool, player_position: int, game_state: GameState
    ) -> Optional[YakuResult]:
        """
        檢查天和。

        天和：莊家在第一巡自摸和牌。
        條件：
        1. 莊家（player_position == dealer）
        2. 第一巡（is_first_turn）
        3. 自摸（is_tsumo）
        4. 門清（hand.is_concealed）

        Args:
            hand (Hand): 手牌。
            is_tsumo (bool): 是否自摸。
            is_first_turn (bool): 是否為第一巡。
            player_position (int): 玩家位置。
            game_state (GameState): 遊戲狀態。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        # 必須是莊家
        if player_position != game_state.dealer:
            return None

        # 必須是第一巡
        if not is_first_turn:
            return None

        # 必須是自摸
        if not is_tsumo:
            return None

        # 必須是門清
        return YakuResult(Yaku.TENHOU, 13, True) if hand.is_concealed else None

    def check_chihou(
        self, hand: Hand, is_tsumo: bool, is_first_turn: bool, player_position: int, game_state: GameState
    ) -> Optional[YakuResult]:
        """
        檢查地和。

        地和：閒家在第一巡自摸和牌。
        條件：
        1. 閒家（player_position != dealer）
        2. 第一巡（is_first_turn）
        3. 自摸（is_tsumo）
        4. 門清（hand.is_concealed）

        Args:
            hand (Hand): 手牌。
            is_tsumo (bool): 是否自摸。
            is_first_turn (bool): 是否為第一巡。
            player_position (int): 玩家位置。
            game_state (GameState): 遊戲狀態。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        # 必須是閒家
        if player_position == game_state.dealer:
            return None

        # 必須是第一巡
        if not is_first_turn:
            return None

        # 必須是自摸
        if not is_tsumo:
            return None

        # 必須是門清
        return YakuResult(Yaku.CHIHOU, 13, True) if hand.is_concealed else None

    def check_renhou(
        self, hand: Hand, is_tsumo: bool, is_first_turn: bool, player_position: int, game_state: GameState
    ) -> Optional[YakuResult]:
        """
        檢查人和。

        人和：閒家在第一巡榮和。
        條件：
        1. 閒家（player_position != dealer）
        2. 第一巡（is_first_turn）
        3. 榮和（not is_tsumo）
        4. 門清（hand.is_concealed）

        根據規則配置決定翻數：
        - RenhouPolicy.YAKUMAN: 役滿（13翻）
        - RenhouPolicy.TWO_HAN: 2翻（標準競技規則）
        - RenhouPolicy.OFF: 不啟用

        Args:
            hand (Hand): 手牌。
            is_tsumo (bool): 是否自摸。
            is_first_turn (bool): 是否為第一巡。
            player_position (int): 玩家位置。
            game_state (GameState): 遊戲狀態。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        ruleset = game_state.ruleset

        # 檢查是否啟用
        if ruleset.renhou_policy == RenhouPolicy.OFF:
            return None

        # 必須是閒家
        if player_position == game_state.dealer:
            return None

        # 必須是第一巡
        if not is_first_turn:
            return None

        # 必須是榮和
        if is_tsumo:
            return None

        # 必須是門清
        if not hand.is_concealed:
            return None

        # 根據規則配置返回不同的翻數
        if ruleset.renhou_policy == RenhouPolicy.YAKUMAN:
            return YakuResult(Yaku.RENHOU, 13, True)
        elif ruleset.renhou_policy == RenhouPolicy.TWO_HAN:
            return YakuResult(Yaku.RENHOU, 2, False)
        else:
            return None

    def check_haitei_raoyue(self, hand: Hand, is_tsumo: bool, is_last_tile: bool) -> Optional[YakuResult]:
        """
        檢查海底撈月/河底撈魚。

        海底撈月：自摸最後一張牌和牌（1翻）。
        河底撈魚：榮和最後一張牌和牌（1翻）。

        Args:
            hand (Hand): 手牌。
            is_tsumo (bool): 是否自摸。
            is_last_tile (bool): 是否為最後一張牌。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        if not is_last_tile:
            return None

        if is_tsumo:
            return YakuResult(Yaku.HAITEI, 1, False)
        else:
            return YakuResult(Yaku.HOUTEI, 1, False)

    def check_rinshan_kaihou(self, hand: Hand, is_rinshan: bool) -> Optional[YakuResult]:
        """
        檢查嶺上開花。

        嶺上開花：槓後從嶺上摸牌和牌（1翻）。

        Args:
            hand (Hand): 手牌。
            is_rinshan (bool): 是否為嶺上開花。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        return YakuResult(Yaku.RINSHAN, 1, False) if is_rinshan else None

    def _determine_waiting_type(self, winning_tile: Tile, winning_combination: List) -> WaitingType:
        """
        判定聽牌類型。

        Args:
            winning_tile (Tile): 和牌牌。
            winning_combination (List): 和牌組合。

        Returns:
            WaitingType: 聽牌類型：ryanmen（兩面）、penchan（邊張）、kanchan（嵌張）、tanki（單騎）、shabo（雙碰）。
        """
        if not winning_combination:
            return WaitingType.RYANMEN  # 默認為兩面聽

        pair_combination = self._extract_pair(winning_combination)
        if pair_combination and any(tile == winning_tile for tile in pair_combination.tiles):
            return WaitingType.TANKI

        for combination in winning_combination:
            if combination.type != CombinationType.SEQUENCE:
                continue

            if winning_tile not in combination.tiles:
                continue

            tiles = sorted(combination.tiles)
            # 找出和牌牌在順子中的位置
            try:
                index = tiles.index(winning_tile)
            except ValueError:
                # winning_tile 可能因為物件不同而不相等，改用屬性匹配
                index = next(
                    (
                        i
                        for i, tile in enumerate(tiles)
                        if tile.suit == winning_tile.suit and tile.rank == winning_tile.rank
                    ),
                    -1,
                )
                if index == -1:
                    continue

            if index == 1:
                return WaitingType.KANCHAN

            first_rank = tiles[0].rank
            last_rank = tiles[-1].rank
            if index == 0 or index == 2:
                if first_rank == 1 or last_rank == 9:
                    return WaitingType.PENCHAN
                return WaitingType.RYANMEN

        # 默認為兩面聽
        return WaitingType.RYANMEN


    def check_chankan(self, hand: Hand, is_chankan: bool = False) -> Optional[YakuResult]:
        """
        檢查搶槓。

        Args:
            hand (Hand): 手牌。
            is_chankan (bool): 是否為搶槓和。

        Returns:
            Optional[YakuResult]: 役種結果，若不符合則返回 None。
        """
        return YakuResult(Yaku.CHANKAN, 1, False) if is_chankan else None
