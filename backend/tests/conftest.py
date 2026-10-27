import pytest


@pytest.fixture(autouse=True)
def no_external_services(monkeypatch):
    """Keep every test away from the real H-MEM and Zetaris."""
    monkeypatch.delenv("HMEM_URL", raising=False)
    monkeypatch.delenv("ZETARIS_API_KEY", raising=False)