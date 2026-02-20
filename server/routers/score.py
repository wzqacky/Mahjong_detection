"""
Score router — wraps pyriichi to evaluate a winning hand.
"""

from typing import List

from fastapi import APIRouter

from pyriichi.tiles import create_tile, Tile
from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.yaku import YakuChecker
from pyriichi.game_state import GameState, Wind
from pyriichi.scoring import ScoreCalculator, ScoreResult

from server.schemas import ScoreRequest, ScoreResponse, YakuItem

router = APIRouter(prefix="/api", tags=["score"])


# Lookup helpers
_WIND_MAP = {
    "east": Wind.EAST,
    "south": Wind.SOUTH,
    "west": Wind.WEST,
    "north": Wind.NORTH,
}

# Ordered sequences used for dora-indicator → dora conversion
_WIND_ORDER = ["EW", "SW", "WW", "NW"] # 東南西北
_DRAGON_ORDER = ["WD", "GD", "RD"] # 白發中


def _dora_from_indicator(indicator: str) -> str:
    """
    Return the dora tile string for a given indicator tile string.

    Rules (standard riichi mahjong):
      Winds  : EW → SW → WW → NW → EW (cycle of 4)
      Dragons: WD → GD → RD → WD (cycle of 3)
      Numbers: n → n+1, wrapping 9 → 1 within the same suit letter
    """
    if indicator in _WIND_ORDER:
        return _WIND_ORDER[(_WIND_ORDER.index(indicator) + 1) % 4]
    if indicator in _DRAGON_ORDER:
        return _DRAGON_ORDER[(_DRAGON_ORDER.index(indicator) + 1) % 3]
    # Number tile: e.g. "5B" → rank=5, suit_letter="B"
    rank = int(indicator[:-1])
    suit_letter = indicator[-1]
    return f"{(rank % 9) + 1}{suit_letter}"


def _infer_meld_type(tiles: List[Tile], is_open: bool) -> MeldType:
    """
    Infer MeldType from the tile group and the open flag.

      4 tiles            → KAN (open) or ANKAN (closed)
      3 identical tiles  → PON
      3 sequential tiles → CHI
    """
    if len(tiles) == 4:
        return MeldType.KAN if is_open else MeldType.ANKAN

    if len(tiles) == 3:
        suits = [t.suit for t in tiles]
        ranks = [t.rank for t in tiles]

        if len(set(suits)) == 1:
            if len(set(ranks)) == 1:
                return MeldType.PON
            sorted_ranks = sorted(ranks)
            if sorted_ranks[1] - sorted_ranks[0] == 1 and sorted_ranks[2] - sorted_ranks[1] == 1:
                return MeldType.CHI

    tile_strs = [str(t) for t in tiles]
    raise ValueError(f"Cannot infer meld type from tiles: {tile_strs}")


def _count_dora(all_tiles: List[Tile], dora_indicators: List[str]) -> int:
    """
    Count total dora across all tiles (hand + melds + winning tile).

    Two sources of dora:
      1. Regular dora: tile whose string matches the dora derived from an indicator.
      2. Red dora (aka dora): tiles whose _is_red attribute is True.
    """
    dora_strings = {_dora_from_indicator(ind) for ind in dora_indicators}
    count = 0
    for tile in all_tiles:
        if str(tile) in dora_strings:
            count += 1
        if getattr(tile, "_is_red", False):
            count += 1
    return count


