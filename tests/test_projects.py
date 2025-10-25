from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def register_and_get_token(username):
    client.post("/auth/register", json={"username": username, "password": "pw"})
    r = client.post("/auth/login", json={"username": username, "password": "pw"})
    return r.json()["token"]

def test_create_invite_join_flow():
    owner_token = register_and_get_token("owner")
    headers = {"Authorization": f"Bearer {owner_token}"}
    r = client.post("/projects", json={"name": "Proyecto A"}, headers=headers)
    assert r.status_code in (200, 201)
    pid = r.json()["id"]

    r2 = client.post(f"/projects/{pid}/invite", headers=headers)
    assert r2.status_code in (200, 201)
    token = r2.json()["token"]

    member_token = register_and_get_token("member")
    headers_m = {"Authorization": f"Bearer {member_token}"}
    r3 = client.post(f"/projects/{pid}/join", json={"token": token}, headers=headers_m)
    assert r3.status_code == 200
    assert r3.json()["ok"] is True

    r4 = client.get("/projects", headers=headers_m)
    assert r4.status_code == 200
    assert any(p["id"] == pid for p in r4.json())
