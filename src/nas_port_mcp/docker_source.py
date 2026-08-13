"""Published-port discovery via the Docker API (read-only, unix socket)."""

import httpx

DOCKER_SOCKET = "/var/run/docker.sock"


def collect_docker_ports(socket_path: str = DOCKER_SOCKET) -> list[dict]:
    """Return [{port, proto, name, detail}] of published host ports.

    Only read endpoints are called (GET /containers/json). Containers using
    network_mode: host have no published ports here — their listening sockets
    surface via `ss` instead (they live in the host netns, which we also
    observe). Returns [] on any error so the union model degrades gracefully.
    """
    try:
        transport = httpx.HTTPTransport(uds=socket_path)
        with httpx.Client(transport=transport, timeout=3.0) as client:
            resp = client.get("/containers/json")
            resp.raise_for_status()
            containers = resp.json()
    except Exception:  # noqa: BLE001 -- degrade to [] on any Docker API error
        return []

    ports = []
    for c in containers:
        name = (c.get("Names") or ["unknown"])[0].lstrip("/")
        for p in c.get("Ports") or []:
            # GET /containers/json reports published ports with
            # PublicPort/IP; the per-container inspect endpoint uses
            # HostPort/HostIp. Accept both shapes.
            host_port = p.get("PublicPort") or p.get("HostPort")
            if host_port is None:
                continue
            host_ip = p.get("IP") or p.get("HostIp") or "0.0.0.0"
            ports.append(
                {
                    "port": int(host_port),
                    "proto": p.get("Type") or "tcp",
                    "name": name,
                    "detail": (
                        f"published {host_ip}:{host_port} -> "
                        f"{p.get('PrivatePort')}/{p.get('Type')}"
                    ),
                }
            )
    return ports
