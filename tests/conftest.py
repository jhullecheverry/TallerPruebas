import pytest
from db import init_db as init_db_func

@pytest.fixture(autouse=True)
def fresh_db():
    # Each test gets a fresh in-memory DB
    init_db_func("sqlite:///:memory:")
    yield
