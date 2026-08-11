"""FastMCP server: authoritative "what host port can I use?" on the NAS."""

from mcp.server.fastmcp import FastMCP

from nas_port_mcp.docker_source import DOCKER_SOCKET, collect_docker_ports
from nas_port_mcp.dsm_reserved import DSM_RESERVED_PORTS
from nas_port_mcp.netdata import machine_info as _machine_info
from nas_port_mcp.portmap import build_port_map, port_status, suggest
from nas_port_mcp.ss_source import collect_ss_sockets

mcp = FastMCP("nas-port-mcp")


def _protos_by_port(docker_ports: list[dict], ss_sockets: list[dict]) -> dict[int, set[str]]:
    protos: dict[int, set[str]] = {}
    for entry in docker_ports:
        protos.setdefault(entry["port"], set()).add(entry["proto"])
    for entry in ss_sockets:
        protos.setdefault(entry["port"], set()).add(entry["proto"])
    return protos


def _merged_map() -> dict:
    docker = collect_docker_ports(DOCKER_SOCKET)
    ss = collect_ss_sockets()
    return build_port_map(docker, ss, DSM_RESERVED_PORTS)


@mcp.tool()
def list_used_ports(proto: str | None = None, owner_kind: str | None = None) -> list[dict]:
    """List every host port currently bound or reserved, with owner attribution.

    Sources merged: Docker published ports, host listening sockets (`ss`), and
    the static DSM reserved table. Optional filters: proto (tcp|udp) and
    owner_kind (docker|host-process|dsm-reserved).
    """
    docker = collect_docker_ports(DOCKER_SOCKET)
    ss = collect_ss_sockets()
    owners = build_port_map(docker, ss, DSM_RESERVED_PORTS)
    protos = _protos_by_port(docker, ss)

    rows = []
    for port, owner in sorted(owners.items()):
        row = {
            "port": port,
            "proto": sorted(protos.get(port, ["tcp", "udp"])),
            "ownerKind": owner.kind,
            "ownerName": owner.name,
            "detail": owner.detail,
        }
        if proto and proto not in row["proto"]:
            continue
        if owner_kind and owner.kind != owner_kind:
            continue
        rows.append(row)
    return rows


@mcp.tool()
def check_port(port: int) -> dict:
    """Is this host port free? If taken, by what (container / host process / DSM)."""
    return port_status(port, _merged_map())


@mcp.tool()
def suggest_port(preferred: int = 3000, start: int = 1024, end: int = 65535) -> dict:
    """Suggest the next free host port (deterministic, no scanning).

    Returns the first free port >= preferred (or >= start if preferred is
    taken), with attribution for why preferred is unavailable. Call this
    BEFORE generating a new service that needs a published port.
    """
    return suggest(preferred, start, end, _merged_map())


@mcp.tool()
def machine_info() -> dict:
    """Host CPU/RAM/netdata info (wraps netdata's local API)."""
    return _machine_info()
