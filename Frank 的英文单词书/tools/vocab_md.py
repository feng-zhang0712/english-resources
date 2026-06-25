"""Shared markdown parsing for Frank vocabulary chapters."""

from __future__ import annotations

import re

FIELD_RE = re.compile(r"^\[([^\]]+)\]\s*(.*)")
HEADWORD_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
PHONETIC_RE = re.compile(r"^(英/美|英\s|美\s|英/)")
POS_RE = re.compile(
    r"^(n\.|v\.|adj\.|adv\.|prep\.|conj\.|pron\.|interj\.|num\.|art\.|det\.|modal\.|abbr\.|prefix\.|suffix\.|comb\.|phr\.|phrase)"
)


def parse_markdown(text: str) -> tuple[str | None, list[dict]]:
    lines = text.splitlines()
    chapter_title = None
    entries: list[dict] = []
    current: dict | None = None

    for raw in lines:
        line = raw.rstrip()
        if not line:
            continue

        if line.startswith("# "):
            chapter_title = line[2:].strip()
            continue

        m = HEADWORD_RE.match(line)
        if m:
            if current:
                entries.append(current)
            current = {"word": m.group(1), "meta": [], "fields": []}
            continue

        if current is None:
            continue

        fm = FIELD_RE.match(line)
        if fm:
            current["fields"].append((fm.group(1), fm.group(2)))
        else:
            current["meta"].append(line)

    if current:
        entries.append(current)
    return chapter_title, entries


def lookup_word(headword: str) -> str:
    """Normalize headword for dictionary API lookup."""
    word = headword.strip()
    word = re.split(r"\s*[（(]", word)[0].strip()
    word = word.split()[0] if word.split() else word
    return word.lower()
