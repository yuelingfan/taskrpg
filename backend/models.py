from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskType(str, enum.Enum):
    LEARNING = "learning"
    WORK = "work"
    EXERCISE = "exercise"
    SOCIAL = "social"
    OTHER = "other"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=True)
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    stats = relationship("UserStats", back_populates="user", uselist=False)
    tasks = relationship("Task", back_populates="user")
    plans = relationship("Plan", back_populates="user")
    memories = relationship("Memory", back_populates="user")


class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    str_value = Column(Integer, default=10)
    int_value = Column(Integer, default=10)
    sta_value = Column(Integer, default=10)
    cha_value = Column(Integer, default=10)

    user = relationship("User", back_populates="stats")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    task_type = Column(SQLEnum(TaskType), default=TaskType.OTHER)
    deadline = Column(DateTime(timezone=True), nullable=True)
    exp_reward = Column(Integer, default=10)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="tasks")
    logs = relationship("TaskLog", back_populates="task")
    subtasks = relationship("Task", backref="parent", remote_side=[id])
    plan = relationship("Plan", back_populates="tasks")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    stages = Column(JSON, default=list)
    status = Column(String, default="active")  # active, completed, paused
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="plans")
    tasks = relationship("Task", back_populates="plan")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="新对话")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    action = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="logs")


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    category = Column(String, index=True)
    speaker = Column(String)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="memories")
