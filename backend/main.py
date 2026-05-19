from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel
from database import engine, get_db, Base
import models, schemas, crud
from ai_service import parse_task_from_text
from agents.task_agent import build_agent
import uuid
import json
from sqlalchemy import text

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TaskRPG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT config
SECRET_KEY = "taskrpg-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@app.get("/")
def read_root():
    return {"message": "TaskRPG API", "version": "1.0.0"}


# ── Auth routes ──────────────────────────────

@app.post("/auth/register", response_model=schemas.TokenResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_name(db, user.name)
    if existing:
        raise HTTPException(status_code=400, detail="该用户名已被注册")
    db_user = crud.create_user(db, user)
    access_token = create_access_token({"sub": str(db_user.id)})
    return schemas.TokenResponse(
        access_token=access_token,
        user=db_user,
    )


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_name(db, credentials.name)
    if not db_user:
        raise HTTPException(status_code=401, detail="用户名不存在")
    if not db_user.password_hash:
        raise HTTPException(status_code=401, detail="该账户未设置密码")
    if not crud.verify_password(credentials.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="密码错误")
    access_token = create_access_token({"sub": str(db_user.id)})
    return schemas.TokenResponse(
        access_token=access_token,
        user=db_user,
    )


# ── User routes ──────────────────────────────

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)


@app.get("/users/", response_model=List[schemas.UserResponse])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip, limit)


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# ── AI Agent routes ──────────────────────────

class ChatRequest(BaseModel):
    message: str
    user_id: int
    session_id: Optional[str] = None


class ChatStep(BaseModel):
    type: str  # "thought" | "tool" | "observation" | "error"
    content: str
    tool_name: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    user_id: int
    steps: Optional[List[ChatStep]] = None


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime


@app.post("/ai/chat", response_model=ChatResponse)
def ai_chat(req: ChatRequest, db: Session = Depends(get_db)):
    # 确保用户存在（复用 create_task 中的逻辑）
    db_user = crud.get_user(db, req.user_id)
    user_id = req.user_id
    if not db_user:
        db_user = db.query(models.User).filter(
            models.User.name == f"user_{req.user_id}"
        ).first()
        if not db_user:
            db_user = models.User(name=f"user_{req.user_id}")
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            db_stats = models.UserStats(user_id=db_user.id)
            db.add(db_stats)
            db.commit()
        user_id = db_user.id

    session_id = req.session_id or str(uuid.uuid4())

    # 如果是新会话，创建记录
    if not req.session_id:
        db_session = models.ChatSession(
            id=session_id,
            user_id=user_id,
            title=req.message[:20] + "..." if len(req.message) > 20 else req.message,
        )
        db.add(db_session)
        db.commit()
    else:
        # 更新会话时间
        db_session = db.query(models.ChatSession).filter(
            models.ChatSession.id == session_id
        ).first()
        if db_session:
            db_session.updated_at = datetime.utcnow()
            db.commit()

    # 构建 Agent 并执行（同步调用，自动注入层级记忆）
    agent = build_agent(db, user_id, session_id)
    result = agent.invoke(req.message)

    # 格式化 intermediate_steps 为前端可读的步骤
    steps = []
    for step in result.get("intermediate_steps", []):
        if len(step) < 2:
            continue
        action, observation = step[0], step[1]
        tool_name = getattr(action, "tool", "unknown")
        tool_input = getattr(action, "tool_input", "")

        if "[ERROR:" in str(observation):
            steps.append(ChatStep(
                type="error",
                content=f"{observation}",
                tool_name=tool_name,
            ))
        else:
            steps.append(ChatStep(
                type="tool",
                content=f"调用 {tool_name}",
                tool_name=tool_name,
            ))
            if observation and str(observation).strip():
                steps.append(ChatStep(
                    type="observation",
                    content=f"{observation}",
                    tool_name=tool_name,
                ))

    return ChatResponse(
        reply=result["output"],
        session_id=session_id,
        user_id=user_id,
        steps=steps if steps else None,
    )


