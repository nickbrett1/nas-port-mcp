"""Static DSM reserved-port table.

Seed values from the design memo. VERIFY against DSM Control Panel on this
box (enabled services list) before trusting as ground truth — see open
questions in the README. Ports here are reported as reserved even when
nothing is currently listening.
"""

# (port, proto, service) — proto is advisory; a reserved port counts as taken
# for suggestion purposes regardless of the proto it is listed with.
DSM_RESERVED_PORTS: list[tuple[int, str, str]] = [
    (21, "tcp", "FTP"),
    (22, "tcp", "SSH"),
    (80, "tcp", "HTTP (web portal)"),
    (111, "tcp", "RPC"),
    (123, "udp", "NTP"),
    (443, "tcp", "HTTPS (web portal)"),
    (445, "tcp", "SMB"),
    (548, "tcp", "AFP"),
    (5000, "tcp", "DSM HTTP"),
    (5001, "tcp", "DSM HTTPS"),
    (5005, "tcp", "WebDAV HTTP"),
    (5006, "tcp", "WebDAV HTTPS"),
    (6690, "tcp", "Synology Drive"),
    (9997, "tcp", "Download Station"),
    (9998, "tcp", "Download Station"),
    (9999, "tcp", "Surveillance Station"),
    (1900, "udp", "SSDP discovery"),
    (5353, "udp", "mDNS"),
]
