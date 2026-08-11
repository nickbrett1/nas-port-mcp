# nas-port-mcp — single container: FastMCP server (stdio) + mcpo (Streamable HTTP)
#
# Requires (see docker-compose.yml):
#   network_mode: host   -> `ss` observes the HOST network namespace
#   /var/run/docker.sock:ro -> published-port attribution (read-only)

FROM python:3.12-slim AS build
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1
COPY pyproject.toml requirements.txt ./
COPY src ./src
RUN python -m venv /opt/venv && /opt/venv/bin/pip install .

FROM python:3.12-slim
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
# iproute2 -> `ss` (host listening sockets); curl -> healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends iproute2 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/venv /opt/venv
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
EXPOSE 3001
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD curl -fsS http://localhost:3001/healthz || exit 1
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
