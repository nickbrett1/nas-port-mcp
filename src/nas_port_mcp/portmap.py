"""Union model: merge Docker API + `ss` + DSM reserved into one port->owner map.

Dedup rule (design memo): Docker binding wins for the "who" label,
host-process is the fallback, DSM reserved is advisory ("reserved even if not
listening") and only fills ports nothing else claims.
"""

from dataclasses import dataclass
from typing import Optional

EPHEMERAL_START = 32768
EPHEMERAL_END = 60999


@dataclass
class PortOwner:
    kind: str  # docker | host-process | dsm-reserved
    name: str
    detail: str = ""


def build_port_map(
    docker_ports: list[dict],
    ss_sockets: list[dict],
    dsm_reserved: list[tuple[int, str, str]],
) -> dict[int, PortOwner]:
    owners: dict[int, PortOwner] = {}

    # Lowest precedence: advisory DSM reservations (never overwrite a real owner)
    for port, _proto, service in dsm_reserved:
        owners.setdefault(port, PortOwner("dsm-reserved", service, f"reserved by DSM ({service})"))

    # Middle: whatever is actually listening on the host
    for entry in ss_sockets:
        port = entry["port"]
        if port not in owners:
            owners[port] = PortOwner("host-process", entry["name"], entry["detail"])

    # Highest: Docker published-port attribution
    for entry in docker_ports:
        owners[entry["port"]] = PortOwner("docker", entry["name"], entry["detail"])

    return owners


def is_ephemeral(port: int) -> bool:
    return EPHEMERAL_START <= port <= EPHEMERAL_END


def port_status(port: int, owners: dict[int, PortOwner]) -> dict:
    owner = owners.get(port)
    return {
        "port": port,
        "free": owner is None,
        "owner": (
            {"kind": owner.kind, "name": owner.name, "detail": owner.detail}
            if owner
            else None
        ),
        "note": "ephemeral-range" if is_ephemeral(port) else None,
    }


def suggest(
    preferred: int = 3000,
    start: int = 1024,
    end: int = 65535,
    owners: Optional[dict[int, PortOwner]] = None,
) -> dict:
    """Deterministic next-free port: first free port >= preferred (or >= start
    if preferred is taken), with attribution for why preferred is unavailable."""
    owners = owners or {}
    used = set(owners)
    preferred_taken = owners.get(preferred)

    if preferred not in used and start <= preferred <= end:
        return {
            "port": preferred,
            "preferredWasTakenBy": None,
            "note": "ephemeral-range" if is_ephemeral(preferred) else None,
        }

    candidate = max(start, preferred)
    while candidate in used and candidate <= end:
        candidate += 1

    return {
        "port": candidate if candidate <= end else None,
        "preferredWasTakenBy": (
            {
                "kind": preferred_taken.kind,
                "name": preferred_taken.name,
                "detail": preferred_taken.detail,
            }
            if preferred_taken
            else None
        ),
        "note": "ephemeral-range" if is_ephemeral(candidate) else None,
    }
