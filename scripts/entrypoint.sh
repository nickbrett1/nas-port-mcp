#!/usr/bin/env bash
# nas-port-mcp entrypoint: run the FastMCP server (stdio) behind mcpo
# (Streamable HTTP). Host networking means mcpo binds directly on the host's
# 127.0.0.1:${MCP_PORT} — front with `tailscale serve` for tailnet access.
set -euo pipefail

: "${MCP_PORT:=3001}"

# mcpo 0.0.x CLI: no --transport flag. Load the stdio server from the config
# file (same pattern as igdb-mcp). The server command lives in /app/config.json.
exec mcpo \
  --config /app/config.json \
  --host 127.0.0.1 \
  --port "${MCP_PORT}"
