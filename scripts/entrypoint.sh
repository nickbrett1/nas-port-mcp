#!/usr/bin/env bash
# nas-port-mcp entrypoint: run the FastMCP server (stdio) behind mcpo
# (Streamable HTTP). Host networking means mcpo binds directly on the host.
#
# This server has NO auth — the tailnet is the security boundary. By default
# we bind 0.0.0.0 so the MagicDNS hostname (<host>.<tailnet>.ts.net:3001) is
# reachable from tailnet clients like Open WebUI. For strict tailnet-only
# exposure, set MCP_HOST=<tailnet-ip> (e.g. <your-tailnet-ip>) in the NAS .env.
set -euo pipefail

: "${MCP_PORT:=3001}"
: "${MCP_HOST:=0.0.0.0}"

# mcpo 0.0.x CLI: no --transport flag. Load the stdio server from the config
# file (same pattern as igdb-mcp). The server command lives in /app/config.json.
exec mcpo \
  --config /app/config.json \
  --host "${MCP_HOST}" \
  --port "${MCP_PORT}"
