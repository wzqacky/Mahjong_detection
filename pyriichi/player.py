import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from pyriichi.hand import Hand, Meld
from pyriichi.rules import GameAction, GameState
from pyriichi.tiles import Tile


@dataclass
class PublicInfo:
    """
    公開遊戲資訊 (Visible Game Information)。

    包含所有玩家可見的資訊，用於 AI 決策。
    """

    turn_number: int
    dora_indicators: List[Tile]
    discards: Dict[int, List[Tile]]  # 每個玩家的捨牌
    melds: Dict[int, List[Meld]]  # 每個玩家的副露
    riichi_players: List[int]  # 立直玩家列表
    scores: List[int]  # 玩家分數


class BasePlayer(ABC):
    """
    玩家基類 (Abstract Base Class for Players)。

    定義了玩家的基本介面，所有具體玩家類別都應繼承此類別。
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction],
        public_info: Optional[PublicInfo] = None,
    ) -> Tuple[GameAction, Optional[Tile]]:
        """
        決定下一步動作。

        Args:
            game_state (GameState): 當前遊戲狀態。
            player_index (int): 玩家索引 (0-3)。
            hand (Hand): 玩家手牌。
            available_actions (List[GameAction]): 可執行的動作列表。
            public_info (Optional[PublicInfo]): 公開遊戲資訊（捨牌、副露等）。

        Returns:
            Tuple[GameAction, Optional[Tile]]: (選擇的動作, 相關的牌)。
                - 如果動作是 DISCARD，Tile 是要打出的牌。
                - 如果動作是 CHI/PON/KAN，Tile 是相關的牌（通常是 target tile）。
                - 其他動作 Tile 通常為 None。
        """
        pass


class RandomPlayer(BasePlayer):
    """
    隨機行動的 AI 玩家。

    策略完全隨機，僅在必要時遵守規則（如立直後只能切摸到的牌）。
    """

    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction],
        public_info: Optional[PublicInfo] = None,
    ) -> Tuple[GameAction, Optional[Tile]]:
        """
        決定下一步動作（隨機）。

        Args:
            game_state (GameState): 當前遊戲狀態。
            player_index (int): 玩家索引。
            hand (Hand): 玩家手牌。
            available_actions (List[GameAction]): 可執行的動作列表。

        Returns:
            Tuple[GameAction, Optional[Tile]]: (選擇的動作, 相關的牌)。
        """

        if not available_actions:
            return GameAction.PASS, None

        # 簡單策略：優先和牌，其次立直，否則隨機

        # 如果可以和牌，優先和牌
        if GameAction.RON in available_actions:
            return GameAction.RON, None
        if GameAction.TSUMO in available_actions:
            return GameAction.TSUMO, None

        # 隨機選擇一個動作，過濾掉 PASS (除非只有 PASS)

        # 為了避免死循環或卡住，優先選擇 DISCARD
        if GameAction.DISCARD in available_actions:
            # 隨機打出一張牌

            if hand.is_riichi:
                # 立直後只能打出剛摸到的牌
                tile_to_discard = hand.last_drawn_tile
                if tile_to_discard is None:
                    # Should not happen if we just drew a tile, but fallback to last tile just in case
                    tile_to_discard = hand.tiles[-1]
                return GameAction.DISCARD, tile_to_discard

            tile_to_discard = random.choice(hand.tiles)
            return GameAction.DISCARD, tile_to_discard

        # 如果是回應階段，隨機選擇，但 PASS 權重高一點
        action = random.choice(available_actions)

        if action == GameAction.RICHI:
            valid_discards = hand.tenpai_discards
            if valid_discards:
                return GameAction.RICHI, random.choice(valid_discards)
            else:
                # Should not happen if RICHI is in available_actions
                return GameAction.PASS, None

        # 如果選了需要參數的動作，暫時返回 None

        return action, None


class SimplePlayer(BasePlayer):
    """
    簡單進攻 AI (Simple Attack AI)。

    策略：
    1. 優先和牌 (RON/TSUMO)。
    2. 優先立直 (RICHI)。
    3. 簡單切牌策略：字牌 -> 老頭牌 -> 中張牌。
    """

    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction],
        public_info: Optional[PublicInfo] = None,
    ) -> Tuple[GameAction, Optional[Tile]]:
        """
        決定下一步動作（簡單進攻策略）。

        Args:
            game_state (GameState): 當前遊戲狀態。
            player_index (int): 玩家索引。
            hand (Hand): 玩家手牌。
            available_actions (List[GameAction]): 可執行的動作列表。

        Returns:
            Tuple[GameAction, Optional[Tile]]: (選擇的動作, 相關的牌)。
        """

        if not available_actions:
            return GameAction.PASS, None

        # 1. 優先和牌
        if GameAction.RON in available_actions:
            return GameAction.RON, None
        if GameAction.TSUMO in available_actions:
            return GameAction.TSUMO, None

        # 2. 優先立直
        if GameAction.RICHI in available_actions:
            valid_discards = hand.tenpai_discards
            if valid_discards:
                # 從可立直的捨牌中選擇一張最好的
                best_riichi_discard = self._choose_best_discard(hand, valid_discards)
                return GameAction.RICHI, best_riichi_discard

        # 3. 處理切牌
        if GameAction.DISCARD in available_actions:
            # 如果立直中，只能打出剛摸到的牌
            if hand.is_riichi:
                tile_to_discard = hand.last_drawn_tile
                if tile_to_discard is None:
                    tile_to_discard = hand.tiles[-1]
                return GameAction.DISCARD, tile_to_discard

            # 簡單切牌策略：字牌 -> 老頭牌 -> 中張牌 (孤張優先)
            best_discard = self._choose_best_discard(hand)
            return GameAction.DISCARD, best_discard

        # 4. 處理鳴牌
        if GameAction.PASS in available_actions:
            return GameAction.PASS, None

        return random.choice(available_actions), None

    def _choose_best_discard(
        self, hand: Hand, candidates: Optional[List[Tile]] = None
    ) -> Tile:
        """
        選擇最佳捨牌。

        Args:
            hand (Hand): 手牌。
            candidates (Optional[List[Tile]]): 候選牌列表。如果為 None，則從手牌中選擇。

        Returns:
            Tile: 最佳捨牌。
        """
        tiles_to_consider = candidates if candidates is not None else hand.tiles

        best_discard = None
        min_score = 1000

        for tile in tiles_to_consider:
            score = 0

            if tile.is_honor:
                score = 10

            elif tile.is_terminal:
                score = 20

            else:
                score = 30 + (
                    5 - abs(tile.rank - 5)
                )  # 5是最高分(35)，1/9是26(但已被terminal捕獲)

            # 增加隨機性
            score += random.randint(0, 5)

            if score < min_score:
                min_score = score
                best_discard = tile

        return best_discard


class DefensivePlayer(SimplePlayer):
    """
    防守型 AI (Defensive AI)。

    策略：
    1. 默認使用 SimplePlayer 的進攻策略。
    2. 當有對手立直時，進入防守模式：
       - 優先打出立直家的現物（Genbutsu）。
       - 如果沒有現物，嘗試打出字牌或筋牌（暫時只實現現物）。
       - 棄和（Betaori）：不進行副露。
    """

    def decide_action(
        self,
        game_state: GameState,
        player_index: int,
        hand: Hand,
        available_actions: List[GameAction],
        public_info: Optional[PublicInfo] = None,
    ) -> Tuple[GameAction, Optional[Tile]]:
        """
        決定下一步動作（帶防守邏輯）。
        """
        if not available_actions:
            return GameAction.PASS, None

        # 檢查是否需要防守
        is_defense_mode = False
        threatening_players = []

        if public_info:
            for i in public_info.riichi_players:
                if i != player_index:
                    is_defense_mode = True
                    threatening_players.append(i)

        # 如果不需要防守，使用簡單策略
        if not is_defense_mode:
            return super().decide_action(
                game_state, player_index, hand, available_actions, public_info
            )

        # 防守模式

        # 1. 能夠和牌還是要和 (追立直/兜牌的情況，或者運氣好)
        if GameAction.RON in available_actions:
            return GameAction.RON, None
        if GameAction.TSUMO in available_actions:
            return GameAction.TSUMO, None

        # 2. 棄和：不立直，不副露
        if GameAction.DISCARD in available_actions:
            # 尋找安牌
            safe_tile = self._find_safe_tile(hand, public_info, threatening_players)
            if safe_tile:
                return GameAction.DISCARD, safe_tile

            # 如果沒有完全安牌，回退到 SimplePlayer 的切牌邏輯 (至少會切字牌/老頭牌)
            # 但我們希望它更保守，這裡暫時直接調用父類
            return super().decide_action(
                game_state, player_index, hand, available_actions, public_info
            )

        # 對於副露請求，一律拒絕 (PASS)
        if GameAction.PASS in available_actions:
            return GameAction.PASS, None

        return GameAction.PASS, None

    def _find_safe_tile(
        self,
        hand: Hand,
        public_info: Optional[PublicInfo],
        threatening_players: List[int],
    ) -> Optional[Tile]:
        """尋找手牌中的安牌（現物）。"""
        if not public_info:
            return None

        # 收集所有威脅玩家的現物

        # 這裡簡化處理：只要是任何一個立直家的現物，就認為是"相對"安全的
        # 更嚴格的防守應該是針對所有立直家的共通安牌 (Common Safe Tiles)
        # 但如果無法兼顧，優先防守下家/對家/上家? 或者隨機?
        # 這裡先取交集（針對所有立直家都安全），如果沒有則取聯集（針對至少一人安全）

        common_safe_tiles = None

        for player_idx in threatening_players:
            discards = public_info.discards.get(player_idx, [])
            player_safe_tiles = set(discards)

            if common_safe_tiles is None:
                common_safe_tiles = player_safe_tiles
            else:
                common_safe_tiles = common_safe_tiles.intersection(player_safe_tiles)

        # 檢查手牌中是否有共通安牌
        if common_safe_tiles:
            for tile in hand.tiles:
                if tile in common_safe_tiles:
                    return tile

        # 如果沒有共通安牌，嘗試找針對某個立直家的安牌 (避免放銃給最危險的?)
        # 暫時隨機選一個針對某人的安牌
        all_safe_tiles = set()
        for player_idx in threatening_players:
            all_safe_tiles.update(public_info.discards.get(player_idx, []))

        for tile in hand.tiles:
            if tile in all_safe_tiles:
                return tile

        return None
