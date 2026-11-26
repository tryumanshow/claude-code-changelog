#!/usr/bin/env python3
"""
Parse Claude Code CHANGELOG.md and generate:
  - data/releases.json  (structured data)
  - RELEASES.md         (markdown table)
  - docs/data.json      (dashboard data; docs/index.html is a static page that loads it)
  - docs/ko.json        (Korean bullets for the dashboard)
"""

import json
import re
import os
import subprocess
import hashlib
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = ROOT / "CHANGELOG_RAW.md"
DATES_CACHE = ROOT / "data" / "release_dates.json"
TRANSLATION_CACHE = ROOT / "data" / "translations_cache.json"
JSON_FILE = ROOT / "data" / "releases.json"
RELEASES_FILE = ROOT / "RELEASES.md"
WEB_DATA_FILE = ROOT / "docs" / "data.json"
WEB_KO_FILE = ROOT / "docs" / "ko.json"
META_FILE = ROOT / "data" / "meta.json"

# A fetch that returns a truncated or wrong file must not wipe the dashboard
MIN_VERSION_RATIO = 0.9


# ---------------------------------------------------------------------------
# 0. Fetch release dates from GitHub API
# ---------------------------------------------------------------------------

def fetch_release_dates(needed: set[str]) -> dict[str, str]:
    """Fetch release dates from GitHub API + npm, with local cache.

    `needed` is the set of versions found in the changelog; npm is only queried
    when at least one of them still has no date after the GitHub pass.
    """
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

    # --- Source 2: npm registry (covers versions that have no GitHub release) ---
    if not needed - cached.keys():
        print("npm registry: skipped (every changelog version already has a date)")
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


HANGUL = re.compile(r"[가-힣]")
TRANSLATE_BATCH_SIZE = 30


def _request_translations(texts: list[str], api_key: str) -> list[str]:
    """One OpenAI call. Returns exactly len(texts) strings or raises."""
    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": (
                "You are a technical translator. Translate English changelog entries to Korean. "
                "Keep code/command/path terms in English. Be concise and natural in Korean."
            )},
            {"role": "user", "content": (
                'Translate every string in "items" to Korean. Reply with a JSON object '
                '{"translations": [...]} holding one translation per item, in the same order.\n\n'
                + json.dumps({"items": texts}, ensure_ascii=False)
            )},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    req = Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    translations = json.loads(result["choices"][0]["message"]["content"])["translations"]
    if not isinstance(translations, list) or len(translations) != len(texts):
        raise ValueError(f"expected {len(texts)} translations, got {len(translations)}")
    return translations


def translate_batch_openai(texts: list[str], api_key: str) -> list[str | None]:
    """Translate English feature texts to Korean.

    Returns one item per input: the Korean text, or None where translation
    failed. A batch whose reply cannot be matched to its inputs is split in
    half and retried, so one bad item never shifts or poisons the others.
    """
    if not texts:
        return []
    try:
        translations = _request_translations(texts, api_key)
    except Exception as e:
        if len(texts) == 1:
            print(f"  Warning: translation failed: {e}")
            return [None]
        print(f"  Warning: batch of {len(texts)} failed ({e}); retrying in halves")
        mid = len(texts) // 2
        return translate_batch_openai(texts[:mid], api_key) + translate_batch_openai(texts[mid:], api_key)
    return [
        t.strip() if isinstance(t, str) and HANGUL.search(t) else None
        for t in translations
    ]


def translate_features(entries: list[dict], api_key: str) -> None:
    """Add 'features_ko' to each entry, using cache + OpenAI API.

    Only real translations are cached. Features that cannot be translated (no
    API key, API failure) are shown in English and retried on the next run.
    """
    cache = load_translation_cache()
    to_translate: list[tuple[int, int, str]] = []  # (entry_idx, feat_idx, text)

    for ei, entry in enumerate(entries):
        entry["features_ko"] = []
        for fi, feat in enumerate(entry["features"]):
            cached = cache.get(_content_hash(feat))
            # An entry equal to its source is a failed translation cached by an older run
            if cached and cached != feat:
                entry["features_ko"].append(cached)
            else:
                entry["features_ko"].append(feat)  # English until translated
                to_translate.append((ei, fi, feat))

    total = sum(len(e["features"]) for e in entries)
    if not to_translate:
        print(f"Translation: all {total} features cached, 0 API calls needed")
        return

    if not api_key:
        print(f"Translation: OPENAI_API_KEY not set — used {total - len(to_translate)} cached, "
              f"fell back to English for {len(to_translate)} uncached features")
        return

    print(f"Translation: {len(to_translate)} new features to translate...")
    translated_count = 0
    for batch_start in range(0, len(to_translate), TRANSLATE_BATCH_SIZE):
        batch = to_translate[batch_start:batch_start + TRANSLATE_BATCH_SIZE]
        translations = translate_batch_openai([t[2] for t in batch], api_key)

        for (ei, fi, original), translated in zip(batch, translations):
            if translated is None:
                continue
            cache[_content_hash(original)] = translated
            entries[ei]["features_ko"][fi] = translated
            translated_count += 1

        # Rate limit: be nice to OpenAI
        if batch_start + TRANSLATE_BATCH_SIZE < len(to_translate):
            time.sleep(1)

    save_translation_cache(cache)
    failed = len(to_translate) - translated_count
    print(f"Translation: {translated_count} translated, {failed} left in English, "
          f"cache now has {len(cache)} entries")


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


