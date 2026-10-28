from __future__ import annotations

from typing import Iterable


ANSI = {
    "border": "\033[36m",
    "title": "\033[96m",
    "text": "\033[97m",
    "muted": "\033[90m",
    "yellow": "\033[33m",
    "green": "\033[32m",
    "reset": "\033[0m",
}


def _paint(value: str, color: str) -> str:
    return f"{ANSI[color]}{value}{ANSI['reset']}"


def box(title: str, lines: Iterable[str], width: int = 60) -> str:
    width = max(48, width)
    inner = width - 4
    content = []
    for raw in lines:
        text = str(raw)
        while len(text) > inner:
            content.append(text[:inner])
            text = text[inner:]
        content.append(text)
    border = _paint("╭" + "─" * (width - 2) + "╮", "border")
    separator = _paint("├" + "─" * (width - 2) + "┤", "border")
    bottom = _paint("╰" + "─" * (width - 2) + "╯", "border")
    result = [border]
    result.append(_paint("│ ", "border") + _paint(title.center(inner), "title") + _paint(" │", "border"))
    result.append(separator)
    result.extend(
        _paint("│ ", "border") + _paint(line.ljust(inner), "text") + _paint(" │", "border")
        for line in content
    )
    result.append(bottom)
    return "\n".join(result)


def schedule_text(blocks: Iterable[dict]) -> str:
    lines = []
    for block in sorted(blocks, key=lambda item: (item["date"], item["start"])):
        lines.append(
            f"{block['start']}-{block['end']}  {block.get('category', 'other'):12} "
            f"{block['title']} {'[FIXED]' if block.get('fixed') else ''}"
        )
    return "\n".join(lines) or "No scheduled blocks."
