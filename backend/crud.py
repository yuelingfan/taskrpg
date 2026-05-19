from sqlalchemy.orm import Session
from datetime import datetime
from passlib.context import CryptContext
import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_name(db: Session, name: str):
    return db.query(models.User).filter(models.User.name == name).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        name=user.name,
        password_hash=get_password_hash(user.password) if user.password else None
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    db_stats = models.UserStats(user_id=db_user.id)
    db.add(db_stats)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_tasks(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Task).filter(models.Task.user_id == user_id).offset(skip).limit(limit).all()


def get_tasks_by_status(db: Session, user_id: int, status: models.TaskStatus):
    return db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.status == status
    ).all()


def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def create_task(db: Session, task: schemas.TaskCreate):
    # 如果用户不存在则自动创建（开发环境方便处理）
    db_user = db.query(models.User).filter(models.User.id == task.user_id).first()
    user_id = task.user_id
    if not db_user:
        # 先尝试查找是否已有同名用户（之前自动创建的）
        db_user = db.query(models.User).filter(models.User.name == f"user_{task.user_id}").first()
        if not db_user:
            db_user = models.User(name=f"user_{task.user_id}")
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            db_stats = models.UserStats(user_id=db_user.id)
            db.add(db_stats)
            db.commit()
        user_id = db_user.id

    db_task = models.Task(
        user_id=user_id,
        parent_id=task.parent_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        task_type=task.task_type,
        deadline=task.deadline,
        exp_reward=task.exp_reward
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    log = models.TaskLog(task_id=db_task.id, action="created")
    db.add(log)
    db.commit()
    return db_task


def update_task(db: Session, task_id: int, task_update: schemas.TaskUpdate):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        update_data = task_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_task, key, value)

        if task_update.status == models.TaskStatus.DONE and not db_task.completed_at:
            db_task.completed_at = datetime.utcnow()
            log = models.TaskLog(task_id=db_task.id, action="completed")
            db.add(log)

        db.commit()
        db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        # 级联删除子任务
        db.query(models.Task).filter(models.Task.parent_id == task_id).delete()
        db.delete(db_task)
        db.commit()
        return True
    return False


