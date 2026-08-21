from __future__ import annotations

import re
from pathlib import Path

from .errors import InvalidFileName, InvalidPageRange

INVALID_WINDOWS_CHARS = re.compile(r'[\\/:*?"<>|]')
RESERVED_WINDOWS_NAMES = {
    "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def validate_pdf_name(name: str) -> str:
    name = name.strip()
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    stem = Path(name).stem
    if not stem or INVALID_WINDOWS_CHARS.search(name):
        raise InvalidFileName('ファイル名にWindowsで使用できない文字（\\ / : * ? " < > |）が含まれています。')
    if stem.upper() in RESERVED_WINDOWS_NAMES or name.endswith((".pdf ", ".pdf.")):
        raise InvalidFileName("Windowsで使用できないファイル名です。")
    return name


def parse_page_ranges(text: str, page_count: int) -> list[list[int]]:
    """1始まりの `1-3, 4-7` または改行区切りを0始まりへ変換する。"""
    chunks = [x.strip() for x in re.split(r"[,\n]+", text) if x.strip()]
    if not chunks:
        raise InvalidPageRange("ページ範囲を入力してください（例: 1-3, 4-7）。")
    result: list[list[int]] = []
    seen: set[int] = set()
    for chunk in chunks:
        match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", chunk)
        if not match:
            raise InvalidPageRange(f"ページ指定「{chunk}」の形式が正しくありません。例: 1-3")
        start, end = map(int, match.groups())
        if start < 1 or end < start or end > page_count:
            raise InvalidPageRange(f"ページ指定「{chunk}」は存在するページ（1～{page_count}）の範囲外です。")
        indexes = list(range(start - 1, end))
        if seen.intersection(indexes):
            raise InvalidPageRange("ページ範囲が重複しています。")
        seen.update(indexes)
        result.append(indexes)
    return result
