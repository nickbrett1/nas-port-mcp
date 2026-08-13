"""Tests for the Docker published-port source (parsing only, no daemon).

Regression: GET /containers/json reports published ports with
PublicPort/IP fields (not HostPort/HostIp as in the inspect endpoint),
so the source previously returned [] and all published ports fell
through to `ss` as host-process/unknown.
"""

import httpx

from nas_port_mcp.docker_source import collect_docker_ports


def _fake_containers_json():
    """Shape of GET /containers/json (Ports use PublicPort/IP)."""
    return [
        {
            "Names": ["/webapp"],
            "Image": "nginx",
            "Ports": [
                {
                    "IP": "0.0.0.0",
                    "PrivatePort": 80,
                    "PublicPort": 8080,
                    "Type": "tcp",
                },
                {
                    "IP": "::",
                    "PrivatePort": 80,
                    "PublicPort": 8080,
                    "Type": "tcp",
                },
                {"PrivatePort": 53, "PublicPort": 5353, "Type": "udp"},
            ],
        },
        {
            "Names": ["/db"],
            "Ports": [
                {
                    "IP": "127.0.0.1",
                    "PrivatePort": 5432,
                    "PublicPort": 5432,
                    "Type": "tcp",
                }
            ],
        },
        {"Names": ["/host-net"], "Ports": []},  # network_mode: host → no ports
    ]


def test_parses_public_port_fields(monkeypatch):
    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return _fake_containers_json()

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, path):
            assert path == "/containers/json"
            return FakeResp()

    monkeypatch.setattr(httpx, "HTTPTransport", lambda **kw: object())
    monkeypatch.setattr(httpx, "Client", FakeClient)

    ports = collect_docker_ports()

    by_port = {p["port"]: p for p in ports}
    assert 8080 in by_port
    assert by_port[8080]["name"] == "webapp"
    assert by_port[8080]["proto"] == "tcp"
    # both v4+v6 entries collapse into one row by port; dedup at call site
    assert 5353 in by_port
    assert by_port[5353]["proto"] == "udp"
    assert by_port[5432]["name"] == "db"
    assert by_port[5432]["detail"].startswith("published 127.0.0.1:5432")
    # host-network containers contribute nothing
    assert all(p["port"] != 0 for p in ports)


def test_accepts_inspect_style_host_port_fields(monkeypatch):
    """Fallback: per-container inspect shape (HostPort/HostIp) still works."""

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {
                    "Names": ["/legacy"],
                    "Ports": [
                        {"HostIp": "0.0.0.0", "HostPort": "9000", "Type": "tcp"}
                    ],
                }
            ]

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, path):
            return FakeResp()

    monkeypatch.setattr(httpx, "HTTPTransport", lambda **kw: object())
    monkeypatch.setattr(httpx, "Client", FakeClient)

    ports = collect_docker_ports()
    assert len(ports) == 1
    assert ports[0]["port"] == 9000
    assert ports[0]["name"] == "legacy"


def test_returns_empty_on_api_error(monkeypatch):
    class BoomClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, path):
            raise httpx.ConnectError("no socket")

    monkeypatch.setattr(httpx, "HTTPTransport", lambda **kw: object())
    monkeypatch.setattr(httpx, "Client", BoomClient)

    assert collect_docker_ports() == []
