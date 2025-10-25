from fastapi import FastAPI, Depends, HTTPException, status, Request
from db import init_db, get_session
from crud import (
    create_user, get_user_by_username, create_project, get_user_projects,
    create_invitation, use_invitation, create_task, get_project_tasks, move_task,
    get_task_history, project_report, create_notification, get_notifications_for_user
)
from auth import create_access_token, verify_password, get_current_user
from pydantic import BaseModel
import os
import asyncio
from fastapi.responses import StreamingResponse

DB_FILE = os.environ.get("DB_FILE", "sqlite:///./data.sqlite")
init_db(DB_FILE)

app = FastAPI(title="Project Tasks - TDD (FastAPI)")

# Simple in-memory broadcaster for notifications
class Notifier:
    def __init__(self):
        self.queues = []

    async def publish(self, event: dict):
        for q in list(self.queues):
            await q.put(event)

    def subscribe(self):
        q = asyncio.Queue()
        self.queues.append(q)
        return q

    def unsubscribe(self, q):
        try:
            self.queues.remove(q)
        except ValueError:
            pass

notifier = Notifier()

# Schemas
class RegisterIn(BaseModel):
    username: str
    password: str

class LoginIn(BaseModel):
    username: str
    password: str

class ProjectIn(BaseModel):
    name: str

class InviteIn(BaseModel):
    token: str

class TaskIn(BaseModel):
    title: str
    description: str | None = ""
    assignee_id: int | None = None

class MoveIn(BaseModel):
    to_status: str

# Routes - Auth
@app.post("/auth/register")
def register(payload: RegisterIn):
    try:
        u = create_user(payload.username, payload.password)
        return {"id": u.id, "username": u.username}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@app.post("/auth/login")
def login(payload: LoginIn):
    db = get_session()
    User = get_user_by_username.__globals__['User'] if 'User' in get_user_by_username.__globals__ else None
    u = db.query(User).filter_by(username=payload.username).first()
    if not u:
        raise HTTPException(status_code=401, detail="invalid credentials")
    if not verify_password(payload.password, u.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = create_access_token(sub=u.id, username=u.username)
    return {"token": token}

# Projects
@app.post("/projects")
def create_project_route(payload: ProjectIn, current_user=Depends(get_current_user)):
    p = create_project(payload.name, current_user.id)
    return {"id": p.id, "name": p.name, "owner_id": p.owner_id}

@app.get("/projects")
def list_projects(current_user=Depends(get_current_user)):
    rows = get_user_projects(current_user.id)
    out = [{"id": p.id, "name": p.name, "owner_id": p.owner_id} for p in rows]
    return out

@app.post("/projects/{project_id}/invite")
async def invite_project(project_id: int, current_user=Depends(get_current_user)):
    # naive membership check
    user_projects = get_user_projects(current_user.id)
    if not any(p.id == project_id for p in user_projects):
        raise HTTPException(status_code=403, detail="not a member")
    inv = create_invitation(project_id, current_user.id)
    await notifier.publish({"type": "invitation_created", "project_id": project_id, "token": inv.token, "by": current_user.id})
    create_notification(current_user.id, f"Invitation created for project {project_id}")
    return {"token": inv.token, "expires_at": inv.expires_at}

@app.post("/projects/{project_id}/join")
async def join_project(project_id: int, payload: InviteIn, current_user=Depends(get_current_user)):
    res = use_invitation(payload.token, current_user.id)
    if not res["ok"]:
        raise HTTPException(status_code=400, detail=res["reason"])
    await notifier.publish({"type": "user_joined", "project_id": res["project_id"], "user_id": current_user.id})
    create_notification(current_user.id, f"Joined project {res['project_id']}")
    return {"ok": True, "project_id": res["project_id"]}

@app.get("/projects/{project_id}/report")
def project_report_route(project_id: int, current_user=Depends(get_current_user)):
    r = project_report(project_id)
    return r

# Tasks
@app.post("/tasks/{project_id}/tasks")
async def create_task_route(project_id: int, payload: TaskIn, current_user=Depends(get_current_user)):
    t = create_task(project_id, payload.title, payload.description or "", payload.assignee_id)
    create_notification(current_user.id, f'Task "{payload.title}" created in project {project_id}')
    await notifier.publish({"type": "task_created", "project_id": project_id, "task": {"id": t.id, "title": t.title}})
    return {"id": t.id, "project_id": t.project_id, "title": t.title, "status": t.status}

@app.get("/tasks/{project_id}/tasks")
def list_tasks(project_id: int, current_user=Depends(get_current_user)):
    t = get_project_tasks(project_id)
    out = [{"id": x.id, "title": x.title, "status": x.status} for x in t]
    return out

@app.patch("/tasks/move/{task_id}")
async def move_task_route(task_id: int, payload: MoveIn, current_user=Depends(get_current_user)):
    allowed = ["todo", "doing", "done"]
    if payload.to_status not in allowed:
        raise HTTPException(status_code=400, detail="invalid status")
    res = move_task(task_id, payload.to_status, current_user.id)
    if not res["ok"]:
        raise HTTPException(status_code=404, detail=res["reason"])
    create_notification(current_user.id, f"Task {task_id} moved to {payload.to_status}")
    await notifier.publish({"type": "task_moved", "task_id": task_id, "from": res["from"], "to": res["to"], "by": current_user.id})
    return {"ok": True}

@app.get("/tasks/history/{task_id}")
def task_history_route(task_id: int, current_user=Depends(get_current_user)):
    h = get_task_history(task_id)
    out = [{"from_status": x.from_status, "to_status": x.to_status, "changed_by": x.changed_by, "changed_at": x.changed_at} for x in h]
    return out

# Notifications
@app.get("/notifications")
def notifications_route(current_user=Depends(get_current_user)):
    rows = get_notifications_for_user(current_user.id)
    out = [{"id": r.id, "message": r.message, "created_at": r.created_at, "read": r.read} for r in rows]
    return out

@app.get("/notifications/stream")
def notifications_stream(request: Request, current_user=Depends(get_current_user)):
    q = notifier.subscribe()

    async def event_generator():
        # send initial stored notifications
        initial = get_notifications_for_user(current_user.id)
        yield f"event: init\ndata: { [ {'id':r.id,'message':r.message,'created_at':r.created_at} for r in initial ] }\n\n"
        try:
            while True:
                if await request.is_disconnected():
                    break
                event = await q.get()
                yield f"event: {event.get('type')}\ndata: {event}\n\n"
        finally:
            notifier.unsubscribe(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Health
@app.get("/health")
def health():
    return {"ok": True}
