from sqlalchemy import (
    create_engine, Column, Integer, String, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()
SessionLocal = None

def init_db(db_url: str = "sqlite:///:memory:"):
    global SessionLocal
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    return engine

def get_session():
    global SessionLocal
    if SessionLocal is None:
        init_db()
    return SessionLocal()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)

    owned_projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="owned_projects")
    members = relationship("ProjectMember", back_populates="project")
    tasks = relationship("Task", back_populates="project")

class ProjectMember(Base):
    __tablename__ = "project_members"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String(50), default="member")

    project = relationship("Project", back_populates="members")

class Invitation(Base):
    __tablename__ = "invitations"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    token = Column(String(100), unique=True, index=True)
    expires_at = Column(Integer)
    created_by = Column(Integer, ForeignKey("users.id"))
    used = Column(Boolean, default=False)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String(300))
    description = Column(Text, default="")
    status = Column(String(50), default="todo")
    assignee_id = Column(Integer, nullable=True)
    created_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))

    project = relationship("Project", back_populates="tasks")
    history = relationship("TaskHistory", back_populates="task")

class TaskHistory(Base):
    __tablename__ = "task_history"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    from_status = Column(String(50))
    to_status = Column(String(50))
    changed_by = Column(Integer)
    changed_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))

    task = relationship("Task", back_populates="history")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    message = Column(Text)
    created_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))
    read = Column(Boolean, default=False)
