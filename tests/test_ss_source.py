"""Parsing tests for `ss -tulpn` output (pure string parsing, no NAS)."""

from nas_port_mcp.ss_source import _LINE_RE, _parse_local, collect_ss_sockets


def test_parse_ipv4():
    assert _parse_local("0.0.0.0:3000") == ("0.0.0.0", 3000)


def test_parse_ipv6():
    assert _parse_local("[::]:5000") == ("::", 5000)


def test_parse_wildcard_udp():
    assert _parse_local("*:1900") == ("*", 1900)


def test_line_regex_with_process():
    line = (
        'tcp    LISTEN  0  128  0.0.0.0:3000  0.0.0.0:*  '
        'users:(("docker-proxy",pid=1234,fd=4))'
    )
    m = _LINE_RE.match(line)
    assert m is not None
    assert m.group("local") == "0.0.0.0:3000"
    assert m.group("proc").startswith("docker-proxy")


def test_collect_parses_multiline_output(monkeypatch):
    fake = (
        "Netid  State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process\n"
        'tcp    LISTEN  0       128     0.0.0.0:3000         0.0.0.0:*          users:(("docker-proxy",pid=1,fd=3))\n'
        'tcp6   LISTEN  0       128     [::]:5001             [::]:*            users:(("nginx",pid=2,fd=4))\n'
        'udp    UNCONN  0       0       0.0.0.0:1900         0.0.0.0:*          \n'
    )

    def fake_run(*args, **kwargs):
        class R:
            stdout = fake

        return R()

    monkeypatch.setattr("nas_port_mcp.ss_source.subprocess.run", fake_run)
    sockets = collect_ss_sockets()
    by_port = {s["port"]: s for s in sockets}
    assert by_port[3000]["name"] == "docker-proxy"
    assert by_port[3000]["proto"] == "tcp"
    assert by_port[5001]["proto"] == "tcp"
    assert by_port[5001]["detail"].startswith("::")
    assert by_port[1900]["proto"] == "udp"
