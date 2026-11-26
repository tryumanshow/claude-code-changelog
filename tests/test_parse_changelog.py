import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import parse_changelog as pc  # noqa: E402


def names(body: str) -> set[str]:
    return {c["name"] for c in pc.extract_commands(body)}


def context_of(entries: list[dict], version: str, name: str) -> str:
    entry = next(e for e in entries if e["version"] == version)
    return next(c["context"] for c in entry["commands"] if c["name"] == name)


# --- dates ------------------------------------------------------------------

def test_date_inside_bullet_is_not_the_release_date():
    body = "\n\n- Added `/claude-api api-version` to move code to API version 2026-10-21\n"
    assert pc.extract_date(body) == ""


def test_prose_date_inside_bullet_is_ignored():
    body = "\n\n- Changed the old plan to stay available until November 30, 2026\n"
    assert pc.extract_date(body) == ""


def test_header_date_is_used():
    assert pc.extract_date("\n**Date:** March 29, 2026\n\n- Added a thing here\n") == "2026-03-29"
    assert pc.extract_date(" (2026-03-29)\n\n- Added a thing here\n") == "2026-03-29"


# --- command extraction -------------------------------------------------------

def test_shortcut_casing_is_unified():
    body = "- Fixed `ctrl+c` twice\n- Fixed Ctrl+c once\n- Improved Ctrl-C handling\n"
    assert names(body) == {"Ctrl+C"}


def test_argument_variants_collapse_to_base_command():
    body = "- Added `/tui classic` and `/tui default`\n- Fixed `/export <name>`\n- Fixed `--model default`\n"
    assert names(body) == {"/tui", "/export", "--model"}


def test_filesystem_paths_are_not_commands():
    body = (
        "- Fixed `rm -r` of a mounted drive (`/Volumes`, `/media`, WSL's `/mnt/c`)\n"
        "- Fixed Edit running out of memory on certain `/proc` files\n"
        "- Fixed rules on symlinked directories (`/etc`, `/tmp`, `/var` on macOS)\n"
        "- Fixed reads of ~/.claude/settings.json and /usr/local/bin/claude\n"
        "- Fixed the `/healthz` endpoint and https://github.com/new links\n"
    )
    assert names(body) == set()


def test_camel_case_flags_stay_whole():
    assert names("- Fixed `--disallowedTools` and `--allowedTools`\n") == {"--disallowedTools", "--allowedTools"}


def test_flags_of_other_programs_are_ignored():
    assert names("- Fixed `git commit --amend` being blocked\n") == set()


def test_flags_after_claude_are_collected():
    assert names("- Fixed `claude --chrome --debug` hanging\n") == {"--chrome", "--debug"}


def test_unquoted_slash_command_in_old_entries():
    assert names("- Added /vim command for vim bindings\n") == {"/vim"}


def test_highest_priority_context_wins_within_a_version():
    cmds = pc.extract_commands("- Fixed `/loop` crashing\n- Added `/loop` command\n")
    assert cmds == [{"name": "/loop", "context": "new", "summary": "Added `/loop` command"}]


# --- first appearance ---------------------------------------------------------

CHANGELOG = """# Changelog

## 1.2.0

- Added a footer hint to `/model`
- Fixed `/cost` rounding

## 1.1.0

- Added `/loop` command
- `/rewind` a conversation to undo code changes

## 1.0.0

- Added `/model` command
- Fixed `/cost` showing zero
"""


@pytest.fixture
def entries():
    result = pc.parse_changelog(CHANGELOG)
    pc.mark_first_appearances(result)
    return result


def test_versions_are_parsed_newest_first(entries):
    assert [e["version"] for e in entries] == ["1.2.0", "1.1.0", "1.0.0"]


def test_new_only_at_first_mention(entries):
    assert context_of(entries, "1.0.0", "/model") == "new"
    assert context_of(entries, "1.2.0", "/model") == "improved"
    assert context_of(entries, "1.1.0", "/loop") == "new"


def test_plain_first_mention_counts_as_new(entries):
    assert context_of(entries, "1.1.0", "/rewind") == "new"


def test_first_mention_in_a_fix_is_not_new(entries):
    assert context_of(entries, "1.0.0", "/cost") == "fixed"
    assert context_of(entries, "1.2.0", "/cost") == "fixed"


# --- features -----------------------------------------------------------------

def test_fix_bullets_are_kept_only_when_they_mention_a_command():
    body = "- Added `/loop` command for recurring prompts\n- Fixed `/loop` crashing on resume\n- Fixed a crash on startup somewhere\n"
    feats = pc.extract_features(body, pc.extract_commands(body))
    assert feats == ["Added /loop command for recurring prompts", "Fixed /loop crashing on resume"]


def test_short_command_name_does_not_match_inside_words():
    body = "- Added `/t` shortcut for the todo list\n- Fixed handling of read/tool output errors\n"
    feats = pc.extract_features(body, [{"name": "/t", "context": "new", "summary": ""}])
    assert feats == ["Added /t shortcut for the todo list"]


