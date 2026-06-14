# Homework 5 — MCP Servers

**Author:** Anastasia Kopiika

This homework connects four **MCP (Model Context Protocol)** servers to Claude Code and
demonstrates each one with a concrete request. Three are existing/remote servers; the
fourth is a small custom server built with **FastMCP**.

## What was done

| # | Server | Type | What it does | Screenshot |
|---|--------|------|--------------|------------|
| 1 | **github** | remote (http) | Lists commits, PRs, issues from GitHub | `docs/screenshots/github-mcp-result.png` |
| 2 | **filesystem** | local (npx) | Reads/lists files in `homework-5/` | `docs/screenshots/filesystem-mcp-result.png` |
| 3 | **atlassian** (Jira) | remote (http) | Reads Jira tickets/pages | `docs/screenshots/jira-or-notion-mcp-result.png` |
| 4 | **custom-lorem** | local (FastMCP) | Returns N words from a lorem-ipsum source | `docs/screenshots/custom-mcp-read-tool-result.png` |

All four are registered in [`.mcp.json`](.mcp.json). See [`HOWTORUN.md`](HOWTORUN.md) for
setup and testing steps.

## Resources vs. Tools

These are the two MCP primitives a server can expose — they differ by *who initiates* and *what they do*:

- **Resources** = data Claude **reads**, addressed by a **URI** (like a file or an API
  endpoint). They are passive — the client pulls them by URI, with no side effects.
  Example in the custom server: `lorem://words` (and the template `lorem://words/{word_count}`).

- **Tools** = actions Claude **calls**, with arguments (like running a function or a
  command). They are active — the model decides to invoke them, optionally producing
  side effects. Example in the custom server: `read(word_count: int = 30)`.

In short: a **Resource** answers *"what can I read?"*, a **Tool** answers *"what can I do?"*.

## The custom server (`custom-mcp-server/`)

A minimal FastMCP server named **`custom-lorem`** that reads `lorem-ipsum.md` and returns
exactly `word_count` words (default `30`) from it.

```
custom-mcp-server/
├── server.py         # FastMCP server: 1 tool + 2 resources
├── lorem-ipsum.md    # source text (> 30 words)
└── requirements.txt  # fastmcp
```

It exposes the **same source text** through both primitives so the difference is visible:

- Resource `lorem://words` → first 30 words (default).
- Resource template `lorem://words/{word_count}` → first `word_count` words.
- Tool `read(word_count=30)` → first `word_count` words.

### Demonstrated behaviour

- `read` with `word_count=10` → returns 10 words.
- `read` with no argument → returns the default 30 words.

(See `docs/screenshots/custom-mcp-connected.png` for the tool listed in `/mcp`, and
`docs/screenshots/custom-mcp-read-tool-result.png` for the calls and their results.)

## Folder structure

```
homework-5/
├── README.md                 # this file
├── HOWTORUN.md               # setup & testing instructions
├── TASKS.md                  # original assignment
├── TASK_LIST.md              # detailed checklist (progress)
├── .mcp.json                 # all 4 MCP servers
├── custom-mcp-server/        # the FastMCP custom server
└── docs/screenshots/         # one screenshot per server
```

## Security note

No secret tokens are committed. The GitHub token is referenced via the
`${GITHUB_PERSONAL_ACCESS_TOKEN}` environment variable in `.mcp.json`, and Atlassian uses
browser OAuth on connect.
