"""Fetch and cache US pronunciation audio from dictionaryapi.dev."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
DEFAULT_CACHE = Path(__file__).resolve().parent / ".cache" / "pronunciations"
FALLBACK_AUDIO = "https://api.dictionaryapi.dev/media/pronunciations/en/{slug}-us.mp3"


@dataclass
class Pronunciation:
    word: str
    ipa: str | None = None
    audio: str | None = None

    @property
    def has_audio(self) -> bool:
        return bool(self.audio)


def _slug(word: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", word.lower()).strip("-")


def _is_us_audio(url: str) -> bool:
    lower = url.lower()
    return "-us" in lower or "us_pron" in lower or "/us/" in lower or "american" in lower


def _is_uk_audio(url: str) -> bool:
    lower = url.lower()
    return "-uk" in lower or "uk_pron" in lower or "/uk/" in lower


def _pick_us_phonetics(data: list[dict]) -> Pronunciation:
    word = data[0].get("word", "")
    us: Pronunciation | None = None
    fallback: Pronunciation | None = None

    for item in data[0].get("phonetics", []):
        audio = (item.get("audio") or "").strip()
        ipa = (item.get("text") or "").strip() or None
        if not audio and not ipa:
            continue
        bucket = Pronunciation(word=word, ipa=ipa, audio=audio or None)
        if audio:
            if _is_us_audio(audio) and us is None:
                us = bucket
                continue
            if not _is_uk_audio(audio) and fallback is None:
                fallback = bucket
                continue
        if fallback is None and ipa:
            fallback = bucket

    if us is None and fallback is not None:
        us = fallback
    return us or Pronunciation(word=word)


def _fallback_pronunciation(word: str) -> Pronunciation:
    slug = _slug(word)
    return Pronunciation(
        word=word,
        ipa=None,
        audio=FALLBACK_AUDIO.format(slug=slug),
    )


def fetch_pronunciation(word: str, *, cache_dir: Path | None = DEFAULT_CACHE) -> Pronunciation | None:
    key = word.lower().strip()
    if not key:
        return None

    cache_file = None
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{_slug(key)}.json"
        if cache_file.is_file():
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
            if "audio" in payload:
                return Pronunciation(word=payload["word"], ipa=payload.get("ipa"), audio=payload.get("audio"))
            # legacy cache with uk/us keys
            legacy = payload.get("us") or payload.get("uk")
            if legacy:
                return Pronunciation(word=payload["word"], ipa=legacy.get("ipa"), audio=legacy.get("audio"))

    url = API_URL.format(word=urllib.parse.quote(key))
    try:
        with urllib.request.urlopen(url, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return _fallback_pronunciation(key)

    result = _pick_us_phonetics(data)
    if not result.has_audio:
        result = _fallback_pronunciation(key)

    if cache_file is not None:
        cache_file.write_text(
            json.dumps(
                {"word": result.word, "ipa": result.ipa, "audio": result.audio},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    return result
