# Research Notes — context7 queries (Agent 2, code generation)

These are the context7 lookups made **while building the pipeline**. Each entry records what was
searched, the library ID context7 returned, and the concrete pattern applied in the code.

---

## Query 1: Decimal / monetary rounding for settlement

- **Search:** "decimal Decimal quantize ROUND_HALF_UP two decimal places for monetary rounding"
- **context7 library ID:** `/python/cpython` (Doc/library/decimal.rst)
- **What it returned:** `ROUND_HALF_UP` = "round to nearest with ties going away from zero", and the
  canonical money pattern `Decimal('3.214').quantize(TWOPLACES)` where `TWOPLACES = Decimal('0.01')`.
  Also confirmed that arithmetic like `a * b` keeps full precision and you must call `.quantize()`
  explicitly to pin a fixed number of decimal places.
- **Applied:** In `agents/settlement_processor.py` the fee and net amounts are quantized with
  `.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)` (2dp), and `Decimal("1")` for JPY (0dp,
  zero-decimal currency). This guarantees deterministic, banker-safe rounding instead of `float`.

---

## Query 2: FastMCP — defining tools, resources, and STDIO transport

- **Search:** "define tool and resource with decorator, run server over stdio"
- **context7 library ID:** `/prefecthq/fastmcp` (docs/servers/resources.mdx, docs/deployment/running-server.mdx)
- **What it returned:** the `FastMCP("name")` constructor, the `@mcp.tool` and `@mcp.resource("uri://...")`
  decorators (resource functions return a `str`, e.g. `json.dumps(...)`), and that `mcp.run()` with no
  arguments uses **STDIO transport** — the client spawns the server per session, so the server must not
  rely on staying resident.
- **Applied:** `mcp/server.py` (Task 4) uses `@mcp.tool` for `get_transaction_status` /
  `list_pipeline_results`, `@mcp.resource("pipeline://summary")` for the run summary, and
  `mcp.run()` for STDIO so it matches the `mcp.json` `command/args` launch model.
