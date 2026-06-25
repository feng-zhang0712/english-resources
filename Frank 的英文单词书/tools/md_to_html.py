#!/usr/bin/env python3
"""Convert Frank vocabulary markdown to an interactive HTML preview with pronunciation."""

from __future__ import annotations

import argparse
import html
import http.server
import re
import sys
import webbrowser
from pathlib import Path

from vocab_md import PHONETIC_RE, POS_RE, lookup_word, parse_markdown

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def render_inline(text: str) -> str:
    escaped = html.escape(text)
    return BOLD_RE.sub(r"<strong>\1</strong>", escaped)


def speaker_button(word: str, *, inline: bool = False) -> str:
    lookup = html.escape(lookup_word(word), quote=True)
    cls = "speakers inline" if inline else "speakers"
    return (
        f'<span class="{cls}">'
        f'<button type="button" class="speaker" data-word="{lookup}" '
        f'title="美音" aria-label="播放美音">🔊</button>'
        f"</span>"
    )


def render_entry(entry: dict) -> str:
    word = html.escape(entry["word"])
    lookup = html.escape(lookup_word(entry["word"]), quote=True)
    has_phonetic = any(PHONETIC_RE.match(line) for line in entry["meta"])
    head_speaker = speaker_button(entry["word"], inline=True) if has_phonetic else ""

    meta_html: list[str] = []
    for line in entry["meta"]:
        css = "meta"
        if PHONETIC_RE.match(line):
            css = "meta phonetic"
        elif POS_RE.match(line):
            css = "meta pos"
        elif line.startswith("（") or line.startswith("("):
            css = "meta note"

        meta_html.append(
            f'<div class="{css}">{render_inline(line)}</div>'
        )

    fields_html: list[str] = []
    for label, content in entry["fields"]:
        fields_html.append(
            '<div class="field">'
            f'<span class="field-label">[{html.escape(label)}]</span> '
            f'<span class="field-body">{render_inline(content)}</span>'
            "</div>"
        )

    return (
        f'<article class="entry" id="entry-{lookup}">'
        f'<header class="entry-head"><h2 class="headword">{word}</h2>{head_speaker}</header>'
        f'{"".join(meta_html)}'
        f'{"".join(fields_html)}'
        "</article>"
    )


