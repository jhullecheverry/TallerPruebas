from db import (
    get_session, User, Project, ProjectMember, Invitation,
    Task, TaskHistory, Notification
)
from passlib.context import CryptContext
from datetime import datetime
import secrets

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def now_ts():
    return int(datetime.utcnow().timestamp())

# Users
def create_user(username: str, password: str, db=None):
    db = db or get_session()
    if db.query(User).filter(User.username == username).first():
        raise ValueError("username exists")
    u = User(username=username, password_hash=pwd_ctx.hash(password))
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def get_user_by_username(username: str, db=None):
    db = db or get_session()
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(user_id: int, db=None):
    db = db or get_session()
    return db.query(User).get(user_id)

# Projects
def create_project(name: str, owner_id: int, db=None):
    db = db or get_session()
    p = Project(name=name, owner_id=owner_id)
    db.add(p)
    db.commit()
    db.refresh(p)
    # add owner as member
    pm = ProjectMember(project_id=p.id, user_id=owner_id, role="owner")
    db.add(pm)
    db.commit()
    return p

def get_user_projects(user_id: int, db=None):
    db = db or get_session()
    rows = db.query(Project).join(ProjectMember, ProjectMember.project_id == Project.id).filter(ProjectMember.user_id == user_id).all()
    return rows

# Invitations
def create_invitation(project_id: int, created_by: int, ttl_seconds: int = 24*3600, db=None):
    db = db or get_session()
    token = secrets.token_hex(16)
    expires_at = now_ts() + ttl_seconds
    inv = Invitation(project_id=project_id, token=token, expires_at=expires_at, created_by=created_by, used=False)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv

def use_invitation(token: str, user_id: int, db=None):
    db = db or get_session()
    inv = db.query(Invitation).filter(Invitation.token == token, Invitation.used == False).first()
    if not inv:
        return {"ok": False, "reason": "invalid"}
    if inv.expires_at < now_ts():
        return {"ok": False, "reason": "expired"}
    # add membership
    pm = ProjectMember(project_id=inv.project_id, user_id=user_id, role="member")
    db.add(pm)
    inv.used = True
    db.commit()
    return {"ok": True, "project_id": inv.project_id}

# Tasks
def create_task(project_id: int, title: str, description: str = "", assignee_id: int = None, db=None):
    db = db or get_session()
    t = Task(project_id=project_id, title=title, description=description, status="todo", assignee_id=assignee_id, created_at=now_ts(), updated_at=now_ts())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

def get_project_tasks(project_id: int, db=None):
    db = db or get_session()
    return db.query(Task).filter(Task.project_id == project_id).all()

def move_task(task_id: int, to_status: str, changed_by: int, db=None):
    db = db or get_session()
    task = db.query(Task).get(task_id)
    if not task:
        return {"ok": False, "reason": "not_found"}
    from_status = task.status
    task.status = to_status
    task.updated_at = now_ts()
    db.add(task)
    # history
    h = TaskHistory(task_id=task.id, from_status=from_status, to_status=to_status, changed_by=changed_by, changed_at=now_ts())
    db.add(h)
    db.commit()
    return {"ok": True, "from": from_status, "to": to_status}

def get_task_history(task_id: int, db=None):
    db = db or get_session()
    return db.query(TaskHistory).filter(TaskHistory.task_id == task_id).order_by(TaskHistory.changed_at.asc()).all()

# Reports
def project_report(project_id: int, db=None):
    db = db or get_session()
    todo = db.query(Task).filter(Task.project_id == project_id, Task.status == "todo").count()
    doing = db.query(Task).filter(Task.project_id == project_id, Task.status == "doing").count()
    done = db.query(Task).filter(Task.project_id == project_id, Task.status == "done").count()
    return {"todo": todo, "doing": doing, "done": done}

# Notifications
def create_notification(user_id: int, message: str, db=None):
    db = db or get_session()
    n = Notification(user_id=user_id, message=message, created_at=now_ts(), read=False)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n

def get_notifications_for_user(user_id: int, db=None):
    db = db or get_session()
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