def parse_changelog(text: str) -> list[dict]:
    """Return one entry per version, newest first (changelog order)."""
    entries: list[dict] = []
    for version, body in _split_changelog(text):
        commands = extract_commands(body)
        entries.append({
            "version": version,
            "date": extract_date(body),
            "commands": commands,
            "features": extract_features(body, commands),
        })
    return entries


def extract_date(body: str) -> str:
    """Find a release date in the header area of a version section.

    Only the text before the first bullet is considered: dates inside bullets
    ("... API version 2026-10-21", "... until November 30, 2026") describe the
    change, not the release.
    """
    header_lines = []
    for line in body.splitlines():
        if re.match(r"\s*[-*]\s", line):
            break
        header_lines.append(line)
    body = "\n".join(header_lines)
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


BACKTICK_SPAN = re.compile(r"`([^`]+)`")
SLASH_NAME = re.compile(r"/[a-z][a-z0-9-]*")
FLAG_NAME = re.compile(r"(?<![\w-])--[a-z][A-Za-z0-9-]*(?![\w-])")
# Unquoted slash command: not part of a path (`~/x`, `a/b`, `/mnt/c`, `/x.json`) or URL
UNQUOTED_SLASH = re.compile(r"(?<![\w~./:\\<-])(/[a-z][a-z0-9-]*)(?![\w-]|/|\.\w)")
UNQUOTED_FLAG = re.compile(r"(?<![\w-])(--[a-z][A-Za-z0-9-]*)(?![\w-])")
SHORTCUT_PATTERN = re.compile(r"(?<![\w+-])(ctrl|alt|shift)[+\-]([a-z])(?![\w+-])", re.IGNORECASE)

