# nas-port-mcp

A small MCP server for the Synology NAS that answers one question authoritatively:
**"what host port can I use?"** — plus minimal machine info for planning.

Named `nas-port-mcp` deliberately: it is **not** a general-purpose NAS/infra MCP.
It is a read-only port-allocation tool.

Design memo: `memos/nas-port-mcp-design` (Memos). Build log: `memos/nas-port-mcp-buildlog`.

## Tools

| Tool | Description |
|---|---|
| `list_used_ports(proto?, owner_kind?)` | Every bound/reserved host port, with owner attribution |
| `check_port(port)` | Free or taken? If taken, by what (container / host process / DSM) |
| `suggest_port(preferred=3000, start=1024, end=65535)` | **Primary tool** — next free port, deterministic, no scanning. Agents call this **before** writing compose |
| `machine_info()` | Bonus: CPU/RAM/netdata info (wraps netdata's local API, degrades gracefully) |

## Why not a port scan?

- Scans are incomplete: services bound to `127.0.0.1` don't respond to probes but **are** taken.
- Scans answer "what responds?" — we want "what is **allocated**?"
- Scans know nothing about non-listening reservations (DSM's fixed service table).

So this tool merges the host's own sources of truth:

| Source | What it provides | Owner kind |
|---|---|---|
| Docker API (`/var/run/docker.sock`, read-only) | Published ports (`HostIp`/`HostPort` -> container name) | `docker` |
| `ss -tulpn` (host netns) | All listening TCP/UDP sockets + process | `host-process` |
| Static DSM reserved table | Fixed DSM service ports, reserved even when not listening | `dsm-reserved` |

Dedup: Docker wins for the "who" label, host-process is the fallback, DSM reserved is advisory.

## Architecture

```
Agent (Claude Desktop / VSCode agent / Open WebUI)
    │  MCP (Streamable HTTP, Tailscale-only)
    ▼
mcpo (127.0.0.1:3001, host netns)        ← same pattern as igdb-mcp
    │  stdio
    ▼
nas-port-mcp container
    ├─ network_mode: host     → `ss` sees HOST sockets (DSM + host-net containers)
    └─ /var/run/docker.sock:ro → published-port attribution
```

Exposure is loopback + `tailscale serve` (house pattern). The container observes
itself too: after deploy, `check_port(3001)` correctly reports mcpo as the owner.

## Development

Open in VSCode with the Dev Container (Python 3.12, pre-configured).

```bash
# install (dev extras)
pip install -e ".[dev]"
# lint + test (all unit tests use a fake port map — no NAS needed)
ruff check src tests
pytest -v
```

## Deploy

See [deploy/README.md](deploy/README.md). TL;DR: CircleCI builds & publishes the
image to GHCR; import `docker-compose.yml` in DSM Container Manager; `tailscale serve`
fronts port 3001.

## Security posture

- Read-only tool set (no write tools in v1).
- Tailnet-only exposure: loopback bind + Tailscale ACLs (house pattern).
- docker.sock mounted read-only; only read endpoints called.
- `ss` in host netns exposes listening-socket info — acceptable on a single-user tailnet.

## Open questions — resolutions

| Question | Resolution |
|---|---|
| mcpo proxy port | **3001** (3000 is the known squatter; 3001 is the memo's suggested next-free). Verify with `check_port(3001)` on first deploy |
| tailscale socket for `tailscale status` | **Deferred to v1.1** — not a v1 blocker |
| Final DSM reserved table | **Seed table shipped** in `src/nas_port_mcp/dsm_reserved.py`; verify against DSM Control Panel at build time |
| netdata vs /proc | **Netdata-first** with graceful degradation (memo default); no second monitoring stack |

## Acceptance criteria (v1)

- [x] Unit tests green against fake port map (CI)
- [ ] `check_port(3000)` on the real NAS returns `free: false` with correct squatter attribution
- [ ] `suggest_port(preferred=3000)` returns a genuinely free port with `preferredWasTakenBy`
- [ ] DSM-reserved ports (5000/5001/…) reported reserved even when not listening
- [ ] Container runs on the NAS; reachable from VSCode agent and Open WebUI (via mcpo) over the tailnet
- [ ] `machine_info()` works via netdata or degrades gracefully
