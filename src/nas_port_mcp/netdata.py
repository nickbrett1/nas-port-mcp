"""machine_info() via netdata's local API, degrading gracefully.

netdata already runs on the NAS (port 19999); we wrap it instead of
re-implementing /proc parsing. If netdata is unreachable we return a
structured "unavailable" payload rather than raising.
"""

import httpx

NETDATA_URL = "http://localhost:19999"


def _get_json(client: httpx.Client, path: str) -> dict | None:
    try:
        resp = client.get(path, timeout=2.0)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def machine_info(netdata_url: str = NETDATA_URL) -> dict:
    try:
        client = httpx.Client(base_url=netdata_url, timeout=2.0)
    except Exception as exc:
        return {"available": False, "reason": str(exc)}

    with client:
        info = _get_json(client, "/api/v1/info")
        if info is None:
            return {
                "available": False,
                "reason": f"netdata unreachable at {netdata_url}",
                "url": netdata_url,
            }

        result = {
            "available": True,
            "netdata": info.get("version"),
            "hostname": info.get("hostname"),
            "cpu_busy_percent": None,
            "ram_used_mb": None,
        }

        # system.cpu: dims include idle as a percentage
        cpu = _get_json(client, "/api/v1/chart?chart=system.cpu")
        if cpu and cpu.get("data"):
            dims = [d.get("name") for d in cpu.get("dimensions", [])]
            row = cpu["data"][0]
            if "idle" in dims:
                idle = row[dims.index("idle")]
                if isinstance(idle, (int, float)):
                    result["cpu_busy_percent"] = round(100 - idle, 1)

        # system.ram: dims include used, reported in bytes
        ram = _get_json(client, "/api/v1/chart?chart=system.ram")
        if ram and ram.get("data"):
            dims = [d.get("name") for d in ram.get("dimensions", [])]
            row = ram["data"][0]
            if "used" in dims:
                used = row[dims.index("used")]
                if isinstance(used, (int, float)):
                    result["ram_used_mb"] = round(used / 1024 / 1024, 1)

        return result
