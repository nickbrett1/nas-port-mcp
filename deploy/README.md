# Deploying nas-port-mcp on the Synology NAS

## 1. CI (CircleCI) — one-time setup

1. Add the repo to CircleCI (https://app.circleci.com/projects — "Set Up Project").
2. The pipeline uses the **`common`** context. Create a fine-grained PAT
   (https://github.com/settings/tokens) with **Packages: read & write**.
3. In CircleCI → Organization Settings → Contexts → `common`, add:
   - `GHCR_USERNAME` = `nickbrett1`
   - `GHCR_TOKEN` = the PAT
4. Push to `main` → CI runs `test` (ruff + pytest) then `docker-publish`
   (multi-arch amd64/arm64 to `ghcr.io/nickbrett1/nas-port-mcp`).

> The GHCR package is **private** — the NAS must authenticate to pull it (step 2).

## 2. NAS (Container Manager)

1. **Registry:** Container Manager → Registry → add `ghcr.io` with
   `nickbrett1` / PAT (same token as CI).
2. **Project:** Container Manager → Project → New → import `docker-compose.yml`
   (or paste from the repo). It uses `network_mode: host`, mounts
   `/var/run/docker.sock` **read-only**, and labels Watchtower + Homepage.
3. Optional: set `MCP_PORT` in the project's `.env` (default `3001`).
4. Start. Watchtower will auto-update on new `latest` images.

## 3. Expose on the tailnet

The proxy binds `127.0.0.1:3001` only. Front it with Tailscale Serve:

```bash
tailscale serve --bg 3001
```

or HTTPS on 443:

```bash
tailscale serve --bg --https=443 http://127.0.0.1:3001
```

## 4. Verify

```bash
curl -fsS http://127.0.0.1:3001/healthz   # on the NAS → 200
```

- Homepage widget hits `http://localhost:3001/healthz` — only resolves if the
  Homepage container shares host networking; otherwise point it at the
  `tailscale serve` URL.
- MCP clients (Claude Desktop / VSCode agent / Open WebUI): add a
  **Streamable HTTP** server. Endpoint path: `http://nas:3001/mcp` for
  streamable-http (verify exact path against mcpo docs; SSE variant is `/sse`).

## First-run smoke test (dogfood)

Ask any agent: "run `check_port(3000)` and `suggest_port(preferred: 3000)` via
nas-port-mcp". Expect: 3000 taken by its squatter, and a free port suggestion
with `preferredWasTakenBy` populated. Then `check_port(3001)` should report
mcpo itself as the owner.
