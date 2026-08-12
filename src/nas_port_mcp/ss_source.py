"""Host listening-socket discovery via `ss` (host network namespace).

The container runs with network_mode: host, so `ss -tulpn` observes the
host's sockets — including DSM services and host-net containers — which a
bridge-network container could never see.
"""

import re
import subprocess

_LINE_RE = re.compile(
    r"^(?P<proto>tcp|udp)\d*\s+"
    r"(?P<state>\S+)\s+"
    r"\d+\s+\d+\s+"
    r"(?P<local>\S+)\s+"
    r"(?P<peer>\S+)(?:\s+users:\(\("(?P<proc>[^\"]*)\"[^)]*\)\))?"
)


def _parse_local(local: str) -> tuple[str, int] | None:
    """'0.0.0.0:3000' | '[::]:5000' | '*:1900' -> (ip, port)."""
    if local.startswith("["):  # IPv6
        addr, _, rest = local[1:].partition("]")
        port = rest.lstrip(":")
        return (addr, int(port)) if port.isdigit() else None
    addr, _, port = local.rpartition(":")
    return (addr, int(port)) if port.isdigit() else None


def collect_ss_sockets(ss_bin: str = "ss") -> list[dict]:
    """Return [{port, proto, name, detail}] from `ss -tulpn`."""
    try:
        out = subprocess.run(
            [ss_bin, "-tulpn"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        ).stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    sockets = []
    for line in out.splitlines():
        if not line or line.startswith(("Netid", "State")):
            continue
        m = _LINE_RE.match(line.strip())
        if not m:
            continue
        parsed = _parse_local(m.group("local"))
        if not parsed:
            continue
        addr, port = parsed
        proc = m.group("proc") or ""
        name = proc.split(",", 1)[0] if proc else "unknown"
        sockets.append(
            {
                "port": port,
                "proto": m.group("proto"),
                "name": name,
                "detail": f"{addr}:{port} ({m.group('state')})",
            }
        )
    return sockets
