#!/usr/bin/env bash
# nas-port-mcp entrypoint: run the FastMCP server (stdio) behind mcpo
# (Streamable HTTP). Host networking means mcpo binds directly on the host's
# 127.0.0.1:${MCP_PORT} — front with `tailscale serve` for tailnet access.
set -euo pipefail

: "${MCP_PORT:=3001}"
: "${MCP_TRANSPORT:=streamable-http}"

if [ "$MCP_TRANSPORT" = "streamable-http" ]; then
  # mcpo streamable-http mode: expects an SSE-capable upstream by default,
  # so point it at our stdio server explicitly.
  exec mcpo \
    --transport streamable-http \
    --host 127.0.0.1 \
    --port "${MCP_PORT}" \
    --server "python -m nas_port_mcp"
else
  exec mcpo \
    --transport sse \
    --host 127.0.0.1 \
    --port "${MCP_PORT}" \
    --server "python -m nas_port_mcp"
fi
