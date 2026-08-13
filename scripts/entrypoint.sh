#!/usr/bin/env bash
# nas-port-mcp entrypoint: run the FastMCP server (stdio) behind mcpo
# (Streamable HTTP). Host networking means mcpo binds directly on the host.
# We bind 0.0.0.0 so the port is reachable on all host interfaces (tailnet,
# LAN, localhost); front with `tailscale serve` for tailnet-only exposure.
set -euo pipefail

: "${MCP_PORT:=3001}"

# mcpo 0.0.x CLI: no --transport flag. Load the stdio server from the config
# file (same pattern as igdb-mcp). The server command lives in /app/config.json.
exec mcpo \
  --config /app/config.json \
  --host 0.0.0.0 \
  --port "${MCP_PORT}"