def test_highlight_wraps_command_once_and_skips_urls():
    html = pc._highlight_cmds_in_text("Run /loop, see https://x.dev/loop, then /loop again", {"/loop": "new"})
    assert html == 'Run <code class="cmd-ref new">/loop</code>, see https://x.dev/loop, then /loop again'


# --- translation ---------------------------------------------------------------

@pytest.fixture
def cache_file(tmp_path, monkeypatch):
    path = tmp_path / "translations_cache.json"
    monkeypatch.setattr(pc, "TRANSLATION_CACHE", path)
    monkeypatch.setattr(pc.time, "sleep", lambda _: None)
    return path


def make_entries(*features: str) -> list[dict]:
    return [{"version": "1.0.0", "features": list(features)}]


def test_failed_translation_is_not_cached(cache_file, monkeypatch):
    def boom(texts, key):
        raise OSError("network down")

    monkeypatch.setattr(pc, "_request_translations", boom)
    entries = make_entries("Added a thing", "Fixed a thing")
    pc.translate_features(entries, "key")
    assert entries[0]["features_ko"] == ["Added a thing", "Fixed a thing"]
    assert json.loads(cache_file.read_text()) == {}


def test_bad_batch_is_split_so_good_items_still_translate(cache_file, monkeypatch):
    def flaky(texts, key):
        if len(texts) > 1:
            raise ValueError("expected 2 translations, got 1")
        if texts[0] == "Bad item":
            raise ValueError("refused")
        return ["좋은 항목"]

    monkeypatch.setattr(pc, "_request_translations", flaky)
    entries = make_entries("Good item", "Bad item")
    pc.translate_features(entries, "key")
    assert entries[0]["features_ko"] == ["좋은 항목", "Bad item"]
    assert list(json.loads(cache_file.read_text()).values()) == ["좋은 항목"]


def test_untranslated_reply_is_rejected(cache_file, monkeypatch):
    monkeypatch.setattr(pc, "_request_translations", lambda texts, key: list(texts))
    entries = make_entries("Added a thing")
    pc.translate_features(entries, "key")
    assert json.loads(cache_file.read_text()) == {}


def test_english_entry_left_by_an_older_run_is_retried(cache_file, monkeypatch):
    text = "Added a thing"
    cache_file.write_text(json.dumps({pc._content_hash(text): text}))
    monkeypatch.setattr(pc, "_request_translations", lambda texts, key: ["기능을 추가했습니다"])
    entries = make_entries(text)
    pc.translate_features(entries, "key")
    assert entries[0]["features_ko"] == ["기능을 추가했습니다"]


def test_without_api_key_cached_translations_are_still_used(cache_file):
    cache_file.write_text(json.dumps({pc._content_hash("Added a thing"): "기능 추가"}))
    entries = make_entries("Added a thing", "Fixed a thing")
    pc.translate_features(entries, "")
    assert entries[0]["features_ko"] == ["기능 추가", "Fixed a thing"]


# --- pipeline guards -----------------------------------------------------------

@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Point every input/output path at a temp dir and stub the network."""
    for attr, name in [
        ("RAW_FILE", "CHANGELOG_RAW.md"), ("JSON_FILE", "releases.json"),
        ("RELEASES_FILE", "RELEASES.md"), ("HTML_FILE", "index.html"),
        ("META_FILE", "meta.json"), ("TRANSLATION_CACHE", "translations_cache.json"),
    ]:
        monkeypatch.setattr(pc, attr, tmp_path / name)
    monkeypatch.setattr(pc, "fetch_release_dates", lambda needed: {v: "2026-01-01" for v in needed})
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    pc.RAW_FILE.write_text(CHANGELOG)
    return tmp_path


def test_second_run_without_changes_writes_nothing(workspace, capsys, monkeypatch):
    pc.main()
    capsys.readouterr()
    monkeypatch.setattr(Path, "write_text", lambda *a, **k: pytest.fail("output rewritten"))
    pc.main()
    assert "No content changes" in capsys.readouterr().out


def test_new_version_moves_the_timestamp(workspace):
    pc.main()
    pc.META_FILE.write_text('{"updated": "2020-01-01 00:00 UTC"}')
    pc.RAW_FILE.write_text(CHANGELOG.replace("# Changelog\n", "# Changelog\n\n## 1.3.0\n\n- Added `/fresh` command\n"))
    pc.main()
    assert json.loads(pc.META_FILE.read_text())["updated"] != "2020-01-01 00:00 UTC"
    assert len(json.loads(pc.JSON_FILE.read_text())) == 4


def test_truncated_changelog_aborts_without_writing(workspace):
    pc.main()
    before = pc.JSON_FILE.read_text()
    pc.RAW_FILE.write_text("404: Not Found")
    with pytest.raises(SystemExit) as exc:
        pc.main()
    assert "truncated or wrong" in str(exc.value)
    assert pc.JSON_FILE.read_text() == before


def test_missing_changelog_is_an_error(workspace):
    pc.RAW_FILE.unlink()
    with pytest.raises(SystemExit):
        pc.main()
