import pytest

from app.services.store import EvidenceStore


@pytest.fixture
def store():
    return EvidenceStore()
