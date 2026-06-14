# How to run — Homework 5 MCP servers

**Author:** Anastasia Kopiika

This guide covers the **custom FastMCP server** (`custom-lorem`) in detail, plus how the
other three servers were registered. All commands assume Claude Code CLI (`claude mcp ...`).

---

## Prerequisites

```bash
python3 --version     # 3.10+ recommended (3.9 also works)
uv --version          # if missing: brew install uv
```

`uv` runs the server; `fastmcp` is installed into the run environment.

---

## Custom server: `custom-lorem`

### 1. Install dependencies

```bash
cd custom-mcp-server
uv pip install -r requirements.txt   # installs fastmcp
```

> The script also declares its dependency inline (PEP 723 header in `server.py`), so
> `uv run server.py` can resolve `fastmcp` on its own.

### 2. Verify it starts without errors

```bash
uv run server.py
```

It runs over **STDIO** (no port). It will sit waiting for an MCP client — that's correct.
Press `Ctrl+C` to stop. If it starts with no traceback, the server is fine.

### 3. Connect it to Claude Code

```bash
claude mcp add custom-lorem -- uv run \
  /Users/anastasiakopiika/Documents/FrontEnd/gen-ai-software-engineering/homework-5/custom-mcp-server/server.py
```

This writes the entry into `.mcp.json`. Then **restart Claude Code** and run `/mcp` —
`custom-lorem` should show as **connected**, exposing the `read` tool.

> Manual alternative — add this to `.mcp.json` under `mcpServers`:
> ```json
> "custom-lorem": {
>   "command": "uv",
>   "args": ["run",
>     "/Users/anastasiakopiika/Documents/FrontEnd/gen-ai-software-engineering/homework-5/custom-mcp-server/server.py"]
> }
> ```

### 4. Test the `read` tool

In the Claude Code chat:

1. **10 words:**
   > "Use the custom-lorem MCP `read` tool to return 10 words."

   → returns exactly 10 words.

2. **Default count:**
   > "Now call `read` with the default word_count and show the result."

   → returns the default **30** words, confirming the parameter limits the count.

The server also exposes resources you can read by URI:
`lorem://words` (30 words) and `lorem://words/{word_count}` (e.g. `lorem://words/5`).

---

## The other three servers (already registered)

These are in `.mcp.json`; restart Claude Code and run `/mcp` to confirm **connected**.

**GitHub** (remote, needs a Personal Access Token with `repo` scope):
```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx   # keep out of git
claude mcp add -s user --transport http github https://api.githubcopilot.com/mcp \
  -H "Authorization: Bearer $GITHUB_PERSONAL_ACCESS_TOKEN"
```

**Filesystem** (local, scoped to this folder):
```bash
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem \
  /Users/anastasiakopiika/Documents/FrontEnd/gen-ai-software-engineering/homework-5
```

**Atlassian / Jira** (remote, OAuth in the browser on connect):
```bash
claude mcp add --transport sse atlassian https://mcp.atlassian.com/v1/sse
```

---

## Troubleshooting

- **`custom-lorem` not connected** → check the path in `.mcp.json` is absolute and that
  `uv run server.py` works standalone (step 2).
- **`fastmcp` not found** → re-run `uv pip install -r requirements.txt`, or rely on the
  PEP 723 header (`uv run` resolves it automatically).
- **`/mcp` shows nothing new** → fully restart Claude Code after editing `.mcp.json`.
- **GitHub 401** → the `GITHUB_PERSONAL_ACCESS_TOKEN` env var is unset or the token lacks
  `repo` scope.
