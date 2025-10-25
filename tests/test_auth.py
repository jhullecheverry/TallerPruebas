from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_and_login():
    r = client.post("/auth/register", json={"username": "alice", "password": "pass"})
    assert r.status_code in (200, 201)
    r2 = client.post("/auth/login", json={"username": "alice", "password": "pass"})
    assert r2.status_code == 200
    assert "token" in r2.json()

def test_login_wrong_password():
    client.post("/auth/register", json={"username": "bob", "password": "pw"})
    r = client.post("/auth/login", json={"username": "bob", "password": "wrong"})
    assert r.status_code == 401
