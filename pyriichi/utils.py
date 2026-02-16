"""
工具函數

提供便利函數用於牌的解析和格式化。
"""

from typing import List

from pyriichi.tiles import Suit, Tile


def parse_tiles(tile_string: str) -> List[Tile]:
    """
    從字符串解析牌（例如："1m2m3m4p5p6p"）。

    Args:
        tile_string (str): 牌字符串。

    Returns:
        List[Tile]: 牌列表。

    Example:
        >>> parse_tiles("1m2m3m4p5p6p")
        [Tile(MANZU, 1), Tile(MANZU, 2), Tile(MANZU, 3), ...]
        >>> parse_tiles("r5p6p7p")  # 紅寶牌用 r 前綴（標準格式）
        [Tile(PINZU, 5, red=True), Tile(PINZU, 6), Tile(PINZU, 7)]
    """
    tiles = []
    buffer = []  # 存儲 (rank, is_red) 的列表
    i = 0
    suit_map = {"m": Suit.MANZU, "p": Suit.PINZU, "s": Suit.SOZU, "z": Suit.JIHAI}

    while i < len(tile_string):
        char = tile_string[i]

        if char == "r":
            if i + 1 < len(tile_string) and tile_string[i + 1].isdigit():
                rank = int(tile_string[i + 1])
                buffer.append((rank, True))
                i += 2
                continue
            else:
                i += 1
                continue

        if char.isdigit():
            rank = int(char)
            buffer.append((rank, False))
            i += 1
            continue

        if char in suit_map:
            suit = suit_map[char]
            for rank, is_red in buffer:
                tiles.append(Tile(suit, rank, is_red))
            buffer = []
            i += 1
            continue

        # 忽略其他字符
        i += 1

    return tiles


def format_tiles(tiles: List[Tile]) -> str:
    """
    將牌列表格式化為字符串。

    Args:
        tiles (List[Tile]): 牌列表。

    Returns:
        str: 格式化後的字符串。

    Example:
        >>> format_tiles([Tile(Suit.MANZU, 1), Tile(Suit.PINZU, 5)])
        "1m5p"
    """
    return "".join(str(tile) for tile in tiles)


def is_winning_hand(tiles: List[Tile], winning_tile: Tile) -> bool:
    """
    快速檢查是否和牌（便利函數）。

    Args:
        tiles (List[Tile]): 手牌列表（13 張）。
        winning_tile (Tile): 和牌牌。

    Returns:
        bool: 是否和牌。
    """
    from pyriichi.hand import Hand

    hand = Hand(tiles)
    return hand.is_winning_hand(winning_tile)
