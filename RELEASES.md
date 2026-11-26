# Claude Code Changelog Dashboard

> Checked daily at 06:00 KST | Last updated: 2026-11-26 04:10 UTC

| 버전 | 날짜 | 추가된 커맨드/약어 | 주요 기능 |
|------|------|-------------------|----------|
| **v2.1.332** | 2026-11-25 | — | Added skills from MCP servers (beta). They show as server:skill in the / menu; other skills keep their names / Added a PreSkillShellCommand hook event that can refuse a skill or command's inline sh... |
| **v2.1.331** | 2026-11-23 | — | Added Code Mode support in terminal sessions on Amazon Bedrock, Google Cloud's Agent Platform, Microsoft Foundry and Claude Platform on AWS / Added oidc.groups_jsonpath to the Claude apps gateway, ... |
| **v2.1.330** | 2026-11-20 | `--start-dir` | Added sign-in to organizations managed in Anthropic's Enterprise Admin Console: after claude auth login, Claude Code applies the organization's settings and uses its cloud provider or gateway / Add... |
| **v2.1.329** | 2026-11-19 | — | Added a trust dialog warning that says where a folder's hooks are declared / Added a warning in the conversation, in Claude Desktop and other non-interactive hosts, when hooks in managed settings f... |
| **v2.1.328** | 2026-11-19 | `--repository-folder`, `--hook-label`, `--metadata` | Added auto mode for Claude Opus 4.6 and Sonnet 4.6 on Amazon Bedrock, Google Cloud's Agent Platform, Microsoft Foundry and Claude apps gateway; interactive sessions with no permission mode start in... |
| **v2.1.327** | 2026-11-17 | — | Added a confirmation before /install-github-app changes a repository / Added claude mcp add-json <name> - to read the server's JSON from stdin, so tokens can stay off the command line; not availabl... |
| **v2.1.326** | 2026-11-16 | — | Added support for turning on Code Mode while agent teams are enabled; if you already turned it on, sessions with teams on now start in Code Mode / Added a startup warning when an --allowedTools, --... |
| **v2.1.325** | 2026-11-13 | — | Added a spinner tip in VS Code and similar integrated terminals about re-running a notebook cell, shown once Claude has read or edited a Jupyter notebook / Added a line under the error shown when y... |
| **v2.1.323** | 2026-11-12 | — | Added Code Mode, an experimental opt-in in which Claude writes JavaScript to call its tools; see https://code.claude.com/docs/en/code-mode to turn it on, or to turn it off for an organization / Add... |
| **v2.1.322** | 2026-11-10 | — | Added fast mode on Vertex in the global, us and eu regions, falling back to standard speed if Vertex refuses it |
| **v2.1.321** | 2026-11-09 | — | Added Claude Fable 5.2 (claude-fable-5-2), now the default Fable model — 1M context, $8/$40 per Mtok with $0.20/Mtok cache reads / Added --settings <file> to claude remote-control, which applies a ... |
| **v2.1.319** | 2026-11-06 | — | Added support for MCP tasks in the terminal: when an MCP server runs a tool call as a task, Claude Code moves it to the background right away and tells Claude the result when it finishes / Added th... |
| **v2.1.318** | 2026-11-04 | `--release-idle-session-min` | Added a record of your answer when Claude Code asks to turn on the mods it writes in a session / Added assume_role on mantle upstreams of the Claude apps gateway, for a role in another AWS account ... |
| **v2.1.317** | 2026-11-03 | — | Added a warning to /schedule when a new cloud scheduled task gets connectors you did not ask for, with how to remove them / Added a check that asks before a web or shell tool call sends your accoun... |
| **v2.1.316** | 2026-10-31 | — | Added CLAUDE_CODE_DISABLE_ULTRATHINK, which turns the ultrathink keyword off / Added pooled group budgets to the Claude apps gateway: one monthly budget that a group's members share, on top of each... |
| **v2.1.314** | 2026-10-30 | — | Added permissions.blockWritesOutsideWorkingDirectories: Write, Edit and NotebookEdit refuse paths outside the working directories in every permission mode / Added an optional groups list to Claude ... |
| **v2.1.312** | 2026-10-27 | — | Added oidc.user_id_claim to the Claude apps gateway, to identify people by an id_token claim other than sub, such as Microsoft Entra ID's oid / Added click to send: in fullscreen, clicking the "to ... |
| **v2.1.311** | 2026-10-26 | `--hold-idle-file`, `--max-hold-min` | Added --hold-idle-file and --max-hold-min to self-hosted-runner, to keep an idle session while your host reports processes it left running / Added a tip for the Explanatory output style, shown when... |
| **v2.1.310** | 2026-10-23 | — | Added the Monitor tool and plugin monitors on Bedrock, Vertex, and Foundry, and when telemetry or nonessential traffic is disabled; long foreground sleeps are now blocked there too / Windows: Fixed... |
| **v2.1.309** | 2026-10-22 | — | Fixed sandboxed commands and auto-accepted edits being able to modify the MCP config file passed with --mcp-config / Fixed ctrl+o not showing messages from other agents and sessions that are still ... |
| **v2.1.308** | 2026-10-22 | — | Bug fixes and reliability improvements |
| **v2.1.307** | 2026-10-21 | — | Added /claude-api api-version to move Claude API code to API version 2026-10-21 / Added the claude_code.safety_event OpenTelemetry event for each tool call a permission rule, auto mode, a safety ch... |
| **v2.1.306** | 2026-10-21 | — | Fixed claude -p inside cloud sessions reporting "Not logged in" when started without the session's environment variables / Fixed an API error being replaced by "prompt is too long", and an unneeded... |
| **v2.1.305** | 2026-10-20 | — | Added sandbox.allowNestedUserNamespaces so sandboxed commands on Linux can create user namespaces (Chromium, rootless podman); this lets them get around the sandbox's file protections / Added CLAUD... |
| **v2.1.304** | 2026-10-19 | `/auto-mode-setup` | Added a transcript line when a plugin that runs first skips one of your mod's hooks, naming the event and the plugin / Added decider: "person" to a mod's tool.check answer: only the permission dial... |
| **v2.1.303** | 2026-10-18 | — | Bug fixes and reliability improvements |
| **v2.1.302** | 2026-10-16 | `/design-sync`, `/design-login` | Added CLAUDE_CODE_AUTO_MODE_MODEL to choose the model the client-side auto mode classifier uses; it does not change the model for server-side auto mode / Added an Idle compaction row to /config for... |
| **v2.1.301** | 2026-10-15 | — | Added CLAUDE_CODE_RETRY_WATCHDOG_MAX_USAGE_LIMIT_WAIT_MS so unattended retry mode (CLAUDE_CODE_RETRY_WATCHDOG) ends a request at a usage limit that resets too far away instead of waiting / Added Op... |
| **v2.1.300** | 2026-10-14 | — | Added virtualText to a mod's prompt decorations: text drawn in the prompt box that never enters the draft or the submitted prompt / Added cache_creation_5m_tokens and cache_creation_1h_tokens to th... |
| **v2.1.299** | 2026-10-14 | `--shutdown-drain-sec`, `--disallow-tools` | Added CLAUDE_CODE_DISABLE_FILE_MENTIONS environment variable: Claude gets the paths of @ file mentions to read with its file tools, not the files' contents / Added idle compaction in the terminal: ... |
| **v2.1.296** | 2026-10-09 | — | Added a code key to the Claude apps gateway's managed.policies[]: the same settings as cli, also applied in Claude Desktop's Code tab; beside desktop, it turns on Claude Desktop's gateway mode / Ad... |
| **v2.1.295** | 2026-10-08 | `--strict` | Added onFailure: "block" for command and HTTP hooks: a hook that can't start, times out, or exits with an unexpected code blocks the action instead of letting it through / Added Program Status Prot... |
| **v2.1.294** | 2026-10-08 | — | Fixed prompt and agent hooks written as instructions (such as "Block commands that...") allowing what they should block / Improved how prompt hooks on Stop and SubagentStop written as instructions ... |
| **v2.1.293** | 2026-10-07 | — | Added Claude Haiku 5.5 (claude-haiku-5-5), now the default Haiku model on the Anthropic API — 1M context, $0.10/$0.50 per Mtok ($0.50/$2.50 for prompts over 100K) / Added agentType to the subagentS... |
| **v2.1.292** | 2026-10-06 | `--marketplace` | Added --marketplace <source> to claude plugin install: adds the marketplace if needed, under the same policy checks as claude plugin marketplace add, then installs the plugin from it / Added an eff... |
| **v2.1.291** | 2026-10-06 | — | Fixed a regression in 2.1.290 where cloud sessions could drop answers to permission prompts / Fixed a regression in 2.1.288 where the last messages of a session could be lost when quitting |
| **v2.1.290** | 2026-10-05 | — | Added serverToolUses to the result of a mod's turn.step hook: the tool calls the API ran itself (the advisor), each with its id, name, input, start and end / Added agentId to the tool.check event o... |
| **v2.1.289** | 2026-10-03 | — | [VSCode] Reverted a 2.1.288 change to claude auth status that may have made sign-outs more frequent / Fixed plugin list, plugin eval and plugin update showing a stale copy of a plugin installed fro... |
| **v2.1.288** | 2026-10-02 | `--max-findings` | Added $.ui.selection() for mods: returns the text you last selected in fullscreen mode and, when the selection lies within one transcript row, that row / Added a built-in gh api to cloud sessions w... |
| **v2.1.287** | 2026-10-01 | — | Added Claude Mods: plugins may now modify deeper behavior / Added You should know, a built-in mod where a side agent watches your back and flags things you or Claude might miss. Turn it on with /pl... |
| **v2.1.286** | 2026-09-30 | — | Added a count such as "2 of 5" to the permission prompt when several permission requests stack up / Added mouse support for the "N more" rows of lists in fullscreen mode: click one to jump to that ... |
| **v2.1.285** | 2026-09-29 | `--desktop`, `--values-stdin`, `--config` | Added CLAUDE_CODE_DISABLE_WEB_FETCH environment variable to turn off the WebFetch tool / Added claude --desktop to open the Claude desktop app on the current directory, or on a session with --conti... |
| **v2.1.284** | 2026-09-28 | `/rate-limit-options` | Added Claude Sonnet 5.5 (claude-sonnet-5-5), now the default Sonnet model on the Anthropic API — 1M context, $2/$10 per Mtok with $0.20/Mtok cache reads / Added a "Yes, but ask again next time" ans... |
| **v2.1.283** | 2026-09-25 | — | Added x-claude-code-prompt-id to the gateway hint headers so LLM gateways can group the requests that serve one user prompt; opt in with CLAUDE_CODE_GATEWAY_HINT_HEADERS=1 / Added availableModelsMa... |
| **v2.1.282** | 2026-09-24 | — | Added a maxProseWidth setting that caps the width of Claude's prose in wide terminals while tables and code blocks keep the full width / Added a startup notice, and /status and claude doctor entrie... |
| **v2.1.281** | 2026-09-23 | — | Added Claude apps gateway support for newer Claude Desktop keys in desktop policy blocks, including blockReadsOutsideWorkingDirectories and disableBypassPermissionsMode / Added assume_role on Claud... |
| **v2.1.280** | 2026-09-22 | — | Added Claude Opus 5.5 (claude-opus-5-5), now the default Opus model — 1M context, $4/$20 per Mtok with $0.20/Mtok cache reads / Added mouse support to more lists in fullscreen mode: the wheel scrol... |
| **v2.1.278** | 2026-09-19 | — | Added an Auto mode server row to /status showing whether this session's auto mode classifier runs on the server |
| **v2.1.277** | 2026-09-18 | — | Added AGENTS.md support: in a project with no CLAUDE.md, Claude Code reads AGENTS.md instead; change it under "Project instructions" in /config / Added CLAUDE_GATEWAY_PROXY_IS_EGRESS_BOUNDARY=1 for... |
| **v2.1.276** | 2026-09-18 | — | Fixed every request failing with 400 … Input tag 'advisor_20260301' when ANTHROPIC_BASE_URL points at a proxy or gateway (2.1.275 regression) |
| **v2.1.275** | 2026-09-17 | — | Added the signed-in account to Claude apps gateway sign-in: when the gateway names it, you confirm it before the credential is saved, and /status shows it / Added a send-now key (ctrl+enter, or ctr... |
| **v2.1.274** | 2026-09-17 | — | Added a visible warning when memory usage is critical, with steps to free memory or restart safely / Added CLAUDE_CODE_MCP_STARTUP_WAIT_MS to bound how long the first non-interactive turn waits for... |
| **v2.1.273** | 2026-09-15 | — | Added x-claude-code-request-class, x-claude-code-agent-type, x-claude-code-prev-tool-durations, x-claude-code-compaction and x-claude-code-context-compacted request headers for LLM gateways; opt in... |
| **v2.1.272** | 2026-09-15 | — | Bug fixes and reliability improvements |
| **v2.1.271** | 2026-09-14 | `--drain-marker-file`, `--accept-command` | Added fast mode in Claude Code Remote sessions (cloud and self-hosted runners): the host's fast-mode setting or /fast typed in the session applies where your organization allows it / Added mouse su... |
| **v2.1.270** | 2026-09-12 | — | Fixed read-only git commands in Bash unexpectedly asking for permission after a session had been running for a while (regression in 2.1.269) |
| **v2.1.269** | 2026-09-11 | — | Added claude plugin eval: run a plugin's eval suite against Claude Code and get scored, reproducible results (JSON + HTML report); see claude plugin eval --help / Added /output-style [name] to list... |
| **v2.1.268** | 2026-09-10 | `--remove-session-state` | Added to the Claude apps gateway: with pricing: set in gateway.yaml, signed-in Claude Code clients receive the same rates through managed settings, so /cost and telemetry match the spend meter / Ad... |
| **v2.1.267** | 2026-09-09 | `--system-prompt-snapshot` | Added maxEffortLevel setting (top-level or per model under modelSettings): caps the effort level on every provider, including Bedrock, Vertex and Foundry; users can still pick a lower level / Added... |
| **v2.1.266** | 2026-09-08 | — | Fixed a 2.1.265 regression affecting LLM-gateway and proxy setups: the undocumented CLAUDE_CODE_USE_GATEWAY environment variable, previously ignored unless ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOK... |
| **v2.1.265** | 2026-09-08 | — | Added user.email and user.groups to the telemetry Claude Desktop and Cowork send through a Claude apps gateway, matching terminal sessions / Added support for pointing --plugin-dir at a folder of p... |
| **v2.1.263** | 2026-09-06 | — | Bug fixes and reliability improvements |
| **v2.1.261** | 2026-09-04 | `--append-subagent-system-prompt-file`, `/skill-doctor` | Added an "Organization policy" line to /status and claude doctor that says why your organization's policy could not be loaded, such as a proxy not passing the endpoint through / Added bashOutputMax... |
| **v2.1.260** | 2026-09-03 | — | Added a diff panel that opens beside the conversation in fullscreen mode and shows your uncommitted changes as Claude edits; toggle it with /diff / Added a likely cause for prompt-cache misses (e.g... |
| **v2.1.259** | 2026-09-02 | `--permission-prompts` | Added managedMcpServers managed setting: organizations can provide HTTP/SSE MCP servers to every user (same entry shape as .mcp.json); entries that name a command to run are skipped / Added --permi... |
| **v2.1.258** | 2026-09-01 | — | Fixed Claude Code failing to launch on macOS 12 (Monterey), a regression introduced in 2.1.255 / Fixed remote and scheduled sessions failing with "user messages must have non-empty content" after a... |
| **v2.1.257** | 2026-09-01 | — | Added Claude Fable 5.1 (claude-fable-5-1), now the default Fable model — 1M context, $10/$50 per Mtok with $0.25/Mtok cache reads / Added "Time format" (timeFormat) and timeZone settings: 12-hour, ... |
| **v2.1.252** | 2026-08-31 | — | Fixed Bash commands failing with "task output swap refused (tasks dir moved or linked)" on some Macs / Fixed "always allow" not saving in a project that has no .claude/settings.local.json yet / Fix... |
| **v2.1.251** | 2026-08-28 | — | Added PreModelSwitch and PostModelSwitch hook events (block, confirm, or annotate a model switch); SessionStart resume hooks now receive session staleness and the estimated re-cache cost / Added li... |
| **v2.1.250** | 2026-08-28 | — | Bug fixes and reliability improvements |
| **v2.1.248** | 2026-08-27 | `--restricted`, `--client-label` | Added --restricted (or CLAUDE_CODE_RESTRICTED=1): removes the built-in tools that run commands or code and WebFetch (unless named in --tools), keeps file tools inside the working directory, refuses... |
| **v2.1.247** | 2026-08-26 | — | Added the SendFeedback tool: when something goes wrong in a session, Claude can draft a feedback report for you to review and send from /feedback (turn off with the feedbackDrafts setting) / Added ... |
| **v2.1.246** | 2026-08-25 | — | Added a startup warning for Bash allow rules with a wildcard before the subcommand (e.g. Bash(git * main)), since they also match options inserted before the subcommand / Added an Auto mode tab to ... |
| **v2.1.245** | 2026-08-25 | — | Fixed a crash on startup on Linux distributions that ship glibc 2.44 (for example Arch Linux, CachyOS and Fedora Rawhide) |
| **v2.1.243** | 2026-08-24 | — | Added a Loops breakdown to /usage: per-loop run count, total tokens, tokens per run, and last run, so runaway or chatty /loop tasks are easy to spot / Added modelPicker setting: curate the /model p... |
| **v2.1.241** | 2026-08-23 | — | Bug fixes and reliability improvements |
| **v2.1.240** | 2026-08-22 | — | Bug fixes and reliability improvements |
| **v2.1.239** | 2026-08-21 | — | Cost estimates (/cost, status line, --max-budget-usd) now include the 1.1× US-only-inference premium for data-residency workspaces / Added the one-time fullscreen renderer offer on Bedrock, Vertex,... |
| **v2.1.238** | 2026-08-20 | `--defer-shutdown-max-min`, `--proxy-authorization-command`, `--proxy-authorization-file` | Added a keybindingFlavor setting: set it to "readline" to make Ctrl+W in the prompt delete back to the previous whitespace, as in Bash; the default ("classic") is unchanged / Plugin marketplaces: h... |
| **v2.1.237** | 2026-08-20 | — | Added a built-in "Concise" output style: Claude leads with results and skips preamble and narration, while doing the work just as thoroughly. Select it under Output style in /config. |

---

## How it works

- GitHub Actions checks [anthropics/claude-code CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) daily at 06:00 KST
- Python script parses new entries and updates this table + [dashboard](https://tryumanshow.github.io/claude-code-changelog)

## Links

- [Official Changelog](https://code.claude.com/docs/en/changelog)
- [GitHub Releases](https://github.com/anthropics/claude-code/releases)
- [npm](https://www.npmjs.com/package/@anthropic-ai/claude-code)

---

<p align="center">Made with Claude Code by <a href="https://github.com/tryumanshow">@tryumanshow</a></p>
