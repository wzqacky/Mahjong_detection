"""
Request / response schemas for the Mahjong Score API.

Tile string format (matches YOLO detection output and pyriichi's create_tile):
  Number suits : "1B"–"9B" (Pinzu), "1C"–"9C" (Sozu), "1D"–"9D" (Manzu)
  Winds        : "EW", "SW", "WW", "NW"
  Dragons      : "WD" (Haku), "GD" (Hatsu), "RD" (Chun)
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MeldInput(BaseModel):
    """One open (or closed-kan) meld."""

    tiles: List[str] = Field(
        ...,
        description="3 tiles for Chi/Pon, 4 tiles for Kan/Ankan",
    )
    is_open: bool = Field(
        True,
        description="True = open meld (Chi/Pon/open Kan). False = closed kan (Ankan) only.",
    )


class GameContextInput(BaseModel):
    """Game-level context that affects yaku eligibility and payment amounts."""

    round_wind: str = Field(
        "east",
        description="Current round wind: 'east' OR 'south' OR 'west' OR 'north'",
    )
    round_number: int = Field(1, ge=1, le=4)
    dealer_position: int = Field(
        0,
        ge=0,
        le=3,
        description="Seat index (0–3) of the current dealer (East seat)",
    )
    player_position: int = Field( # 3-4 players
        0,
        ge=2,
        le=3,
        description="Seat index (0–3) of the winning player",
    )
    # This is added whenever nobody wins or when the dealer wins
    honba: int = Field(0, ge=0, description="Number of honba sticks on the table")
    riichi_sticks: int = Field(
        0, ge=0, le=3, description="Number of riichi sticks (1000-pt bets) on the table"
    )


class ScoreRequest(BaseModel):
    """
    Full description of a winning hand.

    `tiles` should contain only the *concealed* tiles that are still in hand —
    i.e. after removing the winning tile and any tiles that belong to open melds.

    Example for a hand of  2C 3C 4C | 4D 5D 6D | WW WW WW (pon) | 8B 8B 8B 8B (kan)
    with winning tile 2B:
        tiles            = ["2C","3C","4C","4D","5D","6D"]
        winning_tile     = "2B"
        melds            = [
            {"tiles": ["WW","WW","WW"], "is_open": true},
            {"tiles": ["8B","8B","8B","8B"], "is_open": true},
        ]
    """

    # Concealed hand tiles (excl. winning tile and meld tiles)
    tiles: List[str] = Field(
        ...,
        description="Concealed hand tiles, excluding the winning tile and meld tiles",
    )
    red_tile_flags: List[bool] = Field(
        default=[],
        description="Parallel to `tiles`; True marks that tile as a red dora",
    )

    # Winning tile
    winning_tile: str = Field(..., description="The tile that completed the hand")
    winning_tile_is_red: bool = Field(False, description="True if the winning tile is a red dora")

    # Open / closed melds
    melds: List[MeldInput] = Field(default=[], description="All melds (open or ankan)")

    # Win-condition flags
    is_riichi: bool = False # 立直
    is_tsumo: bool = Field(False, description="True = self-draw win (tsumo)") # 自摸
    is_ippatsu: bool = Field(False, description="True = won within one go-around after riichi") # 一發
    is_first_turn: bool = Field(False, description="True = dealer's very first draw (tenhou) or non-dealer's (chihou)") # 天糊/ 地糊
    is_last_tile: bool = Field(False, description="True = last tile of the wall (haitei/houtei)") # 海底
    is_rinshan: bool = Field(False, description="True = won on the supplemental draw after a kan") # 嶺上
    is_chankan: bool = Field(False, description="True = robbed an opponent's added kan") # 搶槓

    # Dora indicators
    dora_indicators: List[str] = Field(
        default=[],
        description="Dora *indicator* tile strings (the tile flipped on the wall, not the dora itself)",
    )

    # Game context
    game_context: GameContextInput = Field(default_factory=GameContextInput)


# Response models
class YakuItem(BaseModel):
    """A single matched yaku."""

    code: str = Field(..., description="Internal yaku code, e.g. 'riichi'")
    name_zh: str = Field(..., description="Traditional Chinese name, e.g. '立直'")
    name_en: str = Field(..., description="English name, e.g. 'Riichi'")
    han: int = Field(..., description="Han value of this yaku (0 for yakuman)")
    is_yakuman: bool # 役滿 or not


class ScoreResponse(BaseModel):
    """Full scoring result returned by POST /api/score."""

    is_winning: bool = Field(..., description="False if the hand is not a valid winning hand")

    # Populated only when is_winning=True and yaku exist
    yaku: List[YakuItem] = []
    han: int = 0
    fu: int = 0
    base_points: int = Field(0, description="Basic points (fu * 2^(han+2)); 0 for mangan+")
    total_points: int = Field(0, description="Total points won (after rounding, honba, riichi sticks)")
    dealer_payment: int = Field(0, description="Points each non-dealer pays the dealer on tsumo")
    non_dealer_payment: int = Field(0, description="Points non-dealers pay on tsumo (for non-dealer winner: dealer pays double)")
    honba_bonus: int = Field(0, description="Extra points from honba sticks")
    riichi_sticks_bonus: int = Field(0, description="Points from riichi sticks on the table")
    is_yakuman: bool = False

    # Populated on error or no-yaku
    error: Optional[str] = Field(None, description="Error message if scoring failed or hand has no yaku (chombo)")
