"""Unit tests for the union/merge + suggestion logic (fake port map, no NAS)."""

from nas_port_mcp.portmap import build_port_map, is_ephemeral, port_status, suggest


def _docker(port: int, name: str) -> list[dict]:
    return [{"port": port, "proto": "tcp", "name": name, "detail": ""}]


def _ss(port: int, name: str) -> list[dict]:
    return [{"port": port, "proto": "tcp", "name": name, "detail": ""}]


def test_docker_wins_over_host_process():
    owners = build_port_map(_docker(3000, "parquet-peek"), _ss(3000, "python"), [])
    assert owners[3000].kind == "docker"
    assert owners[3000].name == "parquet-peek"


def test_dsm_reserved_reported_even_when_free():
    owners = build_port_map([], [], [(5000, "tcp", "DSM HTTP")])
    assert owners[5000].kind == "dsm-reserved"
    assert owners[5000].name == "DSM HTTP"


def test_suggest_preferred_free_returns_preferred():
    owners = build_port_map([], [], [])
    result = suggest(3000, 1024, 65535, owners)
    assert result["port"] == 3000
    assert result["preferredWasTakenBy"] is None


def test_suggest_returns_next_free_with_attribution():
    owners = build_port_map(_docker(3000, "squatter"), [], [])
    result = suggest(3000, 1024, 65535, owners)
    assert result["port"] == 3001
    assert result["preferredWasTakenBy"]["kind"] == "docker"
    assert result["preferredWasTakenBy"]["name"] == "squatter"


def test_suggest_skips_reserved_next_port():
    owners = build_port_map(
        _docker(3000, "a"),
        [],
        [(3001, "tcp", "reserved thing")],
    )
    result = suggest(3000, 1024, 65535, owners)
    assert result["port"] == 3002


def test_port_status_free_and_taken():
    assert port_status(4000, build_port_map([], [], []))["free"] is True
    owners = build_port_map(_docker(4000, "x"), [], [])
    assert port_status(4000, owners)["free"] is False
    assert port_status(4000, owners)["owner"]["kind"] == "docker"


def test_ephemeral_range_flag():
    owners = build_port_map([], [], [])
    assert port_status(40000, owners)["note"] == "ephemeral-range"
    assert is_ephemeral(32768) is True
    assert is_ephemeral(60999) is True
    assert is_ephemeral(3001) is False