HTML_SHELL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #f7f8fb;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --label: #2e4a6e;
      --accent: #1a73e8;
      --border: #e5e7eb;
      --phonetic: #374151;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Songti SC", "Noto Serif SC", Georgia, "Times New Roman", serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.55;
    }}
    .page {{
      max-width: 920px;
      margin: 0 auto;
      padding: 24px 20px 64px;
    }}
    .chapter-title {{
      margin: 0 0 24px;
      font-size: 1.75rem;
      font-weight: 700;
      letter-spacing: 0.02em;
    }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      gap: 12px;
      align-items: center;
      padding: 10px 0 14px;
      margin-bottom: 8px;
      background: linear-gradient(var(--bg) 70%, transparent);
      backdrop-filter: blur(6px);
    }}
    .toolbar input {{
      flex: 1;
      padding: 10px 14px;
      border: 1px solid var(--border);
      border-radius: 10px;
      font-size: 1rem;
      background: var(--card);
    }}
    .toolbar .count {{
      color: var(--muted);
      font-size: 0.9rem;
      white-space: nowrap;
    }}
    .entry {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px 18px 14px;
      margin-bottom: 14px;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }}
    .entry-head {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 4px;
    }}
    .headword {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 1.35rem;
      font-weight: 700;
      color: #1a1a1a;
    }}
    .meta {{
      font-size: 0.98rem;
      margin: 2px 0;
      color: var(--text);
    }}
    .meta.phonetic {{
      color: var(--phonetic);
      font-style: italic;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .meta.pos {{ color: #111827; }}
    .meta.note {{ color: var(--muted); padding-left: 0.35rem; }}
    .field {{
      margin-top: 6px;
      font-size: 0.98rem;
    }}
    .field-label {{
      color: var(--label);
      font-weight: 700;
      font-family: "Heiti SC", "PingFang SC", sans-serif;
    }}
    .speakers {{
      display: inline-flex;
      gap: 6px;
      align-items: center;
    }}
    .speakers.inline {{ margin-left: auto; }}
    .speaker {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid #c7dafc;
      background: #eef4ff;
      color: var(--accent);
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 0.9rem;
      cursor: pointer;
      line-height: 1.2;
    }}
    .speaker:hover {{ background: #dbeafe; }}
    .speaker:active {{ transform: scale(0.97); }}
    .speaker.loading {{ opacity: 0.6; pointer-events: none; }}
    .hidden {{ display: none !important; }}
    .toast {{
      position: fixed;
      left: 50%;
      bottom: 24px;
      transform: translateX(-50%);
      background: rgba(17, 24, 39, 0.92);
      color: #fff;
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 0.9rem;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s ease;
    }}
    .toast.show {{ opacity: 1; }}
  </style>
</head>
<body>
  <div class="page">
    <h1 class="chapter-title">{chapter_title}</h1>
    <div class="toolbar">
      <input id="search" type="search" placeholder="搜索单词…" autocomplete="off">
      <span class="count" id="count"></span>
    </div>
    <div id="entries">
{entries}
    </div>
  </div>
  <div class="toast" id="toast" role="status" aria-live="polite"></div>
  <audio id="player" preload="none"></audio>
  <script>
    const API = "https://api.dictionaryapi.dev/api/v2/entries/en/";
    const FALLBACK = "https://api.dictionaryapi.dev/media/pronunciations/en/";
    const cache = new Map();
    const player = document.getElementById("player");
    const toast = document.getElementById("toast");
    let toastTimer = null;

    function showToast(msg) {{
      toast.textContent = msg;
      toast.classList.add("show");
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => toast.classList.remove("show"), 2200);
    }}

    function classifyAudio(url) {{
      const lower = url.toLowerCase();
      if (lower.includes("-us") || lower.includes("us_pron") || lower.includes("/us/")) return "us";
      if (lower.includes("-uk") || lower.includes("uk_pron") || lower.includes("/uk/")) return "uk";
      return "unknown";
    }}

    async function resolveUsAudio(word) {{
      const key = word + ":us";
      if (cache.has(key)) return cache.get(key);

      let chosen = null;
      try {{
        const resp = await fetch(API + encodeURIComponent(word));
        if (resp.ok) {{
          const data = await resp.json();
          let fallback = null;
          for (const item of data[0]?.phonetics || []) {{
            const audio = (item.audio || "").trim();
            if (!audio) continue;
            const bucket = {{ ipa: item.text || "", audio }};
            const kind = classifyAudio(audio);
            if (kind === "us" && !chosen) {{
              chosen = bucket;
              break;
            }}
            if (kind !== "uk" && !fallback) fallback = bucket;
          }}
          if (!chosen) chosen = fallback;
        }}
      }} catch (_) {{ /* offline or blocked */ }}

      if (!chosen) {{
        chosen = {{ audio: FALLBACK + word + "-us.mp3", ipa: "" }};
      }}

      cache.set(key, chosen);
      return chosen;
    }}

    async function playWord(button) {{
      const word = button.dataset.word;
      button.classList.add("loading");
      try {{
        const result = await resolveUsAudio(word);
        if (!result?.audio) {{
          showToast("未找到发音：" + word);
          return;
        }}
        player.src = result.audio;
        await player.play();
      }} catch (err) {{
        showToast("无法播放发音");
      }} finally {{
        button.classList.remove("loading");
      }}
    }}

    document.querySelectorAll(".speaker").forEach((btn) => {{
      btn.addEventListener("click", () => playWord(btn));
    }});

    const search = document.getElementById("search");
    const entries = Array.from(document.querySelectorAll(".entry"));
    const count = document.getElementById("count");

    function updateFilter() {{
      const q = search.value.trim().toLowerCase();
      let visible = 0;
      for (const entry of entries) {{
        const text = entry.textContent.toLowerCase();
        const head = entry.querySelector(".headword")?.textContent.toLowerCase() || "";
        const show = !q || head.includes(q) || text.includes(q);
        entry.classList.toggle("hidden", !show);
        if (show) visible += 1;
      }}
      count.textContent = visible + " / " + entries.length;
    }}

    search.addEventListener("input", updateFilter);
    updateFilter();
  </script>
</body>
</html>
"""


def build_html(chapter_title: str | None, entries: list[dict], *, source_name: str) -> str:
    title = f"Frank 的英文单词书 · {chapter_title}" if chapter_title else source_name
    chapter_heading = html.escape(chapter_title or source_name)
    entries_html = "\n".join(render_entry(entry) for entry in entries)
    return HTML_SHELL.format(
        title=html.escape(title),
        chapter_title=chapter_heading,
        entries=entries_html,
    )


def convert(md_path: Path, out_path: Path | None = None) -> Path:
    text = md_path.read_text(encoding="utf-8")
    chapter_title, entries = parse_markdown(text)
    if not entries:
        raise SystemExit(f"No entries found in {md_path}")

    html_text = build_html(chapter_title, entries, source_name=md_path.stem)
    if out_path is None:
        out_path = md_path.with_suffix(".html")
    out_path.write_text(html_text, encoding="utf-8")
    return out_path


def serve(path: Path, port: int) -> None:
    directory = path.parent.resolve()
    filename = path.name

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def log_message(self, fmt, *args):
            sys.stderr.write("%s - %s\\n" % (self.address_string(), fmt % args))

    url = f"http://127.0.0.1:{port}/{filename}"
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Serving {path}")
    print(f"Preview: {url}")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nStopped.")
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert vocabulary markdown to interactive HTML preview")
    parser.add_argument("input", type=Path, help="Input .md file")
    parser.add_argument("-o", "--output", type=Path, help="Output .html path")
    parser.add_argument("--serve", action="store_true", help="Start local preview server after conversion")
    parser.add_argument("--port", type=int, default=8765, help="Preview server port (default: 8765)")
    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        return 1

    out = convert(args.input, args.output)
    print(f"Wrote {out} ({out.stat().st_size // 1024} KB)")
    if args.serve:
        serve(out, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
