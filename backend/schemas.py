from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskStatus(str, Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskType(str, Enum):
    LEARNING = "learning"
    WORK = "work"
    EXERCISE = "exercise"
    SOCIAL = "social"
    OTHER = "other"


class UserStatsBase(BaseModel):
    str_value: int = 10
    int_value: int = 10
    sta_value: int = 10
    cha_value: int = 10


class UserStatsCreate(UserStatsBase):
    pass


class UserStatsResponse(UserStatsBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    name: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    level: int
    exp: int
    created_at: datetime
    stats: Optional[UserStatsResponse] = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    name: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: TaskType = TaskType.OTHER
    deadline: Optional[datetime] = None
    exp_reward: int = 10


class TaskCreate(TaskBase):
    user_id: int
    parent_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    deadline: Optional[datetime] = None


class TaskResponse(TaskBase):
    id: int
    user_id: int
    parent_id: Optional[int] = None
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskLogBase(BaseModel):
    action: str


class TaskLogCreate(TaskLogBase):
    task_id: int


class TaskLogResponse(TaskLogBase):
    id: int
    task_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class PlanStage(BaseModel):
    name: str
    description: Optional[str] = None
    order: int = 1
    tasks: List[Dict[str, Any]] = []


class PlanBase(BaseModel):
    title: str
    description: Optional[str] = None
    stages: List[PlanStage] = []


class PlanCreate(PlanBase):
    user_id: int


class PlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    stages: Optional[List[PlanStage]] = None
    status: Optional[str] = None


class PlanResponse(PlanBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    tasks: List[TaskResponse] = []

    class Config:
        from_attributes = True


class PlanProgressResponse(BaseModel):
    plan_id: int
    title: str
    total_stages: int
    completed_stages: int
    total_tasks: int
    completed_tasks: int
    current_stage: Optional[str] = None
    progress_percent: float
    status: str
