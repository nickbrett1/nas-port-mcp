# nas-port-mcp
MCP server that authoritatively answers "what host port can I use?" on the Synology NAS. Union of Docker API published ports, host netns sockets (ss), and DSM reserved ports. Read-only; Tailscale-only via mcpo.
