"""Smoke test: the src-layout package installs and imports cleanly."""


def test_package_imports():
    import nas_port_mcp  # noqa: F401

    assert nas_port_mcp.__version__
