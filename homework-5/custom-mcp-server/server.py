# /// script
# requires-python = ">=3.10"
# dependencies = ["fastmcp"]
# ///
"""Custom MCP server (FastMCP) for Homework 5.

Exposes the text in ``lorem-ipsum.md`` through two MCP primitives:

* Resource  ``lorem://words``  — data that Claude *reads* (by URI).
* Tool      ``read``           — an action that Claude *calls* (with an argument).

Both return exactly ``word_count`` words (default 30) from the same source file.
"""

from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("custom-lorem")

# Source text lives next to this script, so the path works from any cwd.
SOURCE_FILE = Path(__file__).parent / "lorem-ipsum.md"
DEFAULT_WORD_COUNT = 30


def _read_words(word_count: int = DEFAULT_WORD_COUNT) -> str:
    """Return exactly ``word_count`` words from the source file."""
    if word_count < 0:
        raise ValueError("word_count must be zero or greater")
    words = SOURCE_FILE.read_text(encoding="utf-8").split()
    return " ".join(words[:word_count])


@mcp.resource("lorem://words")
def lorem_words() -> str:
    """Resource: the first 30 words of the lorem-ipsum source (default)."""
    return _read_words(DEFAULT_WORD_COUNT)


@mcp.resource("lorem://words/{word_count}")
def lorem_words_n(word_count: int) -> str:
    """Resource template: the first ``word_count`` words of the source."""
    return _read_words(int(word_count))


@mcp.tool
def read(word_count: int = DEFAULT_WORD_COUNT) -> str:
    """Tool: return ``word_count`` words (default 30) from the lorem-ipsum source."""
    return _read_words(word_count)


if __name__ == "__main__":
    mcp.run()  # STDIO transport by default