# Endpoint
@router.post("/score", response_model=ScoreResponse)
def compute_score(request: ScoreRequest) -> ScoreResponse:
    """
    Evaluate a winning mahjong hand and return yaku + score breakdown.
    """
    try:
        # 1. Build concealed hand
        red_flags = list(request.red_tile_flags)
        # Pad to match tiles length if caller sent a shorter list
        if len(red_flags) < len(request.tiles):
            red_flags += [False] * (len(request.tiles) - len(red_flags))

        hand_tiles = [
            create_tile(t, is_red=red_flags[i])
            for i, t in enumerate(request.tiles)
        ]
        hand = Hand(hand_tiles)
        hand._is_riichi = request.is_riichi

        # 2. Attach melds
        all_meld_tiles: List[Tile] = []
        for meld_input in request.melds:
            meld_tiles = [create_tile(t) for t in meld_input.tiles]
            meld_type = _infer_meld_type(meld_tiles, meld_input.is_open)
            hand._melds.append(Meld(meld_type, meld_tiles))
            all_meld_tiles.extend(meld_tiles)

        # 3. Winning tile
        winning_tile = create_tile(
            request.winning_tile,
            is_red=request.winning_tile_is_red,
        )

        # 4. Validate + get winning combinations
        if not hand.is_winning_hand(winning_tile=winning_tile):
            return ScoreResponse(is_winning=False)

        winning_combs = hand.get_winning_combinations(winning_tile=winning_tile)
        if not winning_combs:
            return ScoreResponse(is_winning=False)

        # Use the first valid winning decomposition (standard behaviour)
        winning_combination = list(winning_combs.values())[0]

        # 5. Build GameState
        ctx = request.game_context
        game_state = GameState()
        game_state.set_round(
            _WIND_MAP.get(ctx.round_wind.lower(), Wind.EAST),
            ctx.round_number,
        )
        game_state.set_dealer(ctx.dealer_position)
        for _ in range(ctx.honba):
            game_state.add_honba()
        for _ in range(ctx.riichi_sticks):
            game_state.add_riichi_stick()

        # 6. Check yaku
        checker = YakuChecker()
        yaku_results = checker.check_all(
            hand,
            winning_tile,
            winning_combination,
            game_state,
            is_tsumo=request.is_tsumo,
            is_ippatsu=request.is_ippatsu,
            is_first_turn=request.is_first_turn,
            is_last_tile=request.is_last_tile,
            player_position=ctx.player_position,
            is_rinshan=request.is_rinshan,
            is_chankan=request.is_chankan,
        )

        if not yaku_results:
            return ScoreResponse(
                is_winning=True,
                error="No valid yaku — hand is chombo",
            )

        # 7. Count dora
        all_tiles = hand_tiles + all_meld_tiles + [winning_tile]
        dora_count = _count_dora(all_tiles, request.dora_indicators)

        # 8. Compute score
        calculator = ScoreCalculator()

        fu = calculator.calculate_fu(
            hand,
            winning_tile,
            winning_combination,
            yaku_results,
            game_state,
            request.is_tsumo,
            ctx.player_position,
        )
        han = calculator.calculate_han(yaku_results, dora_count)

        is_yakuman = any(r.is_yakuman for r in yaku_results)
        yakuman_count = sum(1 for r in yaku_results if r.is_yakuman)

        # Build ScoreResult with the correct winner position so payment
        # calculations (dealer vs non-dealer tsumo splits) are accurate.
        score = ScoreResult(
            han=han,
            fu=fu,
            base_points=0,
            total_points=0,
            payment_from=0,
            payment_to=ctx.player_position,
            is_yakuman=is_yakuman,
            yakuman_count=yakuman_count,
            is_tsumo=request.is_tsumo,
            kiriage_mangan_enabled=game_state.ruleset.kiriage_mangan,
        )
        score.calculate_payments(game_state)

        # 9. Build response
        yaku_items = [
            YakuItem(
                code=r.yaku.code,
                name_zh=r.yaku.zh,
                name_en=r.yaku.en,
                han=r.han,
                is_yakuman=r.is_yakuman,
            )
            for r in yaku_results
        ]

        return ScoreResponse(
            is_winning=True,
            yaku=yaku_items,
            han=score.han,
            fu=score.fu,
            base_points=score.base_points,
            total_points=score.total_points,
            dealer_payment=score.dealer_payment,
            non_dealer_payment=score.non_dealer_payment,
            honba_bonus=score.honba_bonus,
            riichi_sticks_bonus=score.riichi_sticks_bonus,
            is_yakuman=score.is_yakuman,
        )

    except Exception as exc:
        return ScoreResponse(is_winning=False, error=str(exc))
