"""
規則引擎 - RuleEngine implementation

提供遊戲流程控制、動作執行和規則判定功能。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from pyriichi.enum_utils import TranslatableEnum
from pyriichi.game_state import GameState, Wind
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.scoring import ScoreCalculator, ScoreResult
from pyriichi.tiles import Suit, Tile, TileSet
from pyriichi.yaku import Yaku, YakuChecker, YakuResult


class GameAction(TranslatableEnum):
    """遊戲動作"""

    DRAW = ("draw", "摸牌", "ツモ", "Draw")
    DISCARD = ("discard", "打牌", "捨て牌", "Discard")
    CHI = ("chi", "吃牌", "チー", "Chi")
    PON = ("pon", "碰牌", "ポン", "Pon")
    KAN = ("kan", "明槓", "カン", "Kan")
    ANKAN = ("ankan", "暗槓", "暗槓", "Ankan")
    RICHI = ("riichi", "立直", "リーチ", "Riichi")
    TSUMO = ("tsumo", "自摸", "ツモ", "Tsumo")
    RON = ("ron", "榮和", "ロン", "Ron")
    KYUUSHU_KYUUHAI = ("kyuushu_kyuuhai", "九種九牌", "九種九牌", "Kyuushu Kyuuhai")
    PASS = ("pass", "過", "パス", "Pass")


class GamePhase(TranslatableEnum):
    """遊戲階段"""

    INIT = ("init", "初始化", "初期化", "Init")
    DEALING = ("dealing", "發牌", "配牌", "Dealing")
    PLAYING = ("playing", "對局中", "対局中", "Playing")
    WINNING = ("winning", "和牌處理", "和了処理", "Winning")
    RYUUKYOKU = ("ryuukyoku", "流局", "流局", "Ryuukyoku")
    ENDED = ("ended", "結束", "終了", "Ended")


class RyuukyokuType(TranslatableEnum):
    """流局類型"""

    SUUFON_RENDA = ("suufon_renda", "四風連打", "四風連打", "Suufon Renda")
    SANCHA_RON = ("sancha_ron", "三家和了", "三家和了", "Sancha Ron")
    SUUKANTSU = ("suukantsu", "四槓散了", "四槓散了", "Suukantsu")
    EXHAUSTED = ("exhausted", "牌山耗盡", "牌山が尽きる", "Exhausted Wall")
    SUUCHA_RIICHI = ("suucha_riichi", "四家立直", "四家立直", "Suucha Riichi")
    KYUUSHU_KYUUHAI = ("kyuushu_kyuuhai", "九種九牌", "九種九牌", "Kyuushu Kyuuhai")


@dataclass
class WinResult:
    """和牌結果"""

    win: bool
    player: int
    yaku: List[YakuResult]
    han: int
    fu: int
    points: int
    score_result: ScoreResult
    chankan: Optional[bool] = None
    rinshan: Optional[bool] = None


@dataclass
class RyuukyokuResult:
    """流局結果"""

    ryuukyoku: bool
    ryuukyoku_type: Optional[RyuukyokuType] = None
    flow_mangan_players: List[int] = field(default_factory=list)
    kyuushu_kyuuhai_player: Optional[int] = None


@dataclass
class ActionResult:
    """動作執行結果"""

    success: bool = True
    phase: Optional[GamePhase] = None
    drawn_tile: Optional[Tile] = None
    is_last_tile: Optional[bool] = None
    ryuukyoku: Optional[RyuukyokuResult] = None
    discarded: Optional[bool] = None
    riichi: Optional[bool] = None
    chankan: Optional[bool] = None
    winners: List[int] = field(default_factory=list)
    rinshan_tile: Optional[Tile] = None
    kan: Optional[bool] = None
    ankan: Optional[bool] = None
    rinshan_win: Optional[WinResult] = None
    win_results: Dict[int, WinResult] = field(default_factory=dict)
    meld: Optional[Meld] = None
    called_action: Optional[GameAction] = None
    called_tile: Optional[Tile] = None
    waiting_for: Dict[int, List[GameAction]] = field(default_factory=dict)


class RuleEngine:
    """規則引擎"""

    def __init__(self, num_players: int = 4):
        """
        初始化規則引擎。

        Args:
            num_players (int): 玩家數量（默認 4）。
        """
        self._num_players = num_players
        self._tile_set: Optional[TileSet] = None
        self._hands: List[Hand] = []
        self._current_player = 0
        self._phase = GamePhase.INIT
        self._game_state = GameState(num_players=num_players)
        self._yaku_checker = YakuChecker()
        self._score_calculator = ScoreCalculator()
        self._last_discarded_tile: Optional[Tile] = None
        self._last_discarded_player: Optional[int] = None
        self._last_drawn_tile: Optional[Tuple[int, Tile]] = None

        self._is_first_round: bool = True
        self._discard_history: List[Tuple[int, Tile]] = []
        self._kan_count: int = 0
        self._turn_count: int = 0
        self._is_first_turn_after_deal: bool = True
        self._pending_kan_tile: Optional[Tuple[int, Tile]] = None
        self._winning_players: List[int] = []
        self._ignore_suukantsu: bool = False

        # 振聽狀態追蹤
        self._furiten_permanent: Dict[int, bool] = {}  # 立直振聽（永久）
        self._furiten_temp: Dict[int, bool] = {}  # 同巡振聽（臨時）
        self._furiten_temp_round: Dict[int, int] = {}  # 同巡振聽發生的回合

        self._pao_daisangen: Dict[int, int] = {}
        self._pao_daisuushi: Dict[int, int] = {}

        self._action_handlers = {
            GameAction.DRAW: self._handle_draw,
            GameAction.DISCARD: self._handle_discard,
            GameAction.PON: self._handle_pon,
            GameAction.CHI: self._handle_chi,
            GameAction.RICHI: self._handle_riichi,
            GameAction.KAN: self._handle_kan,
            GameAction.ANKAN: self._handle_ankan,
            GameAction.TSUMO: self._handle_tsumo,
            GameAction.RON: self._handle_ron,
            GameAction.KYUUSHU_KYUUHAI: self._handle_kyuushu_kyuuhai,
            GameAction.PASS: self._handle_pass,
        }

        self._waiting_for_actions: Dict[int, List[GameAction]] = {}
        self._incoming_actions: Dict[int, Tuple[GameAction, Optional[Tile], Dict]] = {}
        self._riichi_ippatsu: Dict[int, bool] = {}
        self._riichi_ippatsu_discard: Dict[int, int] = {}

    def _handle_pass(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        """
        處理 PASS 動作。

        PASS 動作通常由 execute_action 在 waiting 狀態下攔截處理。
        如果直接調用此方法，表示在非等待狀態下調用，這通常是不允許的，
        除非有特殊的 PASS 邏輯（目前沒有）。
        """
        return ActionResult(success=True)

    def start_game(self) -> None:
        """開始新遊戲。"""
        self._game_state = GameState(num_players=self._num_players)
        self._phase = GamePhase.INIT

    def start_round(self) -> None:
        """開始新一局。"""
        self._tile_set = TileSet()
        self._tile_set.shuffle()
        self._phase = GamePhase.DEALING
        self._current_player = self._game_state.dealer
        self._last_discarded_tile = None
        self._last_discarded_player = None

        self._riichi_ippatsu = {}
        self._riichi_ippatsu_discard = {}
        self._is_first_round = True
        self._discard_history = []
        self._kan_count = 0
        self._turn_count = 0
        self._is_first_turn_after_deal = True
        self._pending_kan_tile = None
        self._winning_players = []
        self._ignore_suukantsu = False

        # Reset hands last drawn tile
        for hand in self._hands:
            hand.reset_last_drawn_tile()

        self._furiten_permanent = {}
        self._furiten_temp = {}
        self._furiten_temp_round = {}
        self._pao_daisangen = {}
        self._pao_daisangen = {}
        self._pao_daisuushi = {}

        # 流局滿貫追蹤：記錄玩家的捨牌是否被鳴牌
        self._has_called_discard = {i: False for i in range(self._num_players)}

    def deal(self) -> Dict[int, List[Tile]]:
        """
        發牌。

        Returns:
            Dict[int, List[Tile]]: 每個玩家的手牌字典 {player_id: [tiles]}。

        Raises:
            ValueError: 如果不在發牌階段或牌組未初始化。
        """
        if self._phase != GamePhase.DEALING:
            raise ValueError("只能在發牌階段發牌")

        if not self._tile_set:
            raise ValueError("牌組未初始化")
        hands_tiles = self._tile_set.deal(num_players=self._num_players)
        self._hands = [Hand(tiles) for tiles in hands_tiles]

        self._phase = GamePhase.PLAYING
        self._is_first_turn_after_deal = True

        # 設置莊家等待動作
        dealer = self._game_state.dealer
        actions = self._calculate_turn_actions(dealer)
        self._waiting_for_actions = {dealer: actions}

        return {i: hand.tiles for i, hand in enumerate(self._hands)}

    def get_current_player(self) -> int:
        """
        獲取當前行動玩家。

        Returns:
            int: 當前玩家位置。
        """
        return self._current_player

    def get_last_discard_player(self) -> Optional[int]:
        """獲取最後捨牌的玩家。"""
        return self._last_discarded_player

    def get_phase(self) -> GamePhase:
        """
        獲取當前遊戲階段。

        Returns:
            GamePhase: 當前遊戲階段。
        """
        return self._phase

    @property
    def game_state(self) -> GameState:
        """
        獲取遊戲狀態。

        Returns:
            GameState: 遊戲狀態對象。
        """
        return self._game_state

    @property
    def waiting_for_actions(self) -> Dict[int, List[GameAction]]:
        """獲取當前等待執行的動作"""
        return self._waiting_for_actions

    @property
    def tileset(self) -> Optional[TileSet]:
        """獲取牌組對象"""
        return self._tile_set

    def _calculate_turn_actions(self, player: int) -> List[GameAction]:
        """計算玩家回合內的可執行動作"""
        actions: List[GameAction] = []

        if self._can_discard(player):
            actions.append(GameAction.DISCARD)

        if self._can_riichi(player):
            actions.append(GameAction.RICHI)

        if self._can_kan(player):
            actions.append(GameAction.KAN)

        if self._can_ankan(player):
            actions.append(GameAction.ANKAN)

        if self._can_tsumo(player):
            actions.append(GameAction.TSUMO)

        if self._check_kyuushu_kyuuhai(player):
            actions.append(GameAction.KYUUSHU_KYUUHAI)

        return actions

    def get_available_actions(self, player: int) -> List[GameAction]:
        """
        取得指定玩家當前可執行的動作列表。

        Args:
            player (int): 玩家位置。

        Returns:
            List[GameAction]: 可執行的動作列表。
        """
        if self._phase != GamePhase.PLAYING:
            return []

        if not (0 <= player < len(self._hands)):
            return []

        # 如果處於等待狀態 (現在包含了回合內動作)
        if self._waiting_for_actions:
            return self._waiting_for_actions.get(player, [])

        return []

    def _can_draw(self, player: int) -> bool:
        if player != self._current_player:
            return False
        hand = self._hands[player]
        return hand.total_tile_count() < 14

    def _can_discard(self, player: int) -> bool:
        if player != self._current_player:
            return False
        hand = self._hands[player]
        if not hand.tiles:
            return False
        return hand.total_tile_count() > 0

    def _can_pon(self, player: int) -> bool:
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return False
        if player == self._last_discarded_player:
            return False
        hand = self._hands[player]
        if hand.is_riichi:
            return False
        return hand.can_pon(self._last_discarded_tile)

    def _can_chi(self, player: int) -> bool:
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return False
        if (player - self._last_discarded_player) % self._num_players != 1:
            return False
        hand = self._hands[player]
        if hand.is_riichi:
            return False
        sequences = hand.can_chi(self._last_discarded_tile, from_player=0)
        return len(sequences) > 0

    def _can_riichi(self, player: int) -> bool:
        hand = self._hands[player]
        return (
            hand.is_concealed and not hand.is_riichi and len(hand.tenpai_discards) > 0
        )

    def _can_kan(self, player: int) -> bool:
        hand = self._hands[player]
        if hand.is_riichi:
            return False

        # 他家捨牌可進行大明槓
        if (
            self._last_discarded_tile is not None
            and self._last_discarded_player is not None
            and (
                self._last_discarded_player != player
                and hand.can_kan(self._last_discarded_tile)
            )
        ):
            return True

        # 自家加槓（需為當前玩家）
        if player == self._current_player:
            # 加槓：現有碰升級
            for meld in hand.can_kan(None):
                if meld.type == MeldType.KAN and meld.called_tile is not None:
                    return True

        return False

    def _can_ankan(self, player: int) -> bool:
        hand = self._hands[player]
        possible_kans = hand.can_kan(None)

        if not possible_kans:
            return False

        if not hand.is_riichi:
            return True

        # 立直後只能暗槓不改變聽牌的牌
        # 這裡需要檢查每一個可能的暗槓是否改變聽牌
        # 由於 _can_ankan 只返回 bool，只要有一個合法的暗槓即可
        # 獲取當前聽牌列表
        # 立直狀態下，基準聽牌列表是「打出剛摸到的牌」後的聽牌列表
        # 因為如果不暗槓，就必須模切
        last_drawn = hand.last_drawn_tile
        if last_drawn is None:
            return False  # Should not happen in Riichi turn

        # 暫時移除剛摸到的牌
        try:
            hand._tiles.remove(last_drawn)
        except ValueError:
            return False

        current_waits = hand.get_waiting_tiles()

        # 恢復
        hand._tiles.append(last_drawn)

        if not current_waits:
            return False  # 應該不會發生，立直必聽牌

        for meld in possible_kans:
            if meld.type != MeldType.ANKAN:
                continue

            # 模擬暗槓
            temp_hand = Hand([t for t in hand.tiles])
            temp_hand._melds = [m for m in hand.melds]
            temp_hand._is_riichi = True

            # 執行暗槓 (模擬)
            tiles_to_remove = meld.tiles
            try:
                for t in tiles_to_remove:
                    temp_hand._tiles.remove(t)
            except ValueError:
                continue

            # 添加暗槓
            temp_hand._melds.append(meld)

            # 檢查聽牌是否改變
            new_waits = temp_hand.get_waiting_tiles()

            # 比較聽牌列表
            if sorted(current_waits) == sorted(new_waits):
                return True

        return False

    def _can_tsumo(self, player: int) -> bool:
        """檢查玩家是否可以自摸"""
        if player != self._current_player:
            return False

        if self._last_drawn_tile is None:
            return False

        last_player, last_tile = self._last_drawn_tile
        if last_player != player:
            return False

        return self.check_win(player, last_tile, is_rinshan=False) is not None

    def _can_ron(self, player: int) -> bool:
        """檢查玩家是否可以榮和"""
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return False

        if player == self._last_discarded_player:
            return False  # 不能榮和自己打的牌

        winners = self.check_multiple_ron(
            self._last_discarded_tile, self._last_discarded_player
        )
        return player in winners

    def execute_action(
        self, player: int, action: GameAction, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        """
        執行動作。

        Args:
            player (int): 玩家位置。
            action (GameAction): 動作類型。
            tile (Optional[Tile]): 相關的牌。
            **kwargs: 其他參數。

        Returns:
            ActionResult: 動作執行結果。

        Raises:
            ValueError: 如果動作無效或尚未實作。
        """
        available_actions = self.get_available_actions(player)
        if action not in available_actions:
            raise ValueError(f"玩家 {player} 不能執行動作 {action}")

        handler = self._action_handlers.get(action)
        if handler is None:
            raise ValueError(f"動作 {action} 尚未實作")

        # 錯和檢測（Chombo Detection）

        # 如果處於等待狀態，收集玩家回應
        if self._waiting_for_actions:
            if player not in self._waiting_for_actions:
                raise ValueError(f"玩家 {player} 當前不需要執行動作")

            allowed_actions = self._waiting_for_actions[player]
            if action not in allowed_actions:
                raise ValueError(
                    f"玩家 {player} 不能執行動作 {action}，期待: {allowed_actions}"
                )

            # 記錄回應
            self._incoming_actions[player] = (action, tile, kwargs)

            # 如果玩家錯過榮和（有榮和機會但選擇 PASS 或其他動作），設置同巡振聽
            if GameAction.RON in allowed_actions and action != GameAction.RON:
                self._furiten_temp[player] = True
                self._furiten_temp_round[player] = self._turn_count
            del self._waiting_for_actions[player]

            # 如果所有玩家都已回應，進行裁決
            if not self._waiting_for_actions:
                return self._resolve_decisions()
            else:
                # 等待其他玩家
                return ActionResult(success=True)

        # 非等待狀態，直接執行（例如自摸、暗槓、打牌）
        return handler(player, tile=tile, **kwargs)

    def _resolve_decisions(self) -> ActionResult:
        """裁決所有玩家的回應，執行優先級最高的動作"""
        # 優先級: 榮和 > 碰/槓 > 吃 > PASS

        actions = self._incoming_actions
        self._incoming_actions = {}  # 清空

        # 0. 檢查當前玩家的行動 (打牌/自摸/暗槓/立直)
        # 這種情況下，_waiting_for_actions 應該只包含當前玩家
        # 且 actions 中應該只有一個條目
        if len(actions) == 1:
            player = list(actions.keys())[0]
            action, tile, kwargs = actions[player]

            # 如果是當前玩家的行動 (非中斷)
            if player == self._current_player and action not in (
                GameAction.RON,
                GameAction.PON,
                GameAction.CHI,
                GameAction.PASS,
            ):
                # 執行對應的 handler
                handler = self._action_handlers.get(action)
                if handler:
                    return handler(player, tile, **kwargs)
                else:
                    raise ValueError(f"Action {action} not implemented")

        # 1. 檢查榮和
        ron_players = [p for p, (a, _, _) in actions.items() if a == GameAction.RON]
        if ron_players:
            # 執行榮和（處理多人榮和）
            # 注意：如果有多個榮和，需要依序處理
            # 如果是雙響，我們應該一次性設置?

            # 使用 check_multiple_ron 獲取真正的贏家（考慮頭跳）
            if self._last_discarded_tile is None or self._last_discarded_player is None:
                raise ValueError("無法執行榮和：無捨牌")

            real_winners = self.check_multiple_ron(
                self._last_discarded_tile, self._last_discarded_player
            )

            # 過濾掉不在 real_winners 中的玩家（例如被頭跳截胡的）
            valid_ron_players = [p for p in ron_players if p in real_winners]

            if not valid_ron_players:
                # 應該不會發生，除非邏輯錯誤
                return ActionResult(success=False)

            # 執行榮和
            # 我們可以對第一個贏家調用 _handle_ron，並手動添加其他贏家?
            # 或者 _handle_ron 應該被重構以支持多贏家?
            # 目前 _handle_ron 內部調用 check_win 並設置 result.winners = [player]
            # 我們需要一個能處理多贏家的 _handle_ron_multiple

            return self._handle_ron_multiple(valid_ron_players)

        # 2. 檢查碰/槓
        pon_kan_players = [
            p
            for p, (a, _, _) in actions.items()
            if a in (GameAction.PON, GameAction.KAN)
        ]
        if pon_kan_players:
            # 只有一個玩家可以碰/槓（除了特殊規則，但通常只有一張捨牌）
            # 如果有多個（不可能，除非牌山有誤），取第一個
            player = pon_kan_players[0]
            action, tile, kwargs = actions[player]
            if action == GameAction.PON:
                return self._handle_pon(player, tile, **kwargs)
            else:
                return self._handle_kan(player, tile, **kwargs)  # 這裡是明槓

        # 3. 檢查吃
        chi_players = [p for p, (a, _, _) in actions.items() if a == GameAction.CHI]
        if chi_players:
            player = chi_players[0]
            action, tile, kwargs = actions[player]
            return self._handle_chi(player, tile, **kwargs)

        # 4. 全部 PASS
        # 推進回合
        result = ActionResult()
        self._advance_turn(result)
        return result

    def _handle_ron_multiple(self, winners: List[int]) -> ActionResult:
        """處理多人榮和"""
        result = ActionResult()
        result.winners = winners
        result.win_results = {}

        tile = self._last_discarded_tile
        if tile is None:
            raise ValueError("無捨牌")

        for player in winners:
            win_res = self.check_win(player, tile, is_rinshan=False)  # 榮和非嶺上
            if win_res:
                result.win_results[player] = win_res

        # 處理分數結算（這裡簡化，直接結束）
        # 實際應調用 _process_win_scoring 等
        # 為了保持兼容性，我們調用 _handle_ron 對第一個玩家，然後補全?
        # 不，直接設置狀態
        self._phase = GamePhase.WINNING  # 或 ENDED
        # 這裡需要完整的結算邏輯，暫時復用 _handle_ron 的部分邏輯
        # 但 _handle_ron 只處理單人。
        # 我們假設 demo_ui 會處理 result.win_results

        # 更新分數
        # 注意：多贏家時，供託（立直棒）的分配需根據規則配置（通常給頭跳或平分）
        # 這裡簡化：每個贏家都計算分數，從放銃者扣除。

        loser = self._last_discarded_player

        for player in winners:
            win_res = result.win_results[player]
            points = win_res.points
            # 簡單扣分
            self._game_state.update_score(loser, -points)
            self._game_state.update_score(player, points)

        # 處理立直棒歸屬 (給第一個贏家)
        if self._game_state.riichi_sticks > 0:
            first_winner = winners[0]  # 按順序? check_multiple_ron 返回順序?
            # 假設 check_multiple_ron 按逆時針順序
            self._game_state.update_score(
                first_winner, self._game_state.riichi_sticks * 1000
            )
            self._game_state.clear_riichi_sticks()

        # 本場棒 (Honba) - 通常每個贏家都加? 還是只有第一個?
        # 標準規則：頭跳才有本場。雙響時，通常都加? 或者只有第一個?
        # 天鳳：雙響都加本場費。
        # 這裡暫不處理複雜本場邏輯，假設已在 check_win 計算 (check_win 會包含本場費嗎? 通常會)

        return result

    def _handle_draw(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        result = ActionResult()
        # 檢查手牌數量
        hand = self._hands[player]
        if not self._tile_set:
            raise ValueError("牌組未初始化")

        # 計算槓的數量（每個槓增加 1 張手牌上限）
        kan_count = sum(
            1 for meld in hand.melds if meld.type in [MeldType.KAN, MeldType.ANKAN]
        )
        limit = 14 + kan_count

        if hand.total_tile_count() >= limit:
            raise ValueError(f"手牌已達 {limit} 張，不能再摸牌")
        # 摸牌
        drawn_tile = self._tile_set.draw()
        if drawn_tile:
            hand.add_tile(drawn_tile)
            result.drawn_tile = drawn_tile
        if self._tile_set.is_exhausted():
            result.is_last_tile = True

        # 計算並設置等待動作
        actions = self._calculate_turn_actions(player)
        self._waiting_for_actions = {player: actions}
        result.waiting_for = self._waiting_for_actions
        if not drawn_tile:
            self._phase = GamePhase.RYUUKYOKU
            result.ryuukyoku = RyuukyokuResult(
                ryuukyoku=True, ryuukyoku_type=RyuukyokuType.EXHAUSTED
            )
        return result

    def _check_interrupts(
        self, tile: Tile, discarded_player: int
    ) -> Dict[int, List[GameAction]]:
        """檢查是否有玩家可以對打出的牌進行鳴牌或榮和"""
        interrupts = {}

        # 檢查榮和 (Ron) - 所有其他玩家
        # 檢查鳴牌 (Pon/Kan) - 所有其他玩家
        # 檢查吃牌 (Chi) - 僅下家

        for i in range(self._num_players):
            if i == discarded_player:
                continue

            actions = []

            # 榮和
            if self._can_ron(i):
                actions.append(GameAction.RON)

            # 碰/槓
            if self._can_pon(i):
                actions.append(GameAction.PON)
            if self._can_kan(i):
                actions.append(GameAction.KAN)

            # 吃 (僅下家)
            if (
                (i - discarded_player) % self._num_players != 1
            ):  # Changed from == 1 to != 1 to match _can_chi logic
                pass  # Skip if not next player
            else:
                if self._can_chi(i):
                    actions.append(GameAction.CHI)

            if actions:
                # 如果有動作，必須包含 PASS 選項
                actions.append(GameAction.PASS)
                interrupts[i] = actions

        return interrupts

    def _handle_discard(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        result = ActionResult()
        if tile is None:
            raise ValueError("打牌動作必須指定牌")
        if not self._tile_set:
            raise ValueError("牌組未初始化")

        hand = self._hands[player]

        # 立直後只能打出剛摸到的牌 (除非是暗槓，但暗槓在 _handle_kan 處理)
        if hand.is_riichi:
            if hand.last_drawn_tile and tile != hand.last_drawn_tile:
                raise ValueError("立直後只能打出剛摸到的牌")

        if hand.discard(tile):
            # 記錄打牌並處理相關效果（但不推進回合）
            self._last_discarded_tile = tile
            self._last_discarded_player = player
            self._discard_history.append((player, tile))
            if len(self._discard_history) > 4:
                self._discard_history.pop(0)

            if self._riichi_ippatsu and player in self._riichi_ippatsu:
                if self._riichi_ippatsu_discard.get(player) == 1:
                    self._riichi_ippatsu[player] = False
                self._riichi_ippatsu_discard[player] += 1

            if self._tile_set.is_exhausted():
                result.is_last_tile = True

            result.discarded = True
            hand.reset_last_drawn_tile()  # 打牌後清除最後摸的牌

            # 檢查其他玩家是否可以鳴牌或榮和
            interrupts = self._check_interrupts(tile, player)

            if interrupts:
                # 進入等待狀態
                self._waiting_for_actions = interrupts
                result.waiting_for = interrupts
            else:
                # 無人鳴牌，推進回合並自動摸牌
                self._advance_turn(result)

        return result

    def _advance_turn(self, result: ActionResult) -> None:
        """推進回合並自動摸牌"""
        self._current_player = (self._current_player + 1) % self._num_players
        self._turn_count += 1
        self._is_first_turn_after_deal = False
        self._is_first_round = False

        # 自動摸牌
        draw_result = self._handle_draw(self._current_player)
        if draw_result.drawn_tile:
            result.drawn_tile = draw_result.drawn_tile
            if draw_result.waiting_for:
                result.waiting_for = draw_result.waiting_for
        elif draw_result.ryuukyoku:
            result.ryuukyoku = draw_result.ryuukyoku
            self._phase = GamePhase.RYUUKYOKU

    def _handle_pon(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        result = ActionResult()
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            raise ValueError("沒有可碰的捨牌")
        if player == self._last_discarded_player:
            raise ValueError("不能碰自己打出的牌")

        tile_to_claim = self._last_discarded_tile
        hand = self._hands[player]
        if not hand.can_pon(tile_to_claim):
            raise ValueError("手牌無法碰這張牌")

        discarder = self._last_discarded_player
        self._remove_last_discard(discarder, tile_to_claim)

        meld = hand.pon(tile_to_claim)
        result.meld = meld
        result.called_action = GameAction.PON
        result.called_tile = tile_to_claim

        self._interrupt_ippatsu(GameAction.PON, acting_player=player)

        self._current_player = player
        self._last_discarded_tile = None
        self._last_discarded_player = None
        self._is_first_turn_after_deal = False
        hand.reset_last_drawn_tile()  # 鳴牌後清除最後摸的牌

        # 鳴牌後必須打牌
        self._waiting_for_actions = {player: [GameAction.DISCARD]}
        result.waiting_for = self._waiting_for_actions
        return result

    def _handle_chi(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        result = ActionResult()
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            raise ValueError("沒有可吃的捨牌")
        if (player - self._last_discarded_player) % self._num_players != 1:
            raise ValueError("只能吃上家的牌")

        tile_to_claim = self._last_discarded_tile
        hand = self._hands[player]
        sequences = hand.can_chi(tile_to_claim, from_player=0)
        if not sequences:
            raise ValueError("手牌無法吃這張牌")

        sequence = kwargs.get("sequence")
        if sequence is None:
            sequence = sequences[0]
        elif sequence not in sequences:
            raise ValueError("提供的順子無效")

        discarder = self._last_discarded_player
        self._remove_last_discard(discarder, tile_to_claim)

        meld = hand.chi(tile_to_claim, sequence)
        result.meld = meld
        result.called_action = GameAction.CHI
        result.called_tile = tile_to_claim

        self._interrupt_ippatsu(GameAction.CHI, acting_player=player)

        self._current_player = player
        self._last_discarded_tile = None
        self._last_discarded_player = None
        self._is_first_turn_after_deal = False
        hand.reset_last_drawn_tile()  # 鳴牌後清除最後摸的牌

        # 鳴牌後必須打牌
        self._waiting_for_actions = {player: [GameAction.DISCARD]}
        result.waiting_for = self._waiting_for_actions
        return result

    def _handle_riichi(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        if tile is None:
            raise ValueError("立直必須同時打出一張牌")

        hand = self._hands[player]

        # 檢查打出這張牌後是否聽牌
        # 模擬打牌
        try:
            hand._tiles.remove(tile)
        except ValueError:
            raise ValueError("手牌中沒有這張牌")

        hand._tile_counts_cache = None
        is_tenpai = hand.is_tenpai()

        # 恢復手牌
        hand._tiles.append(tile)
        hand._tile_counts_cache = None

        if not is_tenpai:
            raise ValueError("立直打牌後必須聽牌")

        # 執行打牌
        # 注意：這裡直接調用 _handle_discard，它會處理打牌邏輯和後續流程
        discard_result = self._handle_discard(player, tile, **kwargs)

        # 執行立直
        hand.set_riichi(True)
        self._game_state.add_riichi_stick()
        self._game_state.update_score(player, -1000)
        self._riichi_ippatsu[player] = True
        self._riichi_ippatsu_discard[player] = 0

        # 合併結果
        discard_result.riichi = True
        return discard_result

    def _handle_kan(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        result = ActionResult()
        hand = self._hands[player]

        # If tile is None, try to use last discarded tile (Daiminkan)
        if tile is None:
            if self._last_discarded_tile is None:
                raise ValueError("明槓必須指定被槓的牌")
            tile = self._last_discarded_tile

        # Check if it's a Daiminkan (Open Kan) on discard
        # Must be an interrupt (player != current_player)
        if (
            self._last_discarded_tile
            and tile == self._last_discarded_tile
            and player != self._current_player
        ):
            # Remove from discarder
            if self._last_discarded_player is not None:
                self._remove_last_discard(self._last_discarded_player, tile)

            # Clear last discard state
            self._last_discarded_tile = None
            self._last_discarded_player = None

        meld = hand.kan(tile)
        self._kan_count += 1
        result.kan = True
        hand.reset_last_drawn_tile()  # 槓牌後清除最後摸的牌
        self._current_player = player

        self._interrupt_ippatsu(GameAction.KAN, acting_player=player)

        if self._draw_rinshan_tile(player, result, kan_type=meld.type):
            self._pending_kan_tile = None

        return result

    def _handle_ankan(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        result = ActionResult()
        hand = self._hands[player]

        candidates = hand.can_kan(None)
        if not candidates:
            raise ValueError("手牌無法暗槓")

        # 支援多個暗槓選擇
        selected = None
        if tile:
            for candidate in candidates:
                # 檢查候選是否匹配指定的牌
                # 暗槓/加槓的牌都是相同的，所以檢查第一張即可
                if (
                    candidate.tiles
                    and candidate.tiles[0].suit == tile.suit
                    and candidate.tiles[0].rank == tile.rank
                ):
                    selected = candidate
                    break

            if selected is None:
                raise ValueError(f"無法暗槓指定的牌: {tile}")
        else:
            # 如果未指定，且有多個選擇，默認選第一個（或應拋出歧義錯誤）
            selected = candidates[0]
        is_add_kan = selected.type == MeldType.KAN and selected.called_tile is not None

        if is_add_kan:
            kan_tile = selected.tiles[0]
            self._pending_kan_tile = (player, kan_tile)
            if chankan_winners := self._check_chankan(player, kan_tile):
                result.chankan = True
                result.winners = chankan_winners
                self._pending_kan_tile = None
                return result

        # 使用選定的牌進行槓
        meld = hand.kan(selected.tiles[0])
        if meld:
            self._kan_count += 1
        kan_type = meld.type if meld else MeldType.ANKAN

        if kan_type == MeldType.ANKAN:
            result.ankan = True
        else:
            result.kan = True

        self._interrupt_ippatsu(GameAction.ANKAN, acting_player=player)

        self._draw_rinshan_tile(player, result, kan_type=kan_type)
        if self._pending_kan_tile:
            self._pending_kan_tile = None
        hand.reset_last_drawn_tile()  # 槓牌後清除最後摸的牌

        result.ankan = True
        return result

    def _handle_tsumo(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        """
        處理自摸和牌。

        Args:
            player (int): 和牌玩家。
            tile (Optional[Tile]): 和牌牌（應該是剛摸的牌）。
            **kwargs: 其他參數（如 is_rinshan）。

        Returns:
            ActionResult: 包含和牌結果的 ActionResult。

        Raises:
            ValueError: 如果無法自摸。
        """
        result = ActionResult()
        hand = self._hands[player]

        # 獲取和牌牌（應該是player剛摸的牌）
        if tile is None:
            # 使用最後摸的牌
            if hand.last_drawn_tile:
                tile = hand.last_drawn_tile
            else:
                raise ValueError("無法確定自摸的牌")

        # 檢查是否能自摸和牌
        is_rinshan = kwargs.get("is_rinshan", False)
        win_result = self.check_win(player, tile, is_rinshan=is_rinshan)

        if win_result is None:
            raise ValueError(f"玩家 {player} 無法用 {tile} 自摸和牌")

        # 應用分數變化
        self.apply_win_score(win_result)

        # 設置結果
        result.winners = [player]
        result.rinshan_win = win_result if is_rinshan else None
        result.win_results[player] = win_result

        # 切換到和牌階段
        self._phase = GamePhase.WINNING

        return result

    def _handle_ron(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        """
        處理榮和（支持多人榮和）。

        Args:
            player (int): 聲明榮和的玩家（可能是多人之一）。
            tile (Optional[Tile]): 和牌牌（應該是最後打出的牌）。
            **kwargs: 其他參數。

        Returns:
            ActionResult: 包含和牌結果的 ActionResult。

        Raises:
            ValueError: 如果無法榮和。
        """
        result = ActionResult()

        # 獲取被榮和的牌（最後打出的牌）
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            raise ValueError("沒有可榮和的捨牌")

        winning_tile = self._last_discarded_tile
        discarder = self._last_discarded_player

        # 檢查多人榮和情況
        potential_winners = self.check_multiple_ron(winning_tile, discarder)

        # 檢查是否觸發三家和了流局
        if len(potential_winners) == 0:
            # 空列表表示三家和了，觸發流局
            result.ryuukyoku = RyuukyokuResult(
                ryuukyoku=True, ryuukyoku_type=RyuukyokuType.SANCHA_RON
            )
            result.success = True
            result.phase = GamePhase.ENDED
            self._phase = GamePhase.ENDED
            return result

        # 驗證聲明榮和的玩家在允許列表中
        if player not in potential_winners:
            raise ValueError(f"玩家 {player} 不能榮和（配置限制或振聽）")

        # 處理所有贏家
        winners = potential_winners
        for winner in winners:
            win_result = self.check_win(winner, winning_tile, is_chankan=False)
            if win_result:
                self.apply_win_score(win_result)
                result.win_results[winner] = win_result

        # 設置結果
        result.winners = winners

        # 切換到和牌階段
        self._phase = GamePhase.WINNING

        return result

    def end_round(self, winners: Optional[List[int]] = None) -> None:
        """
        結束一局。

        Args:
            winners (Optional[List[int]]): 獲勝玩家列表（如果為 None，則為流局）。
                - 單人榮和/自摸：[player_id]
                - 雙響/三響：[player1, player2, player3]
        """
        if winners is not None and len(winners) > 0:
            # 和牌處理
            dealer = self._game_state.dealer
            # 如果任一贏家是莊家，則連莊
            dealer_won = dealer in winners

            # 更新莊家
            self._game_state.next_dealer(dealer_won)

            # 檢查擊飛
            if self._check_tobi():
                self._phase = GamePhase.ENDED
                return

            # 檢查安可（Agari-yame）
            # 如果莊家和牌，且啟用安可，且為最後一局（南4或西4），且莊家為第一名，則遊戲結束
            if dealer_won and self._game_state.ruleset.agari_yame:
                is_final_round = (
                    self._game_state.round_wind == Wind.SOUTH
                    and self._game_state.round_number == 4
                ) or (
                    self._game_state.round_wind == Wind.WEST
                    and self._game_state.round_number == 4
                )
                if is_final_round:
                    max_score = max(self._game_state.scores)
                    if self._game_state.scores[dealer] == max_score:
                        self._phase = GamePhase.ENDED
                        return

            # 如果莊家未獲勝，進入下一局
            if not dealer_won:
                has_next = self._game_state.next_round()
                if not has_next:
                    self._phase = GamePhase.ENDED
        else:
            # 流局處理
            # 如果是牌山耗盡流局，檢查流局滿貫和不聽罰符
            if self._tile_set and self._tile_set.is_exhausted():
                # 檢查流局滿貫
                flow_mangan_players = []
                for i in range(self._num_players):
                    if self._check_nagashi_mangan(i):
                        flow_mangan_players.append(i)

                if flow_mangan_players:
                    # 處理流局滿貫分數
                    for winner in flow_mangan_players:
                        is_dealer = winner == self._game_state.dealer
                        payment = 4000 if is_dealer else 2000

                        # 所有人支付（除了贏家）
                        for i in range(self._num_players):
                            if i == winner:
                                continue

                            # 莊家支付更多（如果贏家不是莊家）
                            pay_amount = payment
                            if not is_dealer and i == self._game_state.dealer:
                                pay_amount = 4000

                            self._game_state.update_score(i, -pay_amount)
                            self._game_state.update_score(winner, pay_amount)
                else:
                    # 如果沒有流局滿貫，才計算不聽罰符
                    self._calculate_noten_bappu()

            # 檢查擊飛
            if self._check_tobi():
                self._phase = GamePhase.ENDED
                return

            dealer_won = False  # 流局時莊家不連莊（除非九種九牌，這裡暫不處理）
            self._game_state.next_dealer(dealer_won)

            has_next = self._game_state.next_round()
            if not has_next:
                self._phase = GamePhase.ENDED

    def _handle_kyuushu_kyuuhai(
        self, player: int, tile: Optional[Tile] = None, **kwargs
    ) -> ActionResult:
        """
        處理九種九牌流局
        """
        if not self._check_kyuushu_kyuuhai(player):
            raise ValueError("不滿足九種九牌流局條件")

        result = ActionResult()
        result.ryuukyoku = RyuukyokuResult(
            ryuukyoku=True,
            ryuukyoku_type=RyuukyokuType.KYUUSHU_KYUUHAI,
            kyuushu_kyuuhai_player=player,
        )
        self._phase = GamePhase.RYUUKYOKU
        return result

    def _remove_last_discard(self, discarder: int, tile: Tile) -> None:
        self._hands[discarder].remove_last_discard(tile)
        if self._discard_history and self._discard_history[-1] == (discarder, tile):
            self._discard_history.pop()
        # 標記該玩家有捨牌被鳴牌（影響流局滿貫）
        self._has_called_discard[discarder] = True

    def _draw_rinshan_tile(
        self, player: int, result: ActionResult, *, kan_type: MeldType
    ) -> bool:
        if not self._tile_set:
            return False

        hand = self._hands[player]
        if rinshan_tile := self._tile_set.draw_rinshan():
            hand.add_tile(rinshan_tile)
            result.rinshan_tile = rinshan_tile
            if kan_type == MeldType.KAN:
                result.kan = True
            else:
                result.ankan = True

            if rinshan_win := self._check_rinshan_win(player, rinshan_tile):
                result.rinshan_win = rinshan_win
                self._ignore_suukantsu = True
                self._phase = GamePhase.WINNING
            else:
                # 計算並設置等待動作
                actions = self._calculate_turn_actions(player)
                self._waiting_for_actions = {player: actions}
                result.waiting_for = self._waiting_for_actions
            return True

        self._phase = GamePhase.RYUUKYOKU
        result.ryuukyoku = RyuukyokuResult(
            ryuukyoku=True, ryuukyoku_type=RyuukyokuType.EXHAUSTED
        )
        return False

    def _apply_discard_effects(
        self, player: int, tile: Tile, result: ActionResult
    ) -> None:
        self._last_discarded_tile = tile
        self._last_discarded_player = player
        self._discard_history.append((player, tile))
        if len(self._discard_history) > 4:
            self._discard_history.pop(0)

        if self._riichi_ippatsu and player in self._riichi_ippatsu:
            if self._riichi_ippatsu_discard.get(player) == 1:
                self._riichi_ippatsu[player] = False
            self._riichi_ippatsu_discard[player] += 1
        if self._tile_set and self._tile_set.is_exhausted():
            result.is_last_tile = True

        self._current_player = (player + 1) % self._num_players
        self._turn_count += 1
        self._is_first_turn_after_deal = False
        self._is_first_round = False
        result.discarded = True

    def check_win(
        self,
        player: int,
        winning_tile: Tile,
        is_chankan: bool = False,
        is_rinshan: bool = False,
    ) -> Optional[WinResult]:
        """
        檢查是否可以和牌。

        Args:
            player (int): 玩家位置。
            winning_tile (Tile): 和牌牌。
            is_chankan (bool): 是否為搶槓和。
            is_rinshan (bool): 是否為嶺上開花。

        Returns:
            Optional[WinResult]: 和牌結果（包含役種、得分等），如果不能和則返回 None。
        """
        hand = self._hands[player]

        last_draw = self._last_drawn_tile
        is_tsumo = is_rinshan
        if not is_tsumo and last_draw is not None:
            last_player, last_tile = last_draw
            if last_player == player and last_tile == winning_tile:
                is_tsumo = True

        if not hand.is_winning_hand(winning_tile, is_tsumo):
            return None

        # 獲取和牌組合
        combinations = hand.get_winning_combinations(winning_tile, is_tsumo)
        if not combinations:
            return None

        # 榮和時檢查振聽（振聽玩家不能榮和，但可以自摸）
        if not is_tsumo and self.is_furiten(player):
            return None

        # 判定是否符合一發
        is_ippatsu = self._riichi_ippatsu.get(player, False)

        # 檢查是否為第一巡
        is_first_turn = self._is_first_turn_after_deal
        # 檢查是否為最後一張牌（需要檢查牌山狀態）
        is_last_tile = self._tile_set.is_exhausted() if self._tile_set else False
        # 檢查是否為人和

        # 計算寶牌數量
        dora_count = self._count_dora(player, winning_tile)

        # 高點法：遍歷所有可能的和牌組合，選擇分數最高的一個
        best_score_result = None
        best_yaku_results = None
        best_winning_combination = None

        # 如果是特殊牌型（七對子、國士無雙），combinations 為空，需要檢查一次空組合
        combinations_to_check = combinations if combinations else [[]]

        for winning_combination in combinations_to_check:
            # 檢查役種
            yaku_results = self._yaku_checker.check_all(
                hand,
                winning_tile,
                winning_combination,
                self._game_state,
                is_tsumo=is_tsumo,
                is_ippatsu=is_ippatsu,
                is_first_turn=is_first_turn,
                is_last_tile=is_last_tile,
                player_position=player,
                is_rinshan=is_rinshan,
                is_chankan=is_chankan,
            )
            if not yaku_results:
                continue

            # 計算得分
            score_result = self._score_calculator.calculate(
                hand,
                winning_tile,
                winning_combination,
                yaku_results,
                dora_count,
                self._game_state,
                is_tsumo,
                player_position=player,
            )

            # 更新最高分
            if (
                best_score_result is None
                or score_result.total_points > best_score_result.total_points
            ):
                best_score_result = score_result
                best_yaku_results = yaku_results
                best_winning_combination = winning_combination
            elif score_result.total_points == best_score_result.total_points:
                # 分數相同時，選擇翻數高的
                if score_result.han > best_score_result.han:
                    best_score_result = score_result
                    best_yaku_results = yaku_results
                    best_winning_combination = winning_combination
                # 翻數也相同時，選擇符數高的
                elif (
                    score_result.han == best_score_result.han
                    and score_result.fu > best_score_result.fu
                ):
                    best_score_result = score_result
                    best_yaku_results = yaku_results
                    best_winning_combination = winning_combination
                # 如果是役滿，通常不需要繼續檢查（除非有多倍役滿規則且可能有更高倍數）
                # 但為了簡單起見，我們總是檢查所有組合

        if best_score_result is None:
            return None

        # 確定包牌者
        pao_player = None
        for result in best_yaku_results:
            if result.yaku == Yaku.DAISANGEN:
                pao_player = self._pao_daisangen.get(player)
                if pao_player is not None:
                    break
            elif result.yaku == Yaku.DAISUUSHI:
                pao_player = self._pao_daisuushi.get(player)
                if pao_player is not None:
                    break

        # 計算得分
        score_result = self._score_calculator.calculate(
            hand,
            winning_tile,
            best_winning_combination,
            best_yaku_results,
            dora_count,
            self._game_state,
            is_tsumo,
            player,
            pao_player=pao_player,
        )

        score_result.payment_to = player
        # 如果是榮和，設置支付者
        if not is_tsumo and self._last_discarded_player is not None:
            score_result.payment_from = self._last_discarded_player
        elif is_chankan and self._pending_kan_tile:
            # 搶槓和：支付者為槓牌玩家
            kan_player, _ = self._pending_kan_tile
            score_result.payment_from = kan_player

        if self._kan_count >= 4:
            self._ignore_suukantsu = True

        return WinResult(
            win=True,
            player=player,
            yaku=best_yaku_results,
            han=score_result.han,
            fu=score_result.fu,
            points=score_result.total_points,
            score_result=score_result,
            chankan=is_chankan or None,
            rinshan=is_rinshan or None,
        )

    def check_multiple_ron(self, discarded_tile: Tile, discarder: int) -> List[int]:
        """
        檢查多個玩家是否可以榮和同一張牌。

        根據配置返回可以榮和的玩家列表：
        - head_bump_only=True: 只返回下家
        - allow_double_ron=True: 最多返回2人
        - allow_triple_ron=False且檢測到3人: 返回空列表（觸發流局）
        - allow_triple_ron=True且檢測到3人: 返回3人

        Args:
            discarded_tile (Tile): 被打出的牌。
            discarder (int): 打牌者。

        Returns:
            List[int]: 可以榮和的玩家列表（按逆時針順序，下家優先）。
        """
        # 收集所有可以榮和的玩家（除了打牌者）
        potential_winners = []

        for offset in range(1, self._num_players):
            player = (discarder + offset) % self._num_players

            # 檢查此玩家是否可以榮和
            win_result = self.check_win(
                player, discarded_tile, is_chankan=False, is_rinshan=False
            )
            if win_result is not None:
                potential_winners.append(player)

        # 如果沒有人能榮和，直接返回
        if not potential_winners:
            return []

        # 如果只有一人，直接返回
        if len(potential_winners) == 1:
            return potential_winners

        # 多人可以榮和的情況，根據配置處理
        ruleset = self._game_state.ruleset

        # 首先檢查三家和了（優先級最高，因為可能觸發流局）
        if len(potential_winners) >= 3:
            # 如果禁用三響，返回空列表（將觸發三家和了流局）
            if not ruleset.allow_triple_ron:
                return []  # 觸發流局
            # 如果啟用三響，返回所有玩家（最多3人）
            return potential_winners[:3]

        # 頭跳模式：只允許下家榮和（適用於2人的情況）
        if ruleset.head_bump_only:
            # 返回第一個玩家（下家，逆時針最近）
            return [potential_winners[0]]

        # 雙響情況（2人），且 head_bump_only=False
        if len(potential_winners) == 2:
            if ruleset.allow_double_ron:
                return potential_winners
            else:
                # 禁用雙響但不是頭跳模式，返回下家
                return [potential_winners[0]]

        return potential_winners

    def _check_kyuushu_kyuuhai(self, player: int) -> bool:
        """
        檢查是否滿足九種九牌流局條件

        條件：
        1. 必須是第一巡（玩家自己的第一巡）
        2. 場上無人鳴牌（包括暗槓）
        3. 手牌有9種以上幺九牌
        """
        # 必須是自己的回合
        if player != self._current_player:
            return False

        # 必須是第一巡（自己尚未打過牌）
        if len(self._hands[player].discards) > 0:
            return False

        # 場上不能有副露（包括暗槓）
        for i in range(self._num_players):
            if len(self._hands[i].melds) > 0:
                return False

        # 手牌必須有9種以上幺九牌
        hand = self._hands[player]
        unique_yaochuu = {t for t in hand.tiles if t.is_yaochuu}
        return len(unique_yaochuu) >= 9

    def check_ryuukyoku(self) -> Optional[RyuukyokuType]:
        """
        檢查是否流局。

        Returns:
            Optional[RyuukyokuType]: 流局類型，否則返回 None。
        """
        # 檢查四風連打（優先檢查，因為可以在第一巡發生）
        if self._check_suufon_renda():
            return RyuukyokuType.SUUFON_RENDA

        # 檢查三家和了（多人和牌流局）
        if self._check_sancha_ron():
            return RyuukyokuType.SANCHA_RON

        # 檢查四槓散了（四個槓之後流局）
        if self._kan_count >= 4 and not self._ignore_suukantsu:
            return RyuukyokuType.SUUKANTSU

        # 牌山耗盡流局
        if self._tile_set and self._tile_set.is_exhausted():
            return RyuukyokuType.EXHAUSTED

        # 檢查是否所有玩家都聽牌（全員聽牌流局）
        return RyuukyokuType.SUUCHA_RIICHI if self._check_all_riichi() else None

    def _check_all_riichi(self) -> bool:
        """檢查是否所有玩家都立直"""
        if self._phase != GamePhase.PLAYING:
            return False

        return all(hand.is_riichi for hand in self._hands)

    def _check_suufon_renda(self) -> bool:
        """
        檢查是否四風連打（前四捨牌都是同一風牌）

        Returns:
            是否為四風連打
        """
        # 必須有至少4張捨牌歷史
        if len(self._discard_history) < 4:
            return False

        # 檢查前四張捨牌是否都是同一風牌
        first_tile = self._discard_history[0][1]

        # 必須是風牌（字牌 rank 1-4）
        if first_tile.suit != Suit.JIHAI or not (1 <= first_tile.rank <= 4):
            return False

        return not any(
            tile.suit != Suit.JIHAI or tile.rank != first_tile.rank
            for _, tile in self._discard_history[:4]
        )

    def _check_nagashi_mangan(self, player: int) -> bool:
        """
        檢查是否滿足流局滿貫條件

        條件：
        1. 捨牌全部是幺九牌
        2. 捨牌沒有被鳴牌（碰、吃、槓）
        """
        # 檢查是否有捨牌被鳴牌
        if self._has_called_discard[player]:
            return False

        hand = self._hands[player]
        discards = hand.discards

        # 必須有捨牌
        if not discards:
            return False

        # 檢查所有捨牌是否都是幺九牌
        return all(tile.is_yaochuu for tile in discards)

    def _count_dora(self, player: int, winning_tile: Optional[Tile] = None) -> int:
        """
        計算寶牌數量

        Args:
            player: 玩家位置
            winning_tile: 和牌牌

        Returns:
            寶牌翻數（表寶牌 + 裡寶牌 + 紅寶牌）
        """
        if not self._tile_set:
            return 0

        dora_count = 0
        hand = self._hands[player]

        # 收集所有牌（手牌 + 和牌牌）
        all_tiles = hand.tiles + [winning_tile] if winning_tile else hand.tiles

        # 表寶牌
        if dora_indicators := self._tile_set.get_dora_indicators(self._kan_count):
            for dora_indicator in dora_indicators:
                dora_tile = self._tile_set.get_dora(dora_indicator)
                if dora_tile in all_tiles:
                    dora_count += 1

        # 裡寶牌（立直時）
        if hand.is_riichi:
            if ura_indicators := self._tile_set.get_ura_dora_indicators(
                self._kan_count
            ):
                for ura_indicator in ura_indicators:
                    ura_dora_tile = self._tile_set.get_dora(ura_indicator)
                    if ura_dora_tile in all_tiles:
                        dora_count += 1

        # 紅寶牌
        for tile in all_tiles:
            if tile.is_red:
                dora_count += 1

        return dora_count

    def get_hand(self, player: int) -> Hand:
        """
        獲取玩家的手牌。

        Args:
            player (int): 玩家位置。

        Returns:
            Hand: 玩家的手牌對象。

        Raises:
            ValueError: 如果玩家位置無效。
        """
        if not (0 <= player < self._num_players):
            raise ValueError(f"玩家位置必須在 0-{self._num_players - 1} 之間")
        return self._hands[player]

    def get_game_state(self) -> GameState:
        """
        獲取遊戲狀態。

        Returns:
            GameState: 遊戲狀態對象。
        """
        return self._game_state

    def get_discards(self, player: int) -> List[Tile]:
        """
        獲取玩家的舍牌。

        Args:
            player (int): 玩家位置。

        Returns:
            List[Tile]: 玩家的舍牌列表。

        Raises:
            ValueError: 如果玩家位置無效。
        """
        if not (0 <= player < self._num_players):
            raise ValueError(f"玩家位置必須在 0-{self._num_players - 1} 之間")
        return self._hands[player].discards

    def get_last_discard(self) -> Optional[Tile]:
        """
        取得最新的捨牌（尚未被處理）。

        Returns:
            Optional[Tile]: 最新的捨牌。
        """
        return self._last_discarded_tile

    def get_num_players(self) -> int:
        """
        取得玩家數量。

        Returns:
            int: 玩家數量。
        """
        return self._num_players

    def get_wall_remaining(self) -> Optional[int]:
        """
        取得牌山剩餘張數。

        Returns:
            Optional[int]: 牌山剩餘張數。
        """
        return self._tile_set.remaining if self._tile_set else None

    def get_revealed_dora_indicators(self) -> List[Tile]:
        """
        取得目前公開的寶牌指示牌。

        Returns:
            List[Tile]: 公開的寶牌指示牌列表。
        """
        return self._tile_set.get_dora_indicators() if self._tile_set else []

    def get_available_chi_sequences(self, player: int) -> List[List[Tile]]:
        """
        取得玩家可用的吃牌組合（僅限上家捨牌）。

        Args:
            player (int): 玩家位置。

        Returns:
            List[List[Tile]]: 可用的吃牌組合列表。
        """

        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return []
        if (player - self._last_discarded_player) % self._num_players != 1:
            return []
        hand = self._hands[player]
        return [
            seq.copy() for seq in hand.can_chi(self._last_discarded_tile, from_player=0)
        ]

    def handle_ryuukyoku(self) -> RyuukyokuResult:
        """
        處理流局。

        Returns:
            RyuukyokuResult: 流局結果，包含流局類型、流局滿貫玩家等。
        """
        ryuukyoku_type = self.check_ryuukyoku()
        if not ryuukyoku_type:
            return RyuukyokuResult(ryuukyoku=False)

        result = RyuukyokuResult(
            ryuukyoku=True,
            ryuukyoku_type=ryuukyoku_type,
        )

        # 檢查流局滿貫
        if ryuukyoku_type == RyuukyokuType.EXHAUSTED:
            for i in range(self._num_players):
                if self.check_flow_mangan(i):
                    result.flow_mangan_players.append(i)
                    # 流局滿貫：3000 點
                    self._game_state.update_score(i, 3000)
                    for j in range(self._num_players):
                        if j != i:
                            self._game_state.update_score(j, -1000)

        # 處理九種九牌（第一巡）
        # 檢查九種九牌在第一巡時可以流局
        if self._is_first_turn_after_deal:
            for i in range(self._num_players):
                if self._check_kyuushu_kyuuhai(i):
                    result.ryuukyoku_type = RyuukyokuType.KYUUSHU_KYUUHAI
                    result.kyuushu_kyuuhai_player = i
                    # 九種九牌流局時，莊家連莊
                    break

        # 處理全員聽牌流局
        if ryuukyoku_type == RyuukyokuType.SUUCHA_RIICHI:
            # 全員聽牌流局時，莊家支付 300 點給每個閒家
            dealer = self._game_state.dealer
            for i in range(self._num_players):
                if i != dealer:
                    self._game_state.transfer_points(dealer, i, 300)

        self._phase = GamePhase.RYUUKYOKU
        return result

    def apply_win_score(self, win_result: WinResult) -> None:
        """
        應用和牌分數。

        Args:
            win_result (WinResult): 和牌結果。
        """
        score_result = win_result.score_result
        if not score_result:
            return

        winner = (
            win_result.player if hasattr(win_result, "player") else self._current_player
        )
        # 注意：WinResult 可能沒有 player 字段，如果沒有則假設是當前玩家
        # 但 check_win 返回的 WinResult 沒有 player 字段，我們需要確保它有
        # 或者從外部傳入。這裡我們假設調用者會確保上下文正確。
        # 實際上 check_win 返回的 WinResult 確實沒有 player 字段
        # 所以這裡我們需要依賴 score_result.payment_to

        winner = score_result.payment_to

        # 增加贏家分數
        self._game_state.update_score(winner, score_result.total_points)

        # 扣除輸家分數
        if score_result.is_tsumo:
            # 自摸
            if score_result.pao_player is not None and score_result.pao_payment > 0:
                # 包牌自摸：包牌者全付
                self._game_state.update_score(
                    score_result.pao_player, -score_result.pao_payment
                )
            else:
                # 正常自摸
                dealer = self._game_state.dealer
                for i in range(self._num_players):
                    if i == winner:
                        continue

                    payment = 0
                    if i == dealer:
                        payment = score_result.dealer_payment
                    else:
                        payment = score_result.non_dealer_payment

                    self._game_state.update_score(i, -payment)
        else:
            # 榮和
            loser = score_result.payment_from

            if score_result.pao_player is not None and score_result.pao_payment > 0:
                # 包牌榮和（分擔）
                # 包牌者支付 pao_payment
                self._game_state.update_score(
                    score_result.pao_player, -score_result.pao_payment
                )

                # 放銃者支付剩下的
                # 總支付 = total_points - riichi_sticks
                total_pay = score_result.total_points - score_result.riichi_sticks_bonus
                remaining_pay = total_pay - score_result.pao_payment
                self._game_state.update_score(loser, -remaining_pay)
            else:
                # 正常榮和
                # 放銃者支付 total_points - riichi_sticks
                # 注意：total_points 包含供託，但供託是從場上拿的，不是放銃者出的
                # 放銃者只支付 (base + honba)
                # score_result.total_points = base + honba + sticks
                payment = score_result.total_points - score_result.riichi_sticks_bonus
                self._game_state.update_score(loser, -payment)

        # 清空供託
        if score_result.riichi_sticks_bonus > 0:
            self._game_state.clear_riichi_sticks()

        # 清空本場 (如果是自摸或莊家榮和? 不，通常由 next_dealer 處理)
        # 這裡只處理分數更新

    def _check_chankan(self, kan_player: int, kan_tile: Tile) -> List[int]:
        """
        檢查搶槓（其他玩家是否可以榮和槓牌）

        Args:
            kan_player: 執行槓的玩家
            kan_tile: 被槓的牌

        Returns:
            可以搶槓和牌的玩家列表
        """
        winners = []
        for player in range(self._num_players):
            if player == kan_player:
                continue  # 不能搶自己的槓

            if self.check_win(player, kan_tile, is_chankan=True):
                winners.append(player)

        return winners

    def _interrupt_ippatsu(self, action: GameAction, acting_player: int) -> None:
        """處理副露或槓造成的一發中斷。"""
        if not self._riichi_ippatsu:
            return

        if action not in {
            GameAction.CHI,
            GameAction.PON,
            GameAction.KAN,
            GameAction.ANKAN,
        }:
            return

        if not self._game_state.ruleset.ippatsu_interrupt_on_meld_or_kan:
            return

        for player in self._riichi_ippatsu.keys():
            self._riichi_ippatsu[player] = False
            self._riichi_ippatsu_discard[player] = 0

    def _check_sancha_ron(self) -> bool:
        """
        檢查是否三家和了（多人和牌流局）

        當多個玩家同時可以榮和同一張牌時，如果有三個或以上玩家和牌，則為三家和了（流局）

        Returns:
            是否為三家和了
        """
        if self._last_discarded_tile is None or self._last_discarded_player is None:
            return False

        # 檢查有多少玩家可以榮和這張牌
        winning_players = []
        for player in range(self._num_players):
            if player == self._last_discarded_player:
                continue  # 不能榮和自己的牌

            if self.check_win(player, self._last_discarded_tile):
                winning_players.append(player)

        # 如果三個或以上玩家和牌，則為三家和了
        return len(winning_players) >= 3

    def _check_rinshan_win(
        self, player: int, rinshan_tile: Tile
    ) -> Optional[WinResult]:
        """
        檢查嶺上開花（槓後摸牌和牌）

        Args:
            player: 玩家位置
            rinshan_tile: 從嶺上摸到的牌

        Returns:
            和牌結果，如果不能和則返回 None
        """
        return self.check_win(player, rinshan_tile, is_rinshan=True)

    def _calculate_noten_bappu(self) -> Dict[int, int]:
        """
        計算不聽罰符

        Returns:
            玩家分數變化字典 {player_index: score_change}
        """
        tenpai_players = []
        for i in range(self._num_players):
            if self._hands[i].is_tenpai():
                tenpai_players.append(i)

        num_tenpai = len(tenpai_players)
        changes = {}

        if num_tenpai == 0 or num_tenpai == 4:
            return {}

        if num_tenpai == 1:
            # 1人聽：+3000 / -1000
            winner = tenpai_players[0]
            changes[winner] = 3000
            for i in range(self._num_players):
                if i != winner:
                    changes[i] = -1000

        elif num_tenpai == 2:
            # 2人聽：+1500 / -1500
            for i in range(self._num_players):
                if i in tenpai_players:
                    changes[i] = 1500
                else:
                    changes[i] = -1500

        elif num_tenpai == 3:
            # 3人聽：+1000 / -3000
            loser = [i for i in range(self._num_players) if i not in tenpai_players][0]
            changes[loser] = -3000
            for i in tenpai_players:
                changes[i] = 1000

        # 應用分數變更
        for player, delta in changes.items():
            self._game_state.update_score(player, delta)

        return changes

    def check_furiten_discards(self, player: int) -> bool:
        """
        檢查現物振聽：玩家打過的牌包含在聽牌牌中

        Args:
            player: 玩家位置

        Returns:
            是否為現物振聽
        """
        hand = self._hands[player]

        # 未聽牌不算振聽
        if not hand.is_tenpai():
            return False

        # 獲取聽牌牌
        waiting_tiles = hand.get_waiting_tiles()
        if not waiting_tiles:
            return False

        # 檢查玩家的捨牌歷史
        for discard in hand.discards:
            # 如果打過的牌在聽牌牌中，則為現物振聽
            if any(
                discard.suit == wt.suit and discard.rank == wt.rank
                for wt in waiting_tiles
            ):
                return True

        return False

    def check_furiten_temp(self, player: int) -> bool:
        """
        檢查同巡振聽：同巡內放過榮和機會

        Args:
            player: 玩家位置

        Returns:
            是否為同巡振聽
        """
        # 檢查是否設置了同巡振聽
        if not self._furiten_temp.get(player, False):
            return False

        # 檢查是否是同一回合
        furiten_round = self._furiten_temp_round.get(player, -1)
        return furiten_round == self._turn_count

    def check_furiten_riichi(self, player: int) -> bool:
        """
        檢查立直振聽：立直後放過榮和機會

        Args:
            player: 玩家位置

        Returns:
            是否為立直振聽
        """
        return self._furiten_permanent.get(player, False)

    def is_furiten(self, player: int) -> bool:
        """
        綜合檢查玩家是否處於振聽狀態

        Args:
            player: 玩家位置

        Returns:
            是否處於振聽狀態
        """
        return (
            self.check_furiten_discards(player)
            or self.check_furiten_temp(player)
            or self.check_furiten_riichi(player)
        )

    def _check_tobi(self) -> bool:
        """
        檢查是否觸發擊飛

        Returns:
            是否觸發擊飛
        """
        if not self._game_state.ruleset.tobi_enabled:
            return False

        for score in self._game_state.scores:
            if score < 0:
                return True

        return False
