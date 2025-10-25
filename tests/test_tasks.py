from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def register_and_get_token(username):
    client.post("/auth/register", json={"username": username, "password": "pw"})
    r = client.post("/auth/login", json={"username": username, "password": "pw"})
    return r.json()["token"]

def test_create_task_and_move_history():
    token = register_and_get_token("owner2")
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/projects", json={"name": "P2"}, headers=h)
    pid = r.json()["id"]

    r2 = client.post(f"/tasks/{pid}/tasks", json={"title": "Tarea 1"}, headers=h)
    assert r2.status_code in (200, 201)
    tid = r2.json()["id"]

    r3 = client.patch(f"/tasks/move/{tid}", json={"to_status": "doing"}, headers=h)
    assert r3.status_code == 200

    r4 = client.patch(f"/tasks/move/{tid}", json={"to_status": "done"}, headers=h)
    assert r4.status_code == 200

    r5 = client.get(f"/tasks/history/{tid}", headers=h)
    assert r5.status_code == 200
    history = r5.json()
    assert len(history) >= 2
    assert history[0]["from_status"] == "todo"

def test_project_report_counts():
    token = register_and_get_token("reporter")
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/projects", json={"name": "ReportProj"}, headers=h)
    pid = r.json()["id"]

    t1 = client.post(f"/tasks/{pid}/tasks", json={"title": "A"}, headers=h)
    t2 = client.post(f"/tasks/{pid}/tasks", json={"title": "B"}, headers=h)
    tid = t2.json()["id"]
    client.patch(f"/tasks/move/{tid}", json={"to_status": "doing"}, headers=h)

    r_report = client.get(f"/projects/{pid}/report", headers=h)
    assert r_report.status_code == 200
    body = r_report.json()
    assert "todo" in body and "doing" in body and "done" in body