# False positives to exclude: things that look like `/name` but are not commands
COMMAND_BLOCKLIST = {
    # URL path fragments
    "/claude", "/code", "/www", "/com", "/en", "/docs", "/api",
    "/news", "/v1", "/v2", "/ai", "/new", "/downloads", "/frontend",
    "/component", "/claude-code", "/claude-code-sdk", "/metrics", "/json",
    "/wp-json", "/next", "/data", "/src", "/dist", "/node", "/app", "/lib",
    "/index", "/main", "/test", "/spec", "/healthz", "/readyz", "/protocol",
    "/device", "/anthropic", "/platform", "/types", "/repo", "/build",
    # Filesystem roots and mount points
    "/bin", "/usr", "/etc", "/tmp", "/dev", "/home", "/proc", "/var", "/net",
    "/mnt", "/media", "/opt", "/private", "/storage", "/dir", "/path", "/env",
    # Placeholders used in prose ("a `/word` such as ...", "`/skill-a`")
    "/word", "/name", "/command", "/commands", "/skill-a", "/skill-b",
    "/myplugin", "/backticks", "/script", "/builtin",
    # Other tools' switches (`ipconfig /displaydns`)
    "/displaydns",
    # Generic CLI fragments
    "--no", "--the", "--and", "--from", "--to", "--with",
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


CONTEXT_PREFIXES = (
    ("fixed", ("fixed", "fix ")),
    ("removed", ("removed", "remove ")),
    ("improved", (
        "improved", "changed", "enhanced", "updated",
        "security", "deprecated", "reverted",
        "simplified", "renamed", "moved", "switched",
        "reduced", "avoid", "suppressed", "enable ",
        "show ", "stop ", "preserved",
    )),
    ("new", NEW_FEATURE_STARTS),
)
# Leading scope tags: "[VSCode] ", "Windows: ", "Remote Control: ", "Self-hosted runner: "
SCOPE_TAG = re.compile(r"^(?:\[[^\]]+\]\s*|[A-Za-z][\w.-]*(?: [\w.-]+){0,3}:\s+)")


def _context_by_prefix(text: str) -> str | None:
    lower = text.lower()
    for context, starts in CONTEXT_PREFIXES:
        if lower.startswith(starts):
            return context
    return None


def _detect_context(line: str) -> str:
    """Classify a changelog line as new / improved / fixed / removed / mentioned."""
    text = line.strip().lstrip("-* ")
    untagged = SCOPE_TAG.sub("", text)
    context = _context_by_prefix(text) or _context_by_prefix(untagged)
    if context:
        return context
    # "`/cmd` now ...", "Stats screenshot now works" → improved
    if re.search(r"\b(now|no longer)\b", untagged.lower()):
        return "improved"
    return "mentioned"


def _span_candidates(span: str) -> list[str]:
    """Command names inside one backtick span, reduced to their base form.

    `/tui classic` → `/tui`, `--model default` → `--model`,
    `claude --chrome --debug` → `--chrome`, `--debug`. Paths such as `/mnt/c`
    or `/Volumes` and flags of other programs (`git commit --amend`) yield nothing.
    """
    span = span.strip()
    head = span.split()[0] if span else ""
    if SLASH_NAME.fullmatch(head):
        return [head]
    if head.startswith("--") or head == "claude":
        return FLAG_NAME.findall(span)
    return []


def extract_commands(body: str) -> list[dict]:
    """Extract slash commands, CLI flags and keyboard shortcuts from a version body.

    Returns a list of {"name", "context", "summary"}, one per distinct command.
    Names are normalized (base command without arguments, `Ctrl+C` casing) so the
    same command is never listed twice.
    """
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

        # 1. Backtick-quoted commands and flags (most reliable)
        for m in BACKTICK_SPAN.finditer(line):
            for candidate in _span_candidates(m.group(1)):
                _add(candidate, ctx, summary)

        # 2. Unquoted slash commands (older entries have no backticks)
        unquoted = BACKTICK_SPAN.sub(" ", line)
        for m in UNQUOTED_SLASH.finditer(unquoted):
            if len(m.group(1)) > 2:
                _add(m.group(1), ctx, summary)

        # 3. Unquoted flags (only from new-feature lines to avoid noise)
        if ctx == "new":
            for m in UNQUOTED_FLAG.finditer(unquoted):
                if len(m.group(1)) > 3:
                    _add(m.group(1), ctx, summary)

        # 4. Keyboard shortcuts (Ctrl+X, ctrl-b, ...) normalized to `Ctrl+X`
        for m in SHORTCUT_PATTERN.finditer(line):
            _add(f"{m.group(1).capitalize()}+{m.group(2).upper()}", ctx, summary)

    return list(commands.values())


def mark_first_appearances(entries: list[dict]) -> None:
    """Make `new` mean "first time this command shows up in the changelog".

    - A later line such as "Added a footer hint to `/model`" starts with
      "Added", but `/model` is old: every repeat `new` becomes `improved`.
    - A first mention with no fix/improve verb ("`/rewind` a conversation to
      undo code changes") is an introduction: `mentioned` becomes `new`.
    - A first mention inside a fix or improvement stays as is: the command
      shipped earlier without a changelog line.

    `entries` is newest-first, as in the changelog.
    """
    seen: set[str] = set()
    for entry in reversed(entries):
        for cmd in entry["commands"]:
            if cmd["name"] in seen:
                if cmd["context"] == "new":
                    cmd["context"] = "improved"
            else:
                seen.add(cmd["name"])
                if cmd["context"] == "mentioned":
                    cmd["context"] = "new"


def _mention_pattern(names) -> re.Pattern | None:
    """Regex matching any of the command names as a whole token, case-insensitively."""
    names = sorted(names, key=len, reverse=True)
    if not names:
        return None
    alternatives = "|".join(re.escape(n) for n in names)
    return re.compile(rf"(?<![\w/:-])({alternatives})(?![\w-])", re.IGNORECASE)


def _clean_markdown(text: str) -> str:
    """Strip backticks, bold, and markdown links from text."""
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def extract_features(body: str, commands: list[dict] | None = None) -> list[str]:
    """Extract key feature bullet points.

    Rules:
    - Bullets that mention any command listed in the Commands/Flags column are
      ALWAYS included (so readers can see what changed about each command).
    - Non-fix bullets are included up to MAX_NON_FIX.
    - If a version is fix-only (no new/improved bullets and no commands),
      fall back to all bullets.
    """
    MAX_NON_FIX = 8
    mention = _mention_pattern({c["name"] for c in commands} if commands else set())
    result: list[str] = []
    seen: set[str] = set()
    all_items: list[str] = []
    non_fix_count = 0

    for line in body.splitlines():
        line = line.strip()
        if not line.startswith(("-", "*")):
            continue
        text = line.lstrip("-* ").strip()
        if len(text) < 10:
            continue
        cleaned = _clean_markdown(text)
        all_items.append(cleaned)
        has_cmd = bool(mention and mention.search(cleaned))
        is_fix = any(text.lower().startswith(s) for s in SKIP_STARTS)

        if has_cmd:
            if cleaned not in seen:
                result.append(cleaned)
                seen.add(cleaned)
        elif not is_fix and non_fix_count < MAX_NON_FIX:
            if cleaned not in seen:
                result.append(cleaned)
                seen.add(cleaned)
                non_fix_count += 1

    if not result:
        result = all_items[:8]
    return result


# ---------------------------------------------------------------------------
# 2. Generate outputs
# ---------------------------------------------------------------------------

def _has_new_command(entry: dict) -> bool:
    return any(c["context"] == "new" for c in entry["commands"])


def generate_readme(entries: list[dict], updated: str) -> str:
    lines = [
        "# Claude Code Changelog Dashboard",
        "",
        f"> Checked daily at 06:00 KST | Last updated: {updated}",
        "",
        "| 버전 | 날짜 | 추가된 커맨드/약어 | 주요 기능 |",
        "|------|------|-------------------|----------|",
    ]
    for e in entries[:80]:
        ver = f"**v{e['version']}**"
        date = e["date"] or "—"
        new_cmds = [c["name"] for c in e["commands"] if c["context"] == "new"]
        cmds = ", ".join(f"`{n}`" for n in new_cmds) if new_cmds else "—"
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
        "- GitHub Actions checks [anthropics/claude-code CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) daily at 06:00 KST",
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


def generate_web_data(entries: list[dict], updated: str) -> dict:
    """Payload for docs/index.html: every version with typed feature bullets."""
    return {
        "updated": updated,
        "releases": [
            {
                "version": e["version"],
                "date": e["date"],
                "commands": [{"name": c["name"], "context": c["context"]} for c in e["commands"]],
                "features": [{"type": _detect_context(f), "text": f} for f in e["features"]],
            }
            for e in entries
        ],
    }


def generate_web_translations(entries: list[dict]) -> dict[str, list[str]]:
    """Korean bullets per version, index-aligned with `features` in the web data."""
    return {e["version"]: e.get("features_ko", e["features"]) for e in entries}


def _compact_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def render_outputs(entries: list[dict], updated: str) -> dict[Path, str]:
    """Every generated file and its content, stamped with `updated`."""
    return {
        JSON_FILE: json.dumps(entries, indent=2, ensure_ascii=False),
        RELEASES_FILE: generate_readme(entries, updated),
        WEB_DATA_FILE: _compact_json(generate_web_data(entries, updated)),
        WEB_KO_FILE: _compact_json(generate_web_translations(entries)),
        META_FILE: json.dumps({"updated": updated}, indent=2) + "\n",
    }


def previous_version_count() -> int:
    try:
        return len(json.loads(JSON_FILE.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return 0


def previous_updated() -> str:
    try:
        return json.loads(META_FILE.read_text(encoding="utf-8"))["updated"]
    except (OSError, ValueError, KeyError):
        return ""


def write_outputs(entries: list[dict]) -> bool:
    """Write the generated files unless nothing but the timestamp would change.

    Returns True when files were written. The "last updated" stamp only moves
    when content does, so a quiet day produces no diff and no commit.
    """
    unchanged = render_outputs(entries, previous_updated())
    if all(path.exists() and path.read_text(encoding="utf-8") == text
           for path, text in unchanged.items()):
        return False
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    for path, text in render_outputs(entries, now).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"Wrote {path}")
    return True


def main():
    if not RAW_FILE.exists():
        sys.exit(f"ERROR: {RAW_FILE} not found. Run the GitHub Action first.")

    text = RAW_FILE.read_text(encoding="utf-8")
    entries = parse_changelog(text)
    print(f"Parsed {len(entries)} versions")

    previous = previous_version_count()
    if not entries or len(entries) < previous * MIN_VERSION_RATIO:
        sys.exit(f"ERROR: parsed {len(entries)} versions but the last run had {previous}. "
                 f"{RAW_FILE.name} looks truncated or wrong; nothing was written.")

    # "new" only counts where a command shows up for the first time
    mark_first_appearances(entries)
    total_cmds = sum(len(e["commands"]) for e in entries)
    print(f"Total commands across all versions: {total_cmds}")
    ctx_counts = {}
    for e in entries:
        for c in e["commands"]:
            ctx = c.get("context", "mentioned")
            ctx_counts[ctx] = ctx_counts.get(ctx, 0) + 1
    print(f"Command contexts: {ctx_counts}")

    # Release dates: GitHub/npm are authoritative, header date is the fallback
    dates = fetch_release_dates({e["version"] for e in entries})
    for e in entries:
        e["date"] = dates.get(e["version"]) or e["date"]
    dated = sum(1 for e in entries if e["date"])
    print(f"Dates resolved: {dated}/{len(entries)}")

    # Translate features to Korean (always consults cache; API only if key present)
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    translate_features(entries, openai_key)

    if not write_outputs(entries):
        print("No content changes; outputs left untouched")


if __name__ == "__main__":
    main()
