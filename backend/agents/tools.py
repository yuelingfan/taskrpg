"""AI Agent 可调用的工具定义"""
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas, crud
from ai_service import parse_task_from_text as _parse_task


def build_tools(db: Session, user_id: int):
    """根据 db session 和 user_id 构建工具列表（闭包）"""

    @tool
    def list_user_tasks(status: str = None, limit: int = 10) -> str:
        """查询用户当前的任务列表。status 可选：todo / doing / done。"""
        query = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.parent_id == None
        )
        if status:
            query = query.filter(models.Task.status == status)
        tasks = query.order_by(models.Task.created_at.desc()).limit(limit).all()

        if not tasks:
            return "当前没有任务。"

        lines = []
        for t in tasks:
            status_label = {"todo": "待领取", "doing": "进行中", "done": "已完成"}.get(t.status, t.status)
            deadline_str = f"（截止：{t.deadline.strftime('%m月%d日')}）" if t.deadline else ""
            lines.append(f"- [{t.id}] {t.title} | {status_label} | +{t.exp_reward} XP {deadline_str}")
        return "\n".join(lines)

    @tool
    def get_task_detail(task_id: int) -> str:
        """获取指定任务的详细信息。"""
        task = db.query(models.Task).filter(
            models.Task.id == task_id,
            models.Task.user_id == user_id
        ).first()
        if not task:
            return f"找不到任务 #{task_id}"

        subtasks = db.query(models.Task).filter(models.Task.parent_id == task_id).all()
        sub_str = ""
        if subtasks:
            sub_lines = [f"  - {s.title} ({s.status})" for s in subtasks]
            sub_str = "\n子任务：\n" + "\n".join(sub_lines)

        return (
            f"任务：{task.title}\n"
            f"描述：{task.description or '无'}\n"
            f"状态：{task.status}\n"
            f"优先级：{task.priority}\n"
            f"类型：{task.task_type}\n"
            f"经验值：{task.exp_reward}\n"
            f"截止：{task.deadline.strftime('%Y-%m-%d') if task.deadline else '无'}{sub_str}"
        )

    @tool
    def create_user_task(
        title: str,
        description: str = "",
        task_type: str = "other",
        priority: str = "medium",
        deadline: str = None,
        exp_reward: int = 10,
    ) -> str:
        """为用户创建一个新任务。
        task_type: learning / work / exercise / social / other
        priority: low / medium / high / urgent
        deadline: YYYY-MM-DD 格式，可选
        """
        try:
            task_data = schemas.TaskCreate(
                user_id=user_id,
                title=title,
                description=description or None,
                task_type=task_type,
                priority=priority,
                deadline=datetime.fromisoformat(deadline) if deadline else None,
                exp_reward=exp_reward,
            )
            task = crud.create_task(db, task_data)
            return f"任务创建成功！ID: {task.id}，标题：{task.title}，奖励 {task.exp_reward} XP"
        except Exception as e:
            return f"[ERROR:create_user_task] 创建任务失败：{str(e)}"

    @tool
    def complete_user_task(task_id: int) -> str:
        """将指定任务标记为完成，用户会获得经验值和属性奖励。"""
        task = db.query(models.Task).filter(
            models.Task.id == task_id,
            models.Task.user_id == user_id
        ).first()
        if not task:
            return f"找不到任务 #{task_id}"
        if task.status == "done":
            return f"任务「{task.title}」已经是完成状态了。"

        result = crud.complete_task(db, task_id)
        if result:
            return f"🎉 任务「{result.title}」完成！获得 {result.exp_reward} XP！"
        return "[ERROR:complete_user_task] 完成任务失败。"

    @tool
    def delete_user_task(task_id: int) -> str:
        """删除指定任务及其子任务。"""
        task = db.query(models.Task).filter(
            models.Task.id == task_id,
            models.Task.user_id == user_id
        ).first()
        if not task:
            return f"找不到任务 #{task_id}"

        title = task.title
        success = crud.delete_task(db, task_id)
        if success:
            return f"任务「{title}」已删除。"
        return "[ERROR:delete_user_task] 删除任务失败。"

    @tool
    def get_user_stats() -> str:
        """获取用户当前等级、经验值和属性。"""
        db_user = crud.get_user(db, user_id)
        if not db_user:
            return "用户不存在。"

        stats = db_user.stats
        attr_str = ""
        if stats:
            attr_str = (
                f"\n属性：力量 {stats.str_value} | 智力 {stats.int_value} | "
                f"耐力 {stats.sta_value} | 专注 {stats.cha_value}"
            )

        return (
            f"等级：Lv.{db_user.level}\n"
            f"经验值：{db_user.exp} / {db_user.level * 100}{attr_str}"
        )

    @tool
    def parse_task_intent(text: str) -> str:
        """解析用户的自然语言描述，提取结构化任务信息。"""
        result = _parse_task(text)
        parts = [
            f"标题：{result.get('title')}",
            f"描述：{result.get('description') or '无'}",
            f"优先级：{result.get('priority', 'medium')}",
            f"类型：{result.get('task_type', 'other')}",
            f"截止：{result.get('deadline') or '无'}",
            f"经验值：{result.get('exp_reward', 10)}",
        ]
        subs = result.get("subtasks", [])
        if subs:
            parts.append(f"子任务：{len(subs)} 个")
        return "\n".join(parts)

    @tool
    def create_plan(
        title: str,
        description: str = "",
        stages_json: str = "",
    ) -> str:
        """为用户创建一个长期计划（目标拆解）。
        stages_json: JSON 数组字符串，每个元素包含 name, description, tasks。
        每个 task 必须包含 title 和 deadline（YYYY-MM-DD 格式）。
        示例: [{"name": "第1周", "description": "基础阶段", "tasks": [
          {"title": "背完高频词汇", "deadline": "2026-05-26", "task_type": "learning"},
          {"title": "做两套真题", "deadline": "2026-05-30", "task_type": "learning"}
        ]}]
        """
        try:
            import json
            stages_data = json.loads(stages_json) if stages_json else []
            stages = []
            for i, s in enumerate(stages_data):
                stages.append(schemas.PlanStage(
                    name=s.get("name", f"阶段{i+1}"),
                    description=s.get("description", ""),
                    order=s.get("order", i + 1),
                    tasks=s.get("tasks", []),
                ))

            plan_data = schemas.PlanCreate(
                user_id=user_id,
                title=title,
                description=description or None,
                stages=stages,
            )
            plan = crud.create_plan(db, plan_data)

            # 先创建主任务（代表整个计划，可展开查看子任务）
            total_exp = sum(
                task_info.get("exp_reward", 10)
                for stage in stages_data
                for task_info in stage.get("tasks", [])
            )
            main_task = crud.create_task(db, schemas.TaskCreate(
                user_id=user_id,
                title=title,
                description=description or f"共 {len(stages_data)} 个阶段",
                task_type=stages_data[0].get("tasks", [{}])[0].get("task_type", "other") if stages_data else "other",
                priority="medium",
                exp_reward=max(total_exp, 10),
                plan_id=plan.id,
            ))

            # 为每个阶段的小任务创建子任务（挂到主任务下）
            created_count = 0
            for stage in stages_data:
                for task_info in stage.get("tasks", []):
                    task_create = schemas.TaskCreate(
                        user_id=user_id,
                        parent_id=main_task.id,  # 关键：挂到主任务下作为子任务
                        title=task_info.get("title", "未命名任务"),
                        description=task_info.get("description", ""),
                        task_type=task_info.get("task_type", "other"),
                        priority=task_info.get("priority", "medium"),
                        deadline=datetime.fromisoformat(task_info["deadline"]) if task_info.get("deadline") else None,
                        exp_reward=task_info.get("exp_reward", 10),
                        plan_id=plan.id,
                    )
                    crud.create_task(db, task_create)
                    created_count += 1

            return (
                f"计划创建成功！\n"
                f"主任务：{main_task.title}（可展开查看 {created_count} 个子任务）\n"
                f"计划：{plan.title} 共 {len(stages_data)} 个阶段\n"
                f"计划ID: {plan.id}"
            )
        except Exception as e:
            return f"[ERROR:create_plan] 创建计划失败：{str(e)}"

    @tool
    def get_plan_progress(plan_id: int = 0) -> str:
        """查看指定计划的进度。plan_id 为 0 时返回所有计划列表。"""
        try:
            if plan_id == 0:
                plans = crud.get_plans(db, user_id)
                if not plans:
                    return "当前没有任何计划。"
                lines = ["📋 你的计划列表："]
                for p in plans:
                    progress = crud.get_plan_progress(db, p.id)
                    if progress:
                        bar = "█" * int(progress["progress_percent"] / 10) + "░" * (10 - int(progress["progress_percent"] / 10))
                        lines.append(
                            f"\n[{p.id}] {p.title} ({p.status})\n"
                            f"进度：{bar} {progress['progress_percent']}%\n"
                            f"已完成 {progress['completed_tasks']}/{progress['total_tasks']} 个任务"
                        )
                return "\n".join(lines)

            progress = crud.get_plan_progress(db, plan_id)
            if not progress:
                return f"找不到计划 #{plan_id}"

            bar = "█" * int(progress["progress_percent"] / 10) + "░" * (10 - int(progress["progress_percent"] / 10))
            return (
                f"📋 计划：{progress['title']}\n"
                f"状态：{progress['status']}\n"
                f"进度：{bar} {progress['progress_percent']}%\n"
                f"阶段：{progress['completed_stages']}/{progress['total_stages']} 完成\n"
                f"任务：{progress['completed_tasks']}/{progress['total_tasks']} 完成\n"
                f"当前阶段：{progress['current_stage'] or '待定'}"
            )
        except Exception as e:
            return f"[ERROR:get_plan_progress] 查询计划进度失败：{str(e)}"

    @tool
    def get_user_plans(status: str = None) -> str:
        """获取用户的计划列表。status 可选：active / completed / paused。"""
        query = db.query(models.Plan).filter(models.Plan.user_id == user_id)
        if status:
            query = query.filter(models.Plan.status == status)
        plans = query.order_by(models.Plan.created_at.desc()).all()

        if not plans:
            return "当前没有任何计划。"

        lines = ["📋 计划列表："]
        for p in plans:
            progress = crud.get_plan_progress(db, p.id)
            pct = progress["progress_percent"] if progress else 0
            lines.append(f"- [{p.id}] {p.title} | {p.status} | {pct}%")
        return "\n".join(lines)

    return [
        list_user_tasks,
        get_task_detail,
        create_user_task,
        complete_user_task,
        delete_user_task,
        get_user_stats,
        parse_task_intent,
        create_plan,
        get_plan_progress,
        get_user_plans,
    ]
