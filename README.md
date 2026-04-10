# Claude Code Changelog Dashboard

[![Auto Sync](https://img.shields.io/badge/sync-daily-blue)](https://github.com/tryumanshow/claude-code-changelog/actions)
[![GitHub Pages](https://img.shields.io/badge/dashboard-live-green)](https://tryumanshow.github.io/claude-code-changelog)

Auto-tracking dashboard for [Anthropic Claude Code](https://github.com/anthropics/claude-code) release history.

Parses the official CHANGELOG.md **daily at 06:00 KST** and extracts new commands, CLI flags, and key features per version.

> **English** | [한국어](README_ko.md)

## Live Dashboard

**https://tryumanshow.github.io/claude-code-changelog**

- 252+ versions fully indexed
- Real-time search by version, command, or feature
- "Commands only" filter (show only versions with new commands)
- English/Korean toggle (persisted via localStorage)
- Dark theme + mobile responsive

## How it works

```
GitHub Actions (daily cron, 06:00 KST)
  |
  v
1. Fetch CHANGELOG.md from anthropics/claude-code (curl)
2. GitHub Releases API + npm registry → collect release dates
3. Python parser → extract versions, commands, features
4. OpenAI API (gpt-4o-mini) → translate key features to Korean (cache-based)
5. Generate RELEASES.md (table) + docs/index.html (dashboard)
6. git commit & push → GitHub Pages auto-deploy
```

## Data Sources

| Source | Purpose | Notes |
|--------|---------|-------|
| [CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) | Versions, commands, feature text | Fetched daily |
| [GitHub Releases API](https://github.com/anthropics/claude-code/releases) | Release dates | Early-exit cache |
| [npm registry](https://www.npmjs.com/package/@anthropic-ai/claude-code) | Date backfill (versions not on GitHub) | Skipped when cache > 200 |
| OpenAI API | Korean translation of key features | Translation cache minimizes API calls |

## Project Structure

```
claude-code-changelog/
├── .github/workflows/
│   └── track-releases.yml       # GitHub Actions (daily cron, 06:00 KST)
├── scripts/
│   └── parse_changelog.py       # Parser + translator + HTML generator
├── data/
│   ├── releases.json            # Structured version data
│   ├── release_dates.json       # Date cache (GitHub API + npm)
│   └── translations_cache.json  # Korean translation cache
├── docs/
│   └── index.html               # GitHub Pages dashboard
├── CHANGELOG_RAW.md             # Raw source (auto-fetched)
├── RELEASES.md                  # Auto-generated version table
├── README.md                    # This file
└── README_ko.md                 # Korean README
```

## Setup (Run your own)

1. Fork this repo
2. Enable GitHub Pages: Settings > Pages > Source: `Deploy from a branch` > Branch: `main` / Folder: `/docs`
3. (Optional) Korean translation: Settings > Secrets > Actions > add `OPENAI_API_KEY`
4. Enable the workflow in the Actions tab

`GITHUB_TOKEN` is automatically provided by GitHub Actions. No setup needed.

## Command Extraction Logic

- **Layer 1**: Extract backtick-quoted patterns from the full changelog body (`` `/effort` ``, `` `--bare` ``, `` `Ctrl+B` ``)
- **Layer 2**: Extract unquoted slash commands (common in older versions without backticks)
- **Layer 3**: 59 known commands list ensures first-appearance tracking
- **Blocklist**: Filters out URL paths (`/api`, `/docs`) and generic flags (`--no`, `--the`)

## Translation Cache

- Each translated feature is stored in `translations_cache.json` keyed by SHA-256 hash
- Only untranslated features call the OpenAI API (batched 30 at a time)
- Initial cost ~$0.02, near-free thereafter

## Links

- [Official Changelog](https://code.claude.com/docs/en/changelog)
- [GitHub Releases](https://github.com/anthropics/claude-code/releases)
- [npm: @anthropic-ai/claude-code](https://www.npmjs.com/package/@anthropic-ai/claude-code)

---

<p align="center">
  Made with <a href="https://claude.ai/claude-code">Claude Code</a> by <a href="https://github.com/tryumanshow">@tryumanshow</a>
</p>