def _apply_rpg_rewards(db: Session, user_id: int, task: models.Task):
    """完成任务时增加EXP和属性，处理升级"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    db_stats = db.query(models.UserStats).filter(models.UserStats.user_id == user_id).first()
    if not db_user or not db_stats:
        return

    # 增加 EXP
    exp_gain = task.exp_reward or 10
    db_user.exp += exp_gain

    # 检查升级
    exp_needed = db_user.level * 100
    while db_user.exp >= exp_needed:
        db_user.exp -= exp_needed
        db_user.level += 1
        exp_needed = db_user.level * 100

    # 根据任务类型增加属性
    attr_map = {
        models.TaskType.LEARNING: ("int_value", 1),
        models.TaskType.WORK: ("str_value", 1),
        models.TaskType.EXERCISE: ("sta_value", 1),
        models.TaskType.SOCIAL: ("cha_value", 1),
    }
    if task.task_type in attr_map:
        attr_name, attr_gain = attr_map[task.task_type]
        current = getattr(db_stats, attr_name, 10)
        setattr(db_stats, attr_name, current + attr_gain)

    db.commit()
    db.refresh(db_user)
    db.refresh(db_stats)


def complete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        db_task.status = models.TaskStatus.DONE
        db_task.completed_at = datetime.utcnow()

        log = models.TaskLog(task_id=db_task.id, action="completed")
        db.add(log)
        db.commit()

        # RPG奖励
        _apply_rpg_rewards(db, db_task.user_id, db_task)

        # 如果任务属于某个计划，检查计划进度
        if db_task.plan_id:
            _check_plan_completion(db, db_task.plan_id)

        db.refresh(db_task)
        return db_task
    return None


# ── Plan CRUD ──────────────────────────────

def get_plan(db: Session, plan_id: int):
    return db.query(models.Plan).filter(models.Plan.id == plan_id).first()


def get_plans(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Plan).filter(
        models.Plan.user_id == user_id
    ).offset(skip).limit(limit).all()


def create_plan(db: Session, plan: schemas.PlanCreate):
    # 确保用户存在
    db_user = db.query(models.User).filter(models.User.id == plan.user_id).first()
    user_id = plan.user_id
    if not db_user:
        db_user = db.query(models.User).filter(
            models.User.name == f"user_{plan.user_id}"
        ).first()
        if not db_user:
            db_user = models.User(name=f"user_{plan.user_id}")
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            db_stats = models.UserStats(user_id=db_user.id)
            db.add(db_stats)
            db.commit()
        user_id = db_user.id

    stages_data = []
    for stage in plan.stages:
        stages_data.append({
            "name": stage.name,
            "description": stage.description,
            "order": stage.order,
            "tasks": stage.tasks,
        })

    db_plan = models.Plan(
        user_id=user_id,
        title=plan.title,
        description=plan.description,
        stages=stages_data if stages_data else [],
        status="active",
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


def update_plan(db: Session, plan_id: int, plan_update: schemas.PlanUpdate):
    db_plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
    if not db_plan:
        return None

    update_data = plan_update.model_dump(exclude_unset=True)

    if "stages" in update_data and update_data["stages"] is not None:
        stages_data = []
        for stage in update_data["stages"]:
            if isinstance(stage, dict):
                stages_data.append(stage)
            else:
                stages_data.append({
                    "name": stage.name,
                    "description": stage.description,
                    "order": stage.order,
                    "tasks": stage.tasks,
                })
        db_plan.stages = stages_data
        del update_data["stages"]

    for key, value in update_data.items():
        setattr(db_plan, key, value)

    db.commit()
    db.refresh(db_plan)
    return db_plan


def delete_plan(db: Session, plan_id: int):
    db_plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
    if db_plan:
        # 解除关联任务的 plan_id
        db.query(models.Task).filter(models.Task.plan_id == plan_id).update(
            {models.Task.plan_id: None}
        )
        db.delete(db_plan)
        db.commit()
        return True
    return False


def get_plan_progress(db: Session, plan_id: int):
    """获取计划进度统计"""
    db_plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
    if not db_plan:
        return None

    plan_tasks = db.query(models.Task).filter(models.Task.plan_id == plan_id).all()
    total_tasks = len(plan_tasks)
    completed_tasks = sum(1 for t in plan_tasks if t.status == models.TaskStatus.DONE)

    stages = db_plan.stages or []
    total_stages = len(stages)

    # 计算已完成阶段数（基于阶段内所有任务是否完成）
    completed_stages = 0
    current_stage = None
    for stage in stages:
        stage_tasks = [t for t in plan_tasks if any(
            st.get("title") == t.title for st in stage.get("tasks", [])
        )]
        if stage_tasks and all(t.status == models.TaskStatus.DONE for t in stage_tasks):
            completed_stages += 1
        elif current_stage is None and stage_tasks:
            current_stage = stage["name"]

    # 如果没有从阶段匹配到当前阶段，用简单规则
    if current_stage is None and stages:
        for stage in stages:
            stage_task_titles = {st.get("title") for st in stage.get("tasks", [])}
            stage_tasks = [t for t in plan_tasks if t.title in stage_task_titles]
            if not stage_tasks or any(t.status != models.TaskStatus.DONE for t in stage_tasks):
                current_stage = stage["name"]
                break
        if current_stage is None and stages:
            current_stage = stages[-1]["name"]

    progress_percent = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    return {
        "plan_id": db_plan.id,
        "title": db_plan.title,
        "total_stages": total_stages,
        "completed_stages": completed_stages,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "current_stage": current_stage,
        "progress_percent": round(progress_percent, 1),
        "status": db_plan.status,
    }


def _check_plan_completion(db: Session, plan_id: int):
    """检查计划是否完成"""
    plan_tasks = db.query(models.Task).filter(models.Task.plan_id == plan_id).all()
    if not plan_tasks:
        return

    all_done = all(t.status == models.TaskStatus.DONE for t in plan_tasks)
    if all_done:
        db_plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
        if db_plan and db_plan.status != "completed":
            db_plan.status = "completed"
            db_plan.completed_at = datetime.utcnow()
            db.commit()
