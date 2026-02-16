from __future__ import annotations

from enum import Enum
from typing import Optional


class TranslatableEnum(Enum):
    """提供多語言名稱的列舉基類。"""

    def __new__(cls, code: str, zh: str, ja: str, en: Optional[str] = None):
        obj = object.__new__(cls)
        obj._value_ = code
        obj._zh = zh  # pyright: ignore[reportAttributeAccessIssue]
        obj._ja = ja  # pyright: ignore[reportAttributeAccessIssue]
        obj._en = en  # pyright: ignore[reportAttributeAccessIssue]
        return obj

    @property
    def code(self) -> str:
        """列舉代碼（預設值）。"""
        return str(self.value)

    @property
    def zh(self) -> str:
        """繁體中文名稱。"""
        return self._zh  # pyright: ignore[reportAttributeAccessIssue]

    @property
    def ja(self) -> str:
        """日文名稱。"""
        return self._ja  # pyright: ignore[reportAttributeAccessIssue]

    @property
    def en(self) -> str:
        """英文名稱，若未設定則回傳代碼。"""
        return self._en if self._en is not None else str(self.value)  # pyright: ignore[reportAttributeAccessIssue]
