#!/usr/bin/env python3
"""
Parse Claude Code CHANGELOG.md and generate:
  - data/releases.json  (structured data)
  - RELEASES.md         (markdown table)
  - docs/index.html     (dashboard)
"""

import json
import re
import os
import subprocess
import hashlib
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = ROOT / "CHANGELOG_RAW.md"
DATES_CACHE = ROOT / "data" / "release_dates.json"
TRANSLATION_CACHE = ROOT / "data" / "translations_cache.json"
JSON_FILE = ROOT / "data" / "releases.json"
RELEASES_FILE = ROOT / "RELEASES.md"
HTML_FILE = ROOT / "docs" / "index.html"


# ---------------------------------------------------------------------------
# 0. Fetch release dates from GitHub API
# ---------------------------------------------------------------------------

def fetch_release_dates() -> dict[str, str]:
    """Fetch release dates from GitHub API + npm, with local cache."""
    cached: dict[str, str] = {}
    if DATES_CACHE.exists():
        cached = json.loads(DATES_CACHE.read_text(encoding="utf-8"))

    # --- Source 1: GitHub Releases API (up to 10 pages = 1000 releases) ---
    gh_token = os.environ.get("GITHUB_TOKEN", "")
    headers_args = []
    if gh_token:
        headers_args = ["-H", f"Authorization: token {gh_token}"]

    total_fetched = 0
    for page in range(1, 11):
        try:
            cmd = ["curl", "-sf"] + headers_args + [
                f"https://api.github.com/repos/anthropics/claude-code/releases?per_page=100&page={page}"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                break
            releases = json.loads(result.stdout)
            if not releases:
                break
            new_on_page = 0
            for rel in releases:
                tag = rel.get("tag_name", "")
                version = tag.lstrip("v")
                pub = rel.get("published_at", "")
                if version and pub:
                    if version not in cached:
                        new_on_page += 1
                    cached[version] = pub[:10]
            total_fetched += len(releases)
            if new_on_page == 0:
                break  # all versions on this page already cached
        except Exception as e:
            print(f"Warning: GitHub API page {page} failed: {e}")
            break

    print(f"GitHub API: fetched {total_fetched} releases")

    # --- Source 2: npm registry (covers ALL versions, skip if cache is large enough) ---
    if len(cached) > 200:
        print(f"npm registry: skipped (cache already has {len(cached)} entries)")
    else:
        try:
            result = subprocess.run(
                ["curl", "-sf", "--max-time", "30",
                 "https://registry.npmjs.org/@anthropic-ai/claude-code"],
                capture_output=True, text=True, timeout=35
            )
            if result.returncode == 0:
                npm_data = json.loads(result.stdout)
                time_map = npm_data.get("time", {})
                count = 0
                for version, ts in time_map.items():
                    if version in ("created", "modified"):
                        continue
                    if version not in cached and ts:
                        cached[version] = ts[:10]
                        count += 1
                print(f"npm registry: added {count} new dates")
        except Exception as e:
            print(f"Warning: npm registry fetch failed: {e}")

    # Save cache
    DATES_CACHE.parent.mkdir(parents=True, exist_ok=True)
    DATES_CACHE.write_text(
        json.dumps(cached, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8"
    )
    print(f"Total cached dates: {len(cached)}")
    return cached


# ---------------------------------------------------------------------------
# 0.5. Translation with OpenAI API + cache
# ---------------------------------------------------------------------------

def _content_hash(text: str) -> str:
    """Stable hash for cache key."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_translation_cache() -> dict[str, str]:
    """Load {hash: korean_text} cache."""
    if TRANSLATION_CACHE.exists():
        return json.loads(TRANSLATION_CACHE.read_text(encoding="utf-8"))
    return {}


def save_translation_cache(cache: dict[str, str]) -> None:
    TRANSLATION_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TRANSLATION_CACHE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def translate_batch_openai(texts: list[str], api_key: str) -> list[str]:
    """Translate a batch of English feature texts to Korean via OpenAI API.
    Batches up to 30 items per request to minimize API calls.
    """
    if not texts:
        return []

    # Build numbered list for batch translation
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    prompt = (
        "Translate each numbered line from English to Korean. "
        "Keep technical terms (command names, flags, API names, file paths) in English. "
        "Return ONLY the numbered translations, same format. "
        "Be concise and natural in Korean.\n\n"
        f"{numbered}"
    )

    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a technical translator. Translate English changelog entries to Korean. Keep code/command/path terms in English."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }).encode("utf-8")

    req = Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        content = result["choices"][0]["message"]["content"].strip()

        # Parse numbered responses
        translations = []
        for line in content.splitlines():
            line = line.strip()
            m = re.match(r"^\d+\.\s*(.+)$", line)
            if m:
                translations.append(m.group(1).strip())

        # If parsing failed, return originals
        if len(translations) != len(texts):
            print(f"  Warning: expected {len(texts)} translations, got {len(translations)}. Using originals for mismatch.")
            # Pad with originals
            while len(translations) < len(texts):
                translations.append(texts[len(translations)])

        return translations
    except Exception as e:
        print(f"  Warning: OpenAI API failed: {e}")
        return texts  # fallback to English


def translate_features(entries: list[dict], api_key: str) -> None:
    """Add 'features_ko' to each entry, using cache + OpenAI API."""
    cache = load_translation_cache()
    to_translate: list[tuple[int, int, str]] = []  # (entry_idx, feat_idx, text)

    # Collect untranslated features
    for ei, entry in enumerate(entries):
        entry["features_ko"] = []
        for fi, feat in enumerate(entry["features"]):
            h = _content_hash(feat)
            if h in cache:
                entry["features_ko"].append(cache[h])
            else:
                entry["features_ko"].append(None)  # placeholder
                to_translate.append((ei, fi, feat))

    if not to_translate:
        print(f"Translation: all {sum(len(e['features']) for e in entries)} features cached, 0 API calls needed")
        return

    print(f"Translation: {len(to_translate)} new features to translate...")

    # Batch translate (30 per request)
    BATCH_SIZE = 30
    translated_count = 0
    for batch_start in range(0, len(to_translate), BATCH_SIZE):
        batch = to_translate[batch_start:batch_start + BATCH_SIZE]
        texts = [t[2] for t in batch]
        translations = translate_batch_openai(texts, api_key)

        for (ei, fi, original), translated in zip(batch, translations):
            h = _content_hash(original)
            cache[h] = translated
            entries[ei]["features_ko"][fi] = translated
            translated_count += 1

        # Rate limit: be nice to OpenAI
        if batch_start + BATCH_SIZE < len(to_translate):
            time.sleep(1)

    save_translation_cache(cache)
    print(f"Translation: {translated_count} features translated, cache now has {len(cache)} entries")


# ---------------------------------------------------------------------------
# 1. Parse CHANGELOG.md
# ---------------------------------------------------------------------------

def _split_changelog(text: str) -> list[tuple[str, str]]:
    """Split changelog into [(version, body), ...] pairs."""
    chunks = re.split(r"\n## +(?:Version )?(\d+\.\d+\.\d+)", text)
    pairs = []
    for i in range(1, len(chunks) - 1, 2):
        pairs.append((chunks[i].strip(), chunks[i + 1]))
    return pairs


def parse_changelog(text: str) -> tuple[list[dict], dict[str, str]]:
    """Return (entries, version_bodies) — version_bodies reused by enrich_first_appearances."""
    pairs = _split_changelog(text)
    entries: list[dict] = []
    version_bodies: dict[str, str] = {}
    for version, body in pairs:
        version_bodies[version] = body
        entries.append({
            "version": version,
            "date": extract_date(body),
            "commands": extract_commands(body),
            "features": extract_features(body),
        })
    return entries, version_bodies


def extract_date(body: str) -> str:
    """Try to find date in body."""
    # Pattern: **Date:** March 29, 2026  or  (March 29, 2026)
    m = re.search(r"(\w+ \d{1,2},? \d{4})", body)
    if m:
        try:
            raw = m.group(1).replace(",", "")
            dt = datetime.strptime(raw, "%B %d %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    # Pattern: 2026-03-29
    m = re.search(r"(\d{4}-\d{2}-\d{2})", body)
    if m:
        return m.group(1)
    return ""


COMMAND_PATTERN = re.compile(
    r"`(/?[\w\-]+(?:\s+[\w\-<>]+)?)`"  # `/effort`, `--bare`, `Ctrl+B`
)
# Also match unquoted patterns like: "/release-notes command", "--continue"
UNQUOTED_SLASH = re.compile(r"(?<!\w)(/[a-z][\w\-]*)")  # /vim, /config, /resume
UNQUOTED_FLAG = re.compile(r"(?<!\w)(--[a-z][\w\-]*)")  # --continue, --resume
CTRL_PATTERN = re.compile(r"((?:Ctrl|ctrl|Alt|alt|Shift|shift)[+\-][A-Za-z])")

KNOWN_PREFIXES = ("/", "--", "-n", "-w", "Ctrl+", "Alt+", "Option+", "Shift+", "claude ")

# False positives to exclude (URL fragments, generic words)
COMMAND_BLOCKLIST = {
    # URL path fragments
    "/claude", "/code", "/www", "/com", "/en", "/docs", "/api",
    "/news", "/v1", "/v2", "/bin", "/usr", "/etc", "/tmp", "/dev",
    "/ai", "/new", "/downloads", "/frontend", "/component",
    "/claude-code", "/claude-code-sdk", "/metrics", "/json",
    "/wp-json", "/next", "/data", "/src", "/dist", "/node",
    "/app", "/lib", "/home", "/index", "/main", "/test", "/spec",
    # Generic CLI fragments
    "--no", "--the", "--and", "--from", "--to", "--with",
    # Tool internal references (not user-facing commands)
    "-p", "-c", "-i", "-a", "-o", "-D", "-C", "-f", "-r",
}

# Words that indicate a NEW feature/command (not a fix/improvement)
NEW_FEATURE_STARTS = (
    "added", "new", "introduced", "introducing", "support for",
    "press ", "hit ", "drag ", "run ", "navigate ", "quickly ",
    "custom ", "vim ", "copy", "resume ", "import ", "interactive ",
    "ask claude", "claude code", "claude can", "claude now",
    "you can now", "print mode",
)
# Words that indicate NOT a new feature
SKIP_STARTS = (
    "fixed", "improved", "removed", "changed", "security",
    "deprecated", "reverted", "breaking change", "lots of",
    "updated spinner", "enhanced",
)


# Context priority: higher index wins when same command appears in multiple lines
CONTEXT_PRIORITY = {"mentioned": 0, "fixed": 1, "improved": 2, "removed": 3, "new": 4}


def _detect_context(line: str) -> str:
    """Detect the context type of a changelog line based on its prefix."""
    stripped = line.strip().lstrip("-* ")
    lower = stripped.lower()
    if any(lower.startswith(s) for s in ("fixed", "fix ")):
        return "fixed"
    if any(lower.startswith(s) for s in ("removed", "remove ")):
        return "removed"
    if any(lower.startswith(s) for s in (
        "improved", "changed", "enhanced", "updated",
        "security", "deprecated", "reverted",
    )):
        return "improved"
    if any(lower.startswith(s) for s in NEW_FEATURE_STARTS):
        return "new"
    # "`/cmd` is now ..." or "`--flag` now ..." patterns → improved
    if re.match(r"^`[/\-].*`\s+(is\s+now|now)\b", stripped):
        return "improved"
    return "mentioned"


def extract_commands(body: str) -> list[dict]:
    """Extract ALL slash commands, CLI flags, keyboard shortcuts from the FULL body text.
    Returns list of {"name": str, "context": str, "summary": str}."""
    commands: dict[str, dict] = {}  # name -> {name, context, summary}

    def _add(candidate: str, context: str, summary: str) -> None:
        if candidate in COMMAND_BLOCKLIST:
            return
        if candidate in commands:
            existing = commands[candidate]
            if CONTEXT_PRIORITY.get(context, 0) > CONTEXT_PRIORITY.get(existing["context"], 0):
                existing["context"] = context
                existing["summary"] = summary
        else:
            commands[candidate] = {"name": candidate, "context": context, "summary": summary}

    for line in body.splitlines():
        ctx = _detect_context(line)
        summary = line.strip().lstrip("-* ")[:80]

        # 1. Backtick-quoted commands from ALL lines (most reliable)
        for m in COMMAND_PATTERN.finditer(line):
            candidate = m.group(1).strip()
            if candidate.startswith("/") or candidate.startswith("--"):
                _add(candidate, ctx, summary)
            elif any(candidate.startswith(p) for p in ("Ctrl+", "Alt+", "Option+", "Shift+")):
                _add(candidate, ctx, summary)

        # 2. Unquoted slash commands from ALL lines
        for m in UNQUOTED_SLASH.finditer(line):
            c = m.group(1)
            if len(c) > 2:
                _add(c, ctx, summary)

        # 3. Unquoted flags (only from new-feature lines to avoid noise)
        if ctx == "new":
            for m in UNQUOTED_FLAG.finditer(line):
                c = m.group(1)
                if len(c) > 3:
                    _add(c, ctx, summary)

        # 4. Keyboard shortcuts from ALL lines (Ctrl+X, Ctrl-b, etc.)
        for m in CTRL_PATTERN.finditer(line):
            c = m.group(1).replace("-", "+")
            _add(c, ctx, summary)

    return list(commands.values())


# ---------------------------------------------------------------------------
# Known real slash commands — ensures first-appearance is always tracked
# ---------------------------------------------------------------------------
KNOWN_SLASH_COMMANDS = {
    "/powerup", "/loop", "/simplify", "/batch", "/copy", "/memory",
    "/effort", "/color", "/context", "/plan", "/teleport", "/remote-env",
    "/remote-control", "/reload-plugins", "/rename", "/rewind", "/usage",
    "/terminal-setup", "/plugin", "/config", "/settings",
    "/permissions", "/doctor", "/model", "/help", "/resume", "/agents",
    "/statusline", "/todos", "/vim", "/approved-tools", "/release-notes",
    "/export", "/mcp", "/add-dir", "/pr-comments", "/upgrade", "/status",
    "/compact", "/debug", "/bug", "/clear", "/t", "/stats", "/feedback",
    "/sandbox", "/skills", "/tasks", "/fork", "/btw", "/voice",
    "/mobile", "/chrome", "/buddy", "/output-style", "/fast-mode",
    "/ide", "/heapdump", "/security-review",
}


def _cmd_names(commands: list[dict]) -> set[str]:
    """Get set of command names from commands list."""
    return {c["name"] for c in commands}


def enrich_first_appearances(entries: list[dict], version_bodies: dict[str, str]) -> None:
    """For known slash commands, find the EARLIEST version that mentions them
    (in any context) and ensure they appear in that version's commands list."""
    reversed_entries = list(reversed(entries))
    already_assigned: set[str] = set()
    for cmd in KNOWN_SLASH_COMMANDS:
        # Find first version that mentions this command
        for entry in reversed_entries:
            body = version_bodies.get(entry["version"], "")
            # Check both backticked and bare mentions
            if f"`{cmd}`" in body or f" {cmd} " in body or f" {cmd}," in body or body.startswith(cmd[1:]):
                if cmd not in already_assigned:
                    if cmd not in _cmd_names(entry["commands"]):
                        entry["commands"].append({"name": cmd, "context": "mentioned", "summary": ""})
                    already_assigned.add(cmd)
                break


def extract_features(body: str) -> list[str]:
    """Extract key feature bullet points (non-fix items)."""
    features: list[str] = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith(("-", "*")):
            continue
        text = line.lstrip("-* ").strip()
        # skip fixes, improvements, changes
        if any(text.lower().startswith(s) for s in SKIP_STARTS):
            continue
        if len(text) < 10:
            continue
        # Clean markdown formatting
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        features.append(text)
    return features[:8]  # top 8 per version


# ---------------------------------------------------------------------------
# 2. Generate outputs
# ---------------------------------------------------------------------------

def esc(s: str) -> str:
    """HTML-escape a string."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _feat_html(items: list[str], cmd_context: dict[str, str] | None = None) -> str:
    """Build <ul> from feature list, highlighting commands with context colors."""
    if not items:
        return '<span class="dim">—</span>'
    parts = []
    for f in items:
        escaped = esc(f)
        if cmd_context:
            escaped = _highlight_cmds_in_text(escaped, cmd_context)
        parts.append(f"<li>{escaped}</li>")
    return f'<ul>{"".join(parts)}</ul>'


def _highlight_cmds_in_text(text: str, cmd_context: dict[str, str]) -> str:
    """Replace command mentions in pre-escaped feature text with colored code tags.
    Skips matches inside URLs (preceded by :/ or ://) to avoid breaking links."""
    for name, ctx in sorted(cmd_context.items(), key=lambda x: -len(x[0])):
        css_cls = f"cmd-ref {ctx}" if ctx != "mentioned" else "cmd-ref"
        escaped_name = esc(name)
        replacement = f'<code class="{css_cls}">{escaped_name}</code>'
        # Negative lookbehind: skip if preceded by :/ (URL context)
        pattern = r"(?<!:/)(?<!/)" + re.escape(escaped_name) + r"(?!\w)"
        text = re.sub(pattern, replacement, text, count=1)
    return text


BADGE_LABELS = {"new": "NEW", "fixed": "FIX", "removed": "DEL", "improved": "IMP"}


def _cmds_html(commands: list[dict]) -> str:
    """Build command badges HTML."""
    if not commands:
        return '<span class="dim">—</span>'
    parts = []
    for c in commands:
        ctx = c.get("context", "mentioned")
        badge = ""
        if ctx in BADGE_LABELS:
            badge = f'<span class="cmd-badge {ctx}">{BADGE_LABELS[ctx]}</span>'
        summary_attr = f' title="{esc(c["summary"])}"' if c.get("summary") else ""
        parts.append(f'<span class="cmd-item"{summary_attr}><code>{esc(c["name"])}</code>{badge}</span>')
    return " ".join(parts)

def generate_readme(entries: list[dict]) -> str:
    lines = [
        "# Claude Code Changelog Dashboard",
        "",
        f"> Auto-updated every 3 hours | Last sync: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "| 버전 | 날짜 | 추가된 커맨드/약어 | 주요 기능 |",
        "|------|------|-------------------|----------|",
    ]
    for e in entries[:80]:
        ver = f"**v{e['version']}**"
        date = e["date"] or "—"
        cmds = ", ".join(f"`{c['name']}`" for c in e["commands"]) if e["commands"] else "—"
        feats = " / ".join(e["features"][:3]) if e["features"] else "—"
        if len(feats) > 200:
            feats = feats[:197] + "..."
        lines.append(f"| {ver} | {date} | {cmds} | {feats} |")

    lines.extend([
        "",
        "---",
        "",
        "## How it works",
        "",
        "- GitHub Actions checks [anthropics/claude-code CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) every 3 hours",
        "- Python script parses new entries and updates this table + [dashboard](https://tryumanshow.github.io/claude-code-changelog)",
        "",
        "## Links",
        "",
        "- [Official Changelog](https://code.claude.com/docs/en/changelog)",
        "- [GitHub Releases](https://github.com/anthropics/claude-code/releases)",
        "- [npm](https://www.npmjs.com/package/@anthropic-ai/claude-code)",
        "",
        "---",
        "",
        "<p align=\"center\">Made with Claude Code by <a href=\"https://github.com/tryumanshow\">@tryumanshow</a></p>",
    ])
    return "\n".join(lines) + "\n"


def generate_html(entries: list[dict]) -> str:
    """Generate a self-contained HTML dashboard."""
    rows = ""
    for e in entries:
        cmds = _cmds_html(e["commands"])
        cmd_context = {c["name"]: c["context"] for c in e["commands"]} if e["commands"] else None
        feats_en_html = _feat_html(e["features"], cmd_context)
        feats_ko_html = _feat_html(e.get("features_ko", e["features"]), cmd_context)

        cls = ' class="has-commands"' if e["commands"] else ""
        rows += (
            f'    <tr{cls}>'
            f'<td class="mono">v{e["version"]}</td>'
            f'<td class="nowrap">{e["date"] or "—"}</td>'
            f'<td class="cmds">{cmds}</td>'
            f'<td class="feats">'
            f'<div class="feat-en">{feats_en_html}</div>'
            f'<div class="feat-ko" style="display:none">{feats_ko_html}</div>'
            f'</td>'
            f'</tr>\n'
        )

    updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    total = len(entries)
    with_cmds = sum(1 for e in entries if e["commands"])

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claude Code Changelog Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0a0a0b;
    --surface: #141417;
    --surface-hover: #1a1a1f;
    --border: #27272a;
    --border-subtle: #1e1e22;
    --text: #fafafa;
    --text-secondary: #a1a1aa;
    --text-muted: #71717a;
    --accent: #d4a574;
    --accent-dim: rgba(212,165,116,0.08);
    --accent-border: rgba(212,165,116,0.25);
    --green: #4ade80;
    --blue: #60a5fa;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }}
  .container {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 2.5rem 2rem;
    flex: 1;
  }}
  /* Header */
  header {{
    margin-bottom: 2.5rem;
  }}
  .header-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }}
  header h1 {{
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.02em;
  }}
  header h1 .cc {{ color: var(--accent); }}
  .badge {{
    font-size: 0.7rem;
    font-weight: 500;
    padding: 0.25rem 0.6rem;
    border-radius: 100px;
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid var(--accent-border);
  }}
  .meta {{
    color: var(--text-muted);
    font-size: 0.8rem;
  }}
  .meta a {{
    color: var(--text-secondary);
    text-decoration: none;
  }}
  .meta a:hover {{ color: var(--accent); text-decoration: underline; }}
  /* Stats */
  .stats {{
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
  }}
  .stat {{
    background: var(--surface);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 1rem 1.5rem;
    flex: 1;
    min-width: 0;
  }}
  .stat .num {{
    font-size: 1.8rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: var(--accent);
    line-height: 1.2;
  }}
  .stat .label {{
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 0.2rem;
  }}
  /* Search */
  .toolbar {{
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    align-items: center;
  }}
  .toolbar input[type="text"] {{
    flex: 1;
    padding: 0.55rem 1rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-size: 0.85rem;
    font-family: inherit;
    outline: none;
    transition: border-color 0.15s;
  }}
  .toolbar input[type="text"]:focus {{ border-color: var(--accent); }}
  .toolbar input[type="text"]::placeholder {{ color: var(--text-muted); }}
  .toggle {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
    color: var(--text-secondary);
    font-size: 0.8rem;
    cursor: pointer;
    white-space: nowrap;
    user-select: none;
  }}
  .toggle input {{ accent-color: var(--accent); }}
  .lang-btn {{
    padding: 0.4rem 0.8rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-family: inherit;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }}
  .lang-btn:hover {{
    border-color: var(--accent);
    color: var(--accent);
  }}
  /* Table */
  .table-wrap {{
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    overflow: hidden;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
  }}
  thead th {{
    position: sticky;
    top: 0;
    z-index: 10;
    background: var(--surface);
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.68rem;
    letter-spacing: 0.08em;
  }}
  tbody td {{
    padding: 0.65rem 1rem;
    border-bottom: 1px solid var(--border-subtle);
    vertical-align: top;
  }}
  tbody tr:hover {{ background: var(--surface-hover); }}
  tbody tr.has-commands {{
    background: var(--accent-dim);
  }}
  tbody tr.has-commands:hover {{
    background: rgba(212,165,116,0.12);
  }}
  tbody tr.has-commands td:first-child {{
    border-left: 3px solid var(--accent);
  }}
  .mono {{
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
    font-size: 0.8rem;
  }}
  .nowrap {{
    white-space: nowrap;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--text-secondary);
  }}
  .cmd-item {{
    display: inline-flex;
    align-items: center;
    gap: 0.2rem;
    margin: 0.1rem 0.15rem;
  }}
  .cmds code {{
    display: inline-block;
    background: rgba(212,165,116,0.12);
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--accent);
    border: 1px solid var(--accent-border);
  }}
  .cmd-badge {{
    font-size: 0.55rem;
    font-weight: 600;
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
    letter-spacing: 0.03em;
    line-height: 1;
    white-space: nowrap;
  }}
  .cmd-badge.new {{
    background: rgba(74,222,128,0.15);
    color: var(--green);
    border: 1px solid rgba(74,222,128,0.3);
  }}
  .cmd-badge.fixed {{
    background: rgba(96,165,250,0.15);
    color: var(--blue);
    border: 1px solid rgba(96,165,250,0.3);
  }}
  .cmd-badge.removed {{
    background: rgba(248,113,113,0.15);
    color: #f87171;
    border: 1px solid rgba(248,113,113,0.3);
  }}
  .cmd-badge.improved {{
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid var(--accent-border);
  }}
  /* Legend */
  .legend {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    font-size: 0.75rem;
    color: var(--text-muted);
  }}
  .legend-label {{
    font-weight: 600;
    color: var(--text-secondary);
    margin-right: 0.25rem;
  }}
  .legend-desc {{
    margin-right: 0.5rem;
  }}
  /* Command references in features */
  .cmd-ref {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    padding: 0.1rem 0.35rem;
    border-radius: 3px;
    background: rgba(255,255,255,0.05);
    color: var(--text-secondary);
  }}
  .cmd-ref.new {{
    background: rgba(74,222,128,0.1);
    color: var(--green);
  }}
  .cmd-ref.fixed {{
    background: rgba(96,165,250,0.1);
    color: var(--blue);
  }}
  .cmd-ref.removed {{
    background: rgba(248,113,113,0.1);
    color: #f87171;
  }}
  .cmd-ref.improved {{
    background: rgba(212,165,116,0.08);
    color: var(--accent);
  }}
  .feats ul {{
    list-style: none;
    padding: 0;
    margin: 0;
  }}
  .feats li {{
    position: relative;
    padding-left: 1rem;
    margin-bottom: 0.25rem;
    color: var(--text-secondary);
    font-size: 0.8rem;
    line-height: 1.5;
  }}
  .feats li::before {{
    content: '';
    position: absolute;
    left: 0;
    top: 0.55em;
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: var(--text-muted);
  }}
  .dim {{ color: var(--text-muted); }}
  /* Footer */
  footer {{
    border-top: 1px solid var(--border-subtle);
    padding: 1.5rem 2rem;
    text-align: center;
    color: var(--text-muted);
    font-size: 0.75rem;
  }}
  footer a {{
    color: var(--text-secondary);
    text-decoration: none;
  }}
  footer a:hover {{ color: var(--accent); }}
  footer .heart {{ color: var(--accent); }}
  /* Responsive — card layout on mobile */
  @media (max-width: 768px) {{
    html, body {{ overflow-x: hidden; max-width: 100vw; }}
    .container {{ padding: 1rem 0.75rem; max-width: 100vw; overflow-x: hidden; }}
    header h1 {{ font-size: 1.2rem; }}
    .header-top {{ flex-wrap: wrap; gap: 0.3rem; }}
    .meta {{ font-size: 0.7rem; word-break: break-word; }}
    .stats {{ flex-direction: row; gap: 0.5rem; }}
    .stat {{ padding: 0.7rem 0.8rem; }}
    .stat .num {{ font-size: 1.3rem; }}
    .stat .label {{ font-size: 0.6rem; }}
    .toolbar {{ flex-direction: column; gap: 0.5rem; }}
    .toolbar input[type="text"] {{ font-size: 16px; }}
    .table-wrap {{ border: none; border-radius: 0; }}
    table, thead, tbody {{ display: block; width: 100%; }}
    thead {{ display: none; }}
    tbody tr {{
      display: block;
      background: var(--surface);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      margin-bottom: 0.6rem;
      padding: 0.8rem;
      overflow: hidden;
      max-width: 100%;
      word-break: break-word;
    }}
    tbody tr.has-commands {{
      border-left: 3px solid var(--accent);
      background: var(--accent-dim);
    }}
    tbody td {{
      display: block;
      border: none;
      padding: 0;
    }}
    tbody td.mono {{
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 0.15rem;
    }}
    tbody td.nowrap {{
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-bottom: 0.5rem;
    }}
    tbody td.cmds {{ margin-bottom: 0.5rem; overflow-wrap: break-word; }}
    tbody td.cmds .dim {{ display: none; }}
    .cmds code {{
      font-size: 0.72rem;
      padding: 0.12rem 0.35rem;
      margin: 0.1rem 0.1rem;
      word-break: break-all;
    }}
    .feats li {{
      font-size: 0.73rem;
      line-height: 1.4;
      margin-bottom: 0.2rem;
    }}
    .feats .dim {{ display: none; }}
    footer {{ padding: 1rem; font-size: 0.7rem; }}
  }}
  @media (max-width: 360px) {{
    .stats {{ flex-direction: column; }}
    .stat .num {{ font-size: 1.1rem; }}
  }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="header-top">
      <h1><span class="cc">Claude Code</span> Changelog</h1>
      <span class="badge">AUTO-SYNC</span>
    </div>
    <p class="meta" data-i18n-html="meta">
      Updated every 3 hours &middot; Last sync: {updated} &middot;
      <a href="https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md">Source</a> &middot;
      <a href="https://github.com/tryumanshow/claude-code-changelog">Repo</a>
    </p>
  </header>

  <div class="stats">
    <div class="stat"><div class="num">{total}</div><div class="label" data-i18n="stat_total">Total Versions</div></div>
    <div class="stat"><div class="num">{with_cmds}</div><div class="label" data-i18n="stat_cmds">With New Commands</div></div>
    <div class="stat" id="stat-latest"><div class="num">—</div><div class="label" data-i18n="stat_latest">Latest Release</div></div>
  </div>

  <div class="toolbar">
    <input type="text" id="search" placeholder="Search version, command, feature..." data-i18n-placeholder="search_placeholder">
    <label class="toggle"><input type="checkbox" id="cmds-only"> <span data-i18n="cmds_only">Commands only</span></label>
    <button class="lang-btn" id="lang-toggle">한국어</button>
  </div>

  <div class="legend">
    <span class="legend-label" data-i18n="legend_label">Badge</span>
    <span class="cmd-badge new">NEW</span> <span class="legend-desc" data-i18n="legend_new">Added</span>
    <span class="cmd-badge improved">IMP</span> <span class="legend-desc" data-i18n="legend_imp">Improved</span>
    <span class="cmd-badge fixed">FIX</span> <span class="legend-desc" data-i18n="legend_fix">Fixed</span>
    <span class="cmd-badge removed">DEL</span> <span class="legend-desc" data-i18n="legend_del">Removed</span>
  </div>

  <div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th style="width:90px" data-i18n="th_version">Version</th>
        <th style="width:100px" data-i18n="th_date">Date</th>
        <th style="width:200px" data-i18n="th_commands">Commands / Flags</th>
        <th data-i18n="th_features">Key Features</th>
      </tr>
    </thead>
    <tbody id="tbody">
{rows}
    </tbody>
  </table>
  </div>
</div>

<footer>
  Made with <span class="heart">&hearts;</span> by
  <a href="https://github.com/tryumanshow">@tryumanshow</a>
  &middot; Powered by GitHub Actions &middot;
  Data from <a href="https://github.com/anthropics/claude-code">anthropics/claude-code</a>
</footer>

<script>
  const rows = document.querySelectorAll('#tbody tr');
  const search = document.getElementById('search');
  const cmdsOnly = document.getElementById('cmds-only');

  // Latest release date
  const allDates = [...rows].map(r => r.children[1].textContent.trim()).filter(d => d !== '—');
  document.querySelector('#stat-latest .num').textContent = allDates[0] || '—';

  // --- Filter ---
  function filter() {{
    const q = search.value.toLowerCase();
    const onlyCmds = cmdsOnly.checked;
    rows.forEach(row => {{
      const text = row.textContent.toLowerCase();
      const hasCmd = row.classList.contains('has-commands');
      row.style.display = (!q || text.includes(q)) && (!onlyCmds || hasCmd) ? '' : 'none';
    }});
  }}
  search.addEventListener('input', filter);
  cmdsOnly.addEventListener('change', filter);

  // --- i18n ---
  const i18n = {{
    en: {{
      th_version: 'Version',
      th_date: 'Date',
      th_commands: 'Commands / Flags',
      th_features: 'Key Features',
      stat_total: 'Total Versions',
      stat_cmds: 'With New Commands',
      stat_latest: 'Latest Release',
      cmds_only: 'Commands only',
      search_placeholder: 'Search version, command, feature...',
      legend_label: 'Badge',
      legend_new: 'Added',
      legend_imp: 'Improved',
      legend_fix: 'Fixed',
      legend_del: 'Removed',
      meta: 'Updated every 3 hours &middot; Last sync: {updated} &middot; <a href="https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md">Source</a> &middot; <a href="https://github.com/tryumanshow/claude-code-changelog">Repo</a>',
      toggle_label: '한국어',
    }},
    ko: {{
      th_version: '버전',
      th_date: '날짜',
      th_commands: '커맨드 / 플래그',
      th_features: '주요 기능',
      stat_total: '전체 버전 수',
      stat_cmds: '커맨드 추가된 버전',
      stat_latest: '최신 릴리스',
      cmds_only: '커맨드 있는 버전만',
      search_placeholder: '버전, 커맨드, 기능 검색...',
      legend_label: '범례',
      legend_new: '추가',
      legend_imp: '개선',
      legend_fix: '수정',
      legend_del: '삭제',
      meta: '3시간마다 자동 업데이트 &middot; 마지막 동기화: {updated} &middot; <a href="https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md">소스</a> &middot; <a href="https://github.com/tryumanshow/claude-code-changelog">저장소</a>',
      toggle_label: 'English',
    }},
  }};

  let currentLang = localStorage.getItem('cc-lang') || 'en';

  function applyLang(lang) {{
    currentLang = lang;
    localStorage.setItem('cc-lang', lang);
    const t = i18n[lang];
    document.querySelectorAll('[data-i18n]').forEach(el => {{
      const key = el.getAttribute('data-i18n');
      if (t[key]) el.textContent = t[key];
    }});
    document.querySelectorAll('[data-i18n-html]').forEach(el => {{
      const key = el.getAttribute('data-i18n-html');
      if (t[key]) el.innerHTML = t[key];
    }});
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {{
      const key = el.getAttribute('data-i18n-placeholder');
      if (t[key]) el.placeholder = t[key];
    }});
    document.getElementById('lang-toggle').textContent = t.toggle_label;

    // Toggle feature content (en/ko)
    const showEn = lang === 'en';
    document.querySelectorAll('.feat-en').forEach(el => el.style.display = showEn ? '' : 'none');
    document.querySelectorAll('.feat-ko').forEach(el => el.style.display = showEn ? 'none' : '');
  }}

  document.getElementById('lang-toggle').addEventListener('click', () => {{
    applyLang(currentLang === 'en' ? 'ko' : 'en');
  }});

  applyLang(currentLang);
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not RAW_FILE.exists():
        print(f"ERROR: {RAW_FILE} not found. Run the GitHub Action first.")
        return

    text = RAW_FILE.read_text(encoding="utf-8")
    entries, version_bodies = parse_changelog(text)
    print(f"Parsed {len(entries)} versions")

    # Ensure known slash commands are tracked at their first appearance
    enrich_first_appearances(entries, version_bodies)
    total_cmds = sum(len(e["commands"]) for e in entries)
    print(f"Total commands across all versions: {total_cmds}")
    ctx_counts = {}
    for e in entries:
        for c in e["commands"]:
            ctx = c.get("context", "mentioned")
            ctx_counts[ctx] = ctx_counts.get(ctx, 0) + 1
    print(f"Command contexts: {ctx_counts}")

    # Enrich with release dates from GitHub API
    dates = fetch_release_dates()
    for e in entries:
        if not e["date"] and e["version"] in dates:
            e["date"] = dates[e["version"]]
    dated = sum(1 for e in entries if e["date"])
    print(f"Dates resolved: {dated}/{len(entries)}")

    # Translate features to Korean (if API key available)
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        translate_features(entries, openai_key)
    else:
        print("Translation: OPENAI_API_KEY not set, skipping (features_ko = features)")
        for e in entries:
            e["features_ko"] = e["features"]

    # Save JSON
    JSON_FILE.parent.mkdir(parents=True, exist_ok=True)
    JSON_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {JSON_FILE}")

    # Generate README
    readme = generate_readme(entries)
    RELEASES_FILE.write_text(readme, encoding="utf-8")
    print(f"Wrote {RELEASES_FILE}")

    # Generate HTML dashboard
    html = generate_html(entries)
    HTML_FILE.parent.mkdir(parents=True, exist_ok=True)
    HTML_FILE.write_text(html, encoding="utf-8")
    print(f"Wrote {HTML_FILE}")


if __name__ == "__main__":
    main()
