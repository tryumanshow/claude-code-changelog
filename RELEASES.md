# Claude Code Changelog Dashboard

> Auto-updated every 3 hours | Last sync: 2026-04-04 12:55 UTC

| 버전 | 날짜 | 추가된 커맨드/약어 | 주요 기능 |
|------|------|-------------------|----------|
| **v2.1.92** | 2026-04-04 | `/cost`, `/release-notes`, `--remote-control-session-name-prefix`, `ctrl+e`, `/clear`, `/tag`, `/vim`, `/config` | Added forceRemoteSettingsRefresh policy setting: when set, the CLI blocks startup until remote managed settings are freshly fetched, and exits if the fetch fails (fail-closed) / Added interactive B... |
| **v2.1.91** | 2026-04-02 | `/open`, `--resume`, `/feedback`, `/claude-api` | Added MCP tool result persistence override via _meta["anthropic/maxResultSizeChars"] annotation (up to 500K), allowing larger results like DB schemas to pass through without truncation / Added disa... |
| **v2.1.90** | 2026-04-01 | `/powerup`, `--resume`, `/model`, `/config`, `/resume`, `/displaydns` | Added /powerup — interactive lessons teaching Claude Code features with animated demos / Added CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE env var to keep the existing marketplace cache when git... |
| **v2.1.89** | 2026-04-01 | `--resume`, `alt+s`, `--mcp-config`, `/permissions`, `/path`, `/stats`, `Shift+E`, `Ctrl+B`, `/env`, `/usage`, `/buddy` | Added "defer" permission decision to PreToolUse hooks — headless sessions can pause at a tool call and resume with -p --resume to have the hook re-evaluate / Added CLAUDE_CODE_NO_FLICKER=1 environm... |
| **v2.1.87** | 2026-03-29 | — | — |
| **v2.1.86** | 2026-03-27 | `--resume`, `/feedback`, `--bare`, `/model`, `/plugin`, `/skills` | Added X-Claude-Code-Session-Id header to API requests so proxies can aggregate requests by session without parsing the body / Added .jj and .sl to VCS directory exclusion lists so Grep and file aut... |
| **v2.1.85** | 2026-03-26 | `/loop`, `/open`, `/compact`, `/plugin enable`, `/plugin disable`, `/plugin`, `--worktree`, `--mcp-config`, `shift+e`, `Ctrl+C`, `Ctrl+D` | Added CLAUDE_CODE_MCP_SERVER_NAME and CLAUDE_CODE_MCP_SERVER_URL environment variables to MCP headersHelper scripts, allowing one helper to serve multiple servers / Added conditional if field for h... |
| **v2.1.84** | 2026-03-26 | `/model`, `/clear`, `Ctrl+U`, `ctrl+x`, `ctrl+k`, `--json-schema`, `/voice`, `/mobile`, `/chrome`, `/upgrade`, `/stats`, `Ctrl+S` | Added PowerShell tool for Windows as an opt-in preview. Learn more at https://code.claude.com/docs/en/tools-reference#powershell-tool / Added ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU}_MODEL_SUPPORTS en... |
| **v2.1.83** | 2026-03-25 | `Ctrl+O`, `Ctrl+X`, `Ctrl+E`, `Ctrl+G`, `--mcp-config`, `--print`, `/config`, `--channels`, `Ctrl+B`, `--resume`, `/status`, `Ctrl+F`, `Ctrl+K`, `Ctrl+L`, `Ctrl+U`, `--bare -p`, `--worktree`, `/rewind` | Added managed-settings.d/ drop-in directory alongside managed-settings.json, letting separate teams deploy independent policy fragments that merge alphabetically / Added CwdChanged and FileChanged ... |
| **v2.1.81** | 2026-03-20 | `--bare`, `--settings`, `--channels`, `/btw`, `/rename`, `/exit`, `Ctrl+O` | Added --bare flag for scripted -p calls — skips hooks, LSP, plugin sync, and skill directory walks; requires ANTHROPIC_API_KEY or an apiKeyHelper via --settings (OAuth and keychain auth disabled); ... |
| **v2.1.80** | 2026-03-19 | `--channels`, `--resume`, `/remote-control`, `/sandbox`, `/effort`, `/permissions`, `/plugin install`, `/plugin` | Added rate_limits field to statusline scripts for displaying Claude.ai rate limit usage (5-hour and 7-day windows with used_percentage and resets_at) / Added source: 'settings' plugin marketplace s... |
| **v2.1.79** | 2026-03-18 | `--console`, `/config`, `Ctrl+C`, `/btw`, `/permissions`, `/resume`, `/remote-control` | Added --console flag to claude auth login for Anthropic Console (API billing) authentication / Added "Show turn duration" toggle to the /config menu / CLAUDE_CODE_PLUGIN_SEED_DIR now supports multi... |
| **v2.1.78** | 2026-03-17 | `/plugin uninstall`, `/plugin`, `--resume`, `/sandbox`, `ctrl+u`, `ctrl+d`, `ctrl+k`, `--worktree`, `/model` | Added StopFailure hook event that fires when the turn ends due to an API error (rate limit, auth failure, etc.) / Added ${CLAUDE_PLUGIN_DATA} variable for plugin persistent state that survives plug... |
| **v2.1.77** | 2026-03-17 | `/copy`, `/copy N`, `--resume`, `/feedback`, `Ctrl+D`, `/mcp`, `/fork`, `/branch` | Increased default maximum output token limits for Claude Opus 4.6 to 64k tokens, and the upper bound for Opus 4.6 and Sonnet 4.6 models to 128k tokens / Added allowRead sandbox filesystem setting t... |
| **v2.1.76** | 2026-03-14 | `--name <name>`, `--name`, `--worktree`, `/effort`, `/voice`, `/export`, `--plugin-dir` | Added MCP elicitation support — MCP servers can now request structured input mid-task via an interactive dialog (form fields or browser URL) / Added new Elicitation and ElicitationResult hooks to i... |
| **v2.1.75** | 2026-03-13 | `/color`, `/rename`, `/voice`, `/model`, `/plugin`, `/resume`, `/status`, `--verbose` | Added 1M context window for Opus 4.6 by default for Max, Team, and Enterprise plans (previously required extra usage) / Added /color command for all users to set a prompt-bar color for your session... |
| **v2.1.74** | 2026-03-12 | `/context`, `--agents`, `--model`, `/plugin install`, `/plugin`, `--plugin-dir` | Added actionable suggestions to /context command — identifies context-heavy tools, memory bloat, and capacity warnings with specific optimization tips / Added autoMemoryDirectory setting to configu... |
| **v2.1.73** | 2026-03-11 | `/resume`, `/ide`, `/loop`, `--resume`, `--continue`, `/heapdump`, `/effort`, `/model`, `/output-style`, `/config` | Added modelOverrides setting to map model picker entries to custom provider model IDs (e.g. Bedrock inference profile ARNs) / Added actionable guidance when OAuth login or connectivity checks fail ... |
| **v2.1.72** | 2026-03-10 | `/copy`, `/plan`, `/effort auto`, `/effort`, `/config`, `--continue`, `--compact`, `--effort`, `/clear`, `Ctrl+B`, `/model`, `Ctrl+C`, `Shift+E`, `/anthropic` | Added w key in /copy to write the focused selection directly to a file, bypassing the clipboard (useful over SSH) / Added optional description argument to /plan (e.g., /plan fix the auth bug) that ... |
| **v2.1.71** | 2026-03-07 | `/loop`, `/fork`, `/plugin`, `/permissions`, `--print`, `/plugin uninstall`, `/debug` | Added /loop command to run a prompt or slash command on a recurring interval (e.g. /loop 5m check the deploy) / Added cron scheduling tools for recurring prompts within a session / Added voice:push... |
| **v2.1.70** | 2026-03-06 | `/plugin`, `/security-review`, `/color`, `/color default`, `/color gray`, `/color reset`, `/color none`, `--resume`, `/rename`, `/poll`, `/mcp` | Reduced prompt input re-renders during turns by ~74% / Reduced startup memory by ~426KB for users without custom CA certificates / Reduced Remote Control /poll rate to once per 10 minutes while con... |
| **v2.1.69** | 2026-03-05 | `/claude-api`, `Ctrl+U`, `/remote-control`, `--name`, `--agent`, `/reload-plugins`, `--worktree`, `--model claude-opus-4-0`, `--model claude-opus-4-1`, `/login`, `Shift+E`, `Ctrl+S`, `ctrl+o`, `/stats`, `--setting-sources user`, `/plugin`, `/compact`, `/voice`, `/cost`, `/clear`, `--mcp-config`, `/context`, `Ctrl+O`, `/config`, `--append-system-prompt-file`, `--system-prompt-file`, `/resume` | Added the /claude-api skill for building applications with the Claude API and Anthropic SDK / Added Ctrl+U on an empty bash prompt (!) to exit bash mode, matching escape and backspace / Added numer... |
| **v2.1.68** | 2026-03-04 | `/model` | Opus 4.6 now defaults to medium effort for Max and Team subscribers. Medium effort works well for most tasks — it's the sweet spot between speed and thoroughness. You can change this anytime with /... |
| **v2.1.66** | 2026-03-04 | — | Reduced spurious error logging |
| **v2.1.63** | 2026-02-28 | `/simplify`, `/batch`, `/cost`, `/model`, `/copy`, `/clear` | Added /simplify and /batch bundled slash commands / Project configs & auto memory now shared across git worktrees of the same repository / Added ENABLE_CLAUDEAI_MCP_SERVERS=false env var to opt out... |
| **v2.1.62** | 2026-02-27 | — | — |
| **v2.1.61** | 2026-02-26 | — | — |
| **v2.1.59** | 2026-02-26 | `/memory`, `/copy` | Claude automatically saves useful context to auto-memory. Manage with /memory / Added /copy command to show an interactive picker when code blocks are present, allowing selection of individual code... |
| **v2.1.58** | 2026-02-25 | — | Expand Remote Control to more users |
| **v2.1.56** | 2026-02-25 | — | VS Code: Fixed another cause of "command 'claude-vscode.editor.openLast' not found" crashes |
| **v2.1.55** | 2026-02-25 | — | — |
| **v2.1.53** | 2026-02-25 | `ctrl+f`, `--worktree` | — |
| **v2.1.52** | 2026-02-24 | — | VS Code: Fixed extension crash on Windows ("command 'claude-vscode.editor.openLast' not found") |
| **v2.1.51** | 2026-02-24 | `/model` | Added claude remote-control subcommand for external builds, enabling local environment serving for all users. / Updated plugin marketplace default git timeout from 30s to 120s and added CLAUDE_CODE... |
| **v2.1.50** | 2026-02-20 | `/mcp reconnect`, `/mcp`, `/extra-usage` | Added support for startupTimeout configuration for LSP servers / Added WorktreeCreate and WorktreeRemove hook events, enabling custom VCS setup and teardown when agent worktree isolation creates or... |
| **v2.1.49** | 2026-02-19 | `--worktree`, `Ctrl+F`, `Ctrl+C`, `--scope`, `/model`, `/config`, `--resume`, `/clear` | Added --worktree (-w) flag to start Claude in an isolated git worktree / Subagents support isolation: "worktree" for working in a temporary git worktree / Added Ctrl+F keybinding to kill background... |
| **v2.1.47** | 2026-02-18 | `ctrl+f`, `Shift+D`, `Shift+U`, `/rename`, `/help`, `/model`, `/compact`, `/clear`, `/resume`, `/add-dir`, `Shift+E`, `/resume <session-id>`, `/fork` | Search patterns in collapsed tool results are now displayed in quotes for clarity / Windows: Fixed CWD tracking temp files never being cleaned up, causing them to accumulate indefinitely (anthropic... |
| **v2.1.46** | — | — | Added support for using claude.ai MCP connectors in Claude Code |
| **v2.1.45** | 2026-02-17 | `--add-dir` | Added support for Claude Sonnet 4.6 / Added support for reading enabledPlugins and extraKnownMarketplaces from --add-dir directories / Added spinnerTipsOverride setting to customize spinner tips — ... |
| **v2.1.44** | 2026-02-16 | — | — |
| **v2.1.43** | — | — | — |
| **v2.1.42** | 2026-02-13 | `/resume`, `/compact` | Added one-time Opus 4.6 effort callout for eligible users |
| **v2.1.41** | 2026-02-13 | `/resume`, `/rename` | Added guard against launching Claude Code inside another Claude Code session / Added speed attribute to OTel events and trace spans for fast mode visibility / Added claude auth login, claude auth s... |
| **v2.1.39** | 2026-02-10 | — | — |
| **v2.1.38** | 2026-02-10 | — | Blocked writes to .claude/skills directory in sandbox mode |
| **v2.1.37** | 2026-02-07 | `/fast`, `/extra-usage` | — |
| **v2.1.36** | 2026-02-07 | — | Fast mode is now available for Opus 4.6. Learn more at https://code.claude.com/docs/en/fast-mode |
| **v2.1.34** | 2026-02-06 | — | — |
| **v2.1.33** | 2026-02-06 | `/skills`, `/resume` | Added TeammateIdle and TaskCompleted hook events for multi-agent workflows / Added support for restricting which sub-agents can be spawned via Task(agent_type) syntax in agent "tools" frontmatter /... |
| **v2.1.32** | 2026-02-05 | `--add-dir` | Claude Opus 4.6 is now available! / Added research preview agent teams feature for multi-agent collaboration (token-intensive feature, requires setting CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1) / Cla... |
| **v2.1.31** | 2026-02-04 | — | Added session resume hint on exit, showing how to continue your conversation later / Added support for full-width (zenkaku) space input from Japanese IME in checkbox selection / Reduced layout jitt... |
| **v2.1.30** | 2026-02-03 | `--client-id`, `--client-secret`, `/debug`, `--topo-order`, `--cherry-pick`, `--format`, `--raw`, `/login`, `/upgrade`, `--resume`, `/model`, `Shift+E` | Added pages parameter to the Read tool for PDFs, allowing specific page ranges to be read (e.g., pages: "1-5"). Large PDFs (>10 pages) now return a lightweight reference when @ mentioned instead of... |
| **v2.1.29** | 2026-01-31 | — | — |
| **v2.1.27** | 2026-01-30 | `--from-pr`, `/context` | Added tool call failures and denials to debug logs / Added --from-pr flag to resume sessions linked to a specific GitHub PR number or URL / Sessions are now automatically linked to PRs when created... |
| **v2.1.25** | 2026-01-29 | — | — |
| **v2.1.23** | 2026-01-29 | — | Added customizable spinner verbs setting (spinnerVerbs) / [IDE] Fixed model options displaying incorrect region strings for Bedrock users in headless mode |
| **v2.1.22** | 2026-01-28 | — | — |
| **v2.1.21** | 2026-01-28 | — | Added support for full-width (zenkaku) number input from Japanese IME in option selection prompts / [VSCode] Added automatic Python virtual environment activation, ensuring python and pip commands ... |
| **v2.1.20** | 2026-01-27 | `Ctrl+G`, `--add-dir`, `/context`, `/sandbox`, `/commit-push-pr`, `/copy` | Added arrow key history navigation in vim normal mode when cursor cannot move further / Added external editor shortcut (Ctrl+G) to the help menu for better discoverability / Added PR review status ... |
| **v2.1.19** | 2026-01-23 | `/rename`, `/tag`, `Ctrl+S` | Added env var CLAUDE_CODE_ENABLE_TASKS, set to false to keep the old system temporarily / Added shorthand $0, $1, etc. for accessing individual arguments in custom commands / [SDK] Added replay of ... |
| **v2.1.18** | 2026-01-22 | `/keybindings` | Added customizable keyboard shortcuts. Configure keybindings per context, create chord sequences, and personalize your workflow. Run /keybindings to get started. Learn more at https://code.claude.c... |
| **v2.1.17** | 2026-01-22 | — | — |
| **v2.1.16** | 2026-01-22 | `/compact` | Added new task management system, including new capabilities like dependency tracking / [VSCode] Added native plugin management support / [VSCode] Added ability for OAuth users to browse and resume... |
| **v2.1.15** | 2026-01-21 | `/compact` | Added deprecation notification for npm installations - run claude install or see https://docs.anthropic.com/en/docs/claude-code/getting-started for more options |
| **v2.1.14** | 2026-01-20 | `/feedback`, `/context`, `/config`, `/model`, `/todos`, `/compact`, `/usage` | Added history-based autocomplete in bash mode (!) - type a partial command and press Tab to complete from your bash command history / Added search to installed plugins list - type to filter by name... |
| **v2.1.12** | 2026-01-17 | — | — |
| **v2.1.11** | 2026-01-17 | — | — |
| **v2.1.10** | 2026-01-17 | `--init`, `--init-only`, `--maintenance` | Added new Setup hook event that can be triggered via --init, --init-only, or --maintenance CLI flags for repository setup and maintenance operations / Added keyboard shortcut 'c' to copy OAuth URL ... |
| **v2.1.9** | 2026-01-16 | `Ctrl+G`, `Ctrl+Z` | Added auto:N syntax for configuring the MCP tool search auto-enable threshold, where N is the context window percentage (0-100) / Added plansDirectory setting to customize where plan files are stor... |
| **v2.1.7** | 2026-01-14 | `/model`, `/theme` | Added showTurnDuration setting to hide turn duration messages (e.g., "Cooked for 1m 6s") / Added ability to provide feedback when accepting permission prompts / Added inline display of agent's fina... |
| **v2.1.6** | 2026-01-13 | `/config`, `/doctor`, `/stats`, `Ctrl+G`, `/tasks`, `/mcp` | Added search functionality to /config command for quickly filtering settings / Added Updates section to /doctor showing auto-update channel and available npm versions (stable/latest) / Added date r... |
| **v2.1.5** | 2026-01-12 | — | Added CLAUDE_CODE_TMPDIR environment variable to override the temp directory used for internal temp files, useful for environments with custom temp directory requirements |
| **v2.1.4** | 2026-01-11 | `Ctrl+B` | Added CLAUDE_CODE_DISABLE_BACKGROUND_TASKS environment variable to disable all background task functionality including auto-backgrounding and the Ctrl+B shortcut |
| **v2.1.3** | 2026-01-09 | `/config`, `/doctor`, `/clear` | Merged slash commands and skills, simplifying the mental model with no change in behavior / Added release channel (stable or latest) toggle to /config / Added detection and warnings for unreachable... |
| **v2.1.2** | 2026-01-09 | `Shift+T`, `--agent`, `/tasks`, `/plugins` | Added source path metadata to images dragged onto the terminal, helping Claude understand where images originated / Added clickable hyperlinks for file paths in tool output in terminals that suppor... |
| **v2.1.0** | 2026-01-07 | `Shift+E`, `--resume`, `Ctrl+R`, `Ctrl+B`, `/teleport`, `/remote-env`, `--disallowedTools`, `/plan`, `--tools`, `Ctrl+V`, `Ctrl+O`, `Alt+B`, `Alt+F`, `/path`, `/context`, `--model haiku`, `/hooks`, `/skills`, `/stats` | Added automatic skill hot-reload - skills created or modified in ~/.claude/skills or .claude/skills are now immediately available without restarting the session / Added support for running skills a... |
| **v2.0.76** | 2026-01-07 | — | — |
| **v2.0.75** | 2025-12-20 | — | Minor bugfixes |
| **v2.0.74** | 2025-12-19 | `/terminal-setup`, `/theme`, `ctrl+t`, `/plugins discover`, `/plugins`, `/context` | Added LSP (Language Server Protocol) tool for code intelligence features like go-to-definition, find references, and hover documentation / Added /terminal-setup support for Kitty, Alacritty, Zed, a... |
| **v2.0.73** | 2025-12-19 | `alt+y`, `ctrl+y`, `--session-id`, `--resume`, `--continue`, `--fork-session`, `/theme` | Added clickable [Image #N] links that open attached images in the default viewer / Added alt-y yank-pop to cycle through kill ring history after ctrl-y yank / Added search filtering to the plugin d... |

---

## How it works

- GitHub Actions checks [anthropics/claude-code CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) every 3 hours
- Python script parses new entries and updates this table + [dashboard](https://tryumanshow.github.io/claude-code-changelog)

## Links

- [Official Changelog](https://code.claude.com/docs/en/changelog)
- [GitHub Releases](https://github.com/anthropics/claude-code/releases)
- [npm](https://www.npmjs.com/package/@anthropic-ai/claude-code)

---

<p align="center">Made with Claude Code by <a href="https://github.com/tryumanshow">@tryumanshow</a></p>