@app.get("/ai/sessions", response_model=List[SessionResponse])
def list_sessions(user_id: int, db: Session = Depends(get_db)):
    sessions = db.query(models.ChatSession).filter(
        models.ChatSession.user_id == user_id
    ).order_by(models.ChatSession.updated_at.desc()).all()
    return [
        SessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@app.post("/ai/sessions", response_model=SessionResponse)
def create_session(user_id: int, db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    db_session = models.ChatSession(
        id=session_id,
        user_id=user_id,
        title="新对话",
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return SessionResponse(
        id=db_session.id,
        title=db_session.title,
        created_at=db_session.created_at,
    )


@app.get("/ai/sessions/{session_id}/messages")
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """获取指定会话的历史消息（LangChain message_store 表）"""
    result = db.execute(
        text("SELECT message FROM message_store WHERE session_id = :sid ORDER BY id"),
        {"sid": session_id}
    )
    messages = []
    for row in result:
        msg = json.loads(row[0])
        msg_type = msg.get("type", "")
        role = "user" if msg_type == "human" else "ai" if msg_type == "ai" else msg_type
        messages.append({
            "role": role,
            "content": msg.get("data", {}).get("content", ""),
        })
    return messages


@app.delete("/ai/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    db.query(models.ChatSession).filter(models.ChatSession.id == session_id).delete()
    db.commit()
    # 同时清理 LangChain 存储的消息
    db.execute(text("DELETE FROM message_store WHERE session_id = :sid"), {"sid": session_id})
    db.commit()
    return {"message": "Session deleted"}


# ── Memory routes ────────────────────────────

@app.post("/ai/memory/consolidate")
def consolidate_memory(user_id: int):
    """手动触发记忆整理（定期任务入口）"""
    from memory.memory_manager import MemoryManager
    mm = MemoryManager(user_id)
    mm.consolidate_all()
    # 重新生成各分类总览
    for cat in mm.store.get_categories():
        mm.summarize_category(cat)
    return {"message": "Memory consolidated", "categories": mm.store.get_categories()}


@app.get("/ai/memory/summary")
def get_memory_summary(user_id: int):
    """获取用户的记忆总览"""
    from memory.memory_manager import MemoryManager
    mm = MemoryManager(user_id)
    summary = mm.store.get_summary()
    return {
        "categories": list(summary.keys()),
        "summary": summary,
        "total_memories": mm.store.get_total_memory_count(),
    }


@app.get("/ai/memory/{category}")
def get_memory_detail(user_id: int, category: str):
    """获取某分类的详细记忆"""
    from memory.memory_manager import MemoryManager
    mm = MemoryManager(user_id)
    blocks = mm.store.get_detail_blocks(category)
    memories = mm.store.get_all_detail_memories(category)
    return {
        "category": category,
        "time_blocks": blocks,
        "memories": [{"id": m.id, "content": m.content, "time": m.created_at} for m in memories],
    }


# ── Task routes ──────────────────────────────

@app.post("/tasks/", response_model=schemas.TaskResponse)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, task)


@app.get("/tasks/", response_model=List[schemas.TaskResponse])
def list_tasks(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_tasks(db, user_id, skip, limit)


@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.patch("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db)):
    return crud.update_task(db, task_id, task_update)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    success = crud.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}


@app.post("/tasks/{task_id}/complete", response_model=schemas.TaskResponse)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.complete_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


# ── Plan routes ──────────────────────────────

@app.post("/plans/", response_model=schemas.PlanResponse)
def create_plan(plan: schemas.PlanCreate, db: Session = Depends(get_db)):
    return crud.create_plan(db, plan)


@app.get("/plans/", response_model=List[schemas.PlanResponse])
def list_plans(user_id: int, db: Session = Depends(get_db)):
    return crud.get_plans(db, user_id)


@app.get("/plans/{plan_id}", response_model=schemas.PlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    db_plan = crud.get_plan(db, plan_id)
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return db_plan


@app.patch("/plans/{plan_id}", response_model=schemas.PlanResponse)
def update_plan(plan_id: int, plan_update: schemas.PlanUpdate, db: Session = Depends(get_db)):
    db_plan = crud.update_plan(db, plan_id, plan_update)
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return db_plan


@app.delete("/plans/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    success = crud.delete_plan(db, plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"message": "Plan deleted"}


@app.get("/plans/{plan_id}/progress", response_model=schemas.PlanProgressResponse)
def get_plan_progress(plan_id: int, db: Session = Depends(get_db)):
    progress = crud.get_plan_progress(db, plan_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return progress
