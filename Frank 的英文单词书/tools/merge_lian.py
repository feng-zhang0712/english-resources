#!/usr/bin/env python3
"""Merge [近] and [反] modules into [联] for chapter markdown files."""

from __future__ import annotations

import re
import sys
from pathlib import Path

MODULE_TAGS = ("义", "形", "例", "源", "族", "搭", "近", "反", "辨", "联", "记", "态")
MODULE_RE = re.compile(r"\[(" + "|".join(MODULE_TAGS) + r")\]")
HEADWORD_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
ITEM_SPLIT_RE = re.compile(r",\s(?=[a-z(（\*])")


def split_vocab_items(content: str) -> list[str]:
    content = content.strip()
    if not content:
        return []
    return [part.strip() for part in ITEM_SPLIT_RE.split(content) if part.strip()]


def item_key(item: str) -> str:
    item = item.strip()
    if not item:
        return ""
    if item.startswith("（") or item.startswith("("):
        return ""
    if "：" in item:
        eng = item.split("：", 1)[0]
    else:
        match = re.match(r"^(.+?)\s+[\u4e00-\u9fff（(]", item)
        eng = match.group(1) if match else item.split()[0]
    return eng.replace(", ", " ").lower().strip()


def merge_vocabulary(jin: str, fan: str, lian: str) -> str:
    seen: set[str] = set()
    merged: list[str] = []
    for source in (lian, jin, fan):
        for item in split_vocab_items(source):
            key = item_key(item)
            if key:
                if key in seen:
                    continue
                seen.add(key)
            elif item in merged:
                continue
            merged.append(item)
    return ", ".join(merged)


def extract_modules(text: str) -> tuple[str, dict[str, str]]:
    """Split text into optional prefix and module map (last occurrence wins per tag)."""
    if not MODULE_RE.search(text):
        return text, {}

    parts = MODULE_RE.split(text)
    prefix = parts[0]
    modules: dict[str, str] = {}
    i = 1
    while i < len(parts):
        tag = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""
        modules[tag] = content
        i += 2
    return prefix, modules


def rebuild_with_modules(prefix: str, modules: dict[str, str]) -> str:
    order = ("义", "形", "例", "源", "族", "搭", "辨", "联", "记", "态")
    chunks = [prefix]
    for tag in order:
        if tag in modules and modules[tag]:
            chunks.append(f"[{tag}]{modules[tag]}")
    return "".join(chunks)


def process_entry_lines(lines: list[str]) -> list[str]:
    jin_parts: list[str] = []
    fan_parts: list[str] = []
    lian_parts: list[str] = []
    output: list[str] = []
    lian_line_index: int | None = None

    for line in lines:
        prefix, modules = extract_modules(line)
        if not modules:
            output.append(line)
            continue

        if "近" in modules:
            jin_parts.append(modules.pop("近"))
        if "反" in modules:
            fan_parts.append(modules.pop("反"))
        had_lian = "联" in modules
        if "联" in modules:
            lian_parts.append(modules.pop("联"))

        if modules:
            rebuilt = rebuild_with_modules(prefix, modules)
            output.append(rebuilt)
            if had_lian:
                lian_line_index = len(output) - 1
        elif prefix:
            output.append(prefix.rstrip())

    merged = merge_vocabulary(", ".join(jin_parts), ", ".join(fan_parts), ", ".join(lian_parts))
    if not merged:
        return output

    if lian_line_index is not None:
        prefix, modules = extract_modules(output[lian_line_index])
        modules["联"] = merged
        output[lian_line_index] = rebuild_with_modules(prefix, modules)
        return output

    lian_line = f"[联] {merged}"
    insert_at = len(output)
    for idx, line in enumerate(output):
        if line.startswith("[辨]"):
            insert_at = idx
            break
        if line.startswith("[记]"):
            insert_at = idx
            break
    output.insert(insert_at, lian_line)
    return output


def process_file(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    entries: list[tuple[int, int]] = []
    start = 0
    for i, line in enumerate(lines):
        if HEADWORD_RE.match(line) and i > start:
            entries.append((start, i))
            start = i
    if start < len(lines):
        entries.append((start, len(lines)))

    merged_count = 0
    new_lines = list(lines)
    offset = 0
    for entry_start, entry_end in entries:
        entry_lines = lines[entry_start:entry_end]
        if not any("[近]" in ln or "[反]" in ln for ln in entry_lines):
            continue
        processed = process_entry_lines(entry_lines)
        if processed != entry_lines:
            merged_count += 1
            before = entry_end - entry_start
            after = len(processed)
            new_lines[entry_start + offset : entry_end + offset] = processed
            offset += after - before

    path.write_text("\n".join(new_lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    return len(entries), merged_count


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: merge_lian.py <file.md> ...", file=sys.stderr)
        return 1

    total_entries = 0
    total_merged = 0
    for arg in argv[1:]:
        path = Path(arg)
        entries, merged = process_file(path)
        total_entries += entries
        total_merged += merged
        print(f"{path}: {merged}/{entries} entries updated")
    print(f"Done: {total_merged} entries updated across {len(argv) - 1} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
