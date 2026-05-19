"""用户统计画像生成器 —— 从数据库实时聚合用户行为特征"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from collections import Counter
import models


def generate_user_profile(db: Session, user_id: int) -> dict:
    """生成用户统计画像

    返回结构化数据，包含：
    - 基础属性（等级、经验值、四维属性）
    - 任务统计（总数、完成率、类型分布、优先级分布、平均奖励）
    - 时间习惯（活跃时段、最近活跃天数）
    - 计划统计（计划数、完成率）
    - 行为标签（LLM 可直接使用的自然语言描述）
    """
    profile = {
        "user_id": user_id,
        "basic": _get_basic_stats(db, user_id),
        "tasks": _get_task_stats(db, user_id),
        "plans": _get_plan_stats(db, user_id),
        "time_habits": _get_time_habits(db, user_id),
        "behavior_tags": [],
    }

    # 根据统计数据生成行为标签
    profile["behavior_tags"] = _generate_behavior_tags(profile)

    return profile


def format_profile_for_prompt(profile: dict) -> str:
    """将统计画像格式化为字符串，用于注入 Agent System Prompt"""
    if not profile:
        return ""

    basic = profile.get("basic", {})
    tasks = profile.get("tasks", {})
    plans = profile.get("plans", {})
    habits = profile.get("time_habits", {})
    tags = profile.get("behavior_tags", [])

    lines = ["\n=== 用户画像 ==="]

    # 基础属性
    lines.append(f"等级：Lv.{basic.get('level', 1)}  经验值：{basic.get('exp', 0)}/{basic.get('exp_needed', 100)}")
    stats = basic.get("stats", {})
    lines.append(f"属性：力量 {stats.get('str', 10)} | 智力 {stats.get('int', 10)} | 耐力 {stats.get('sta', 10)} | 专注 {stats.get('cha', 10)}")

    # 任务统计
    lines.append(f"\n任务总数：{tasks.get('total', 0)}  已完成：{tasks.get('completed', 0)}  完成率：{tasks.get('completion_rate', 0)}%")
    if tasks.get("type_distribution"):
        type_str = " | ".join([f"{k} {v}个" for k, v in tasks["type_distribution"].items()])
        lines.append(f"任务类型分布：{type_str}")
    if tasks.get("avg_exp_reward"):
        lines.append(f"平均任务奖励：{tasks['avg_exp_reward']:.0f} XP")

    # 时间习惯
    if habits.get("peak_hours"):
        lines.append(f"活跃时段：{', '.join(habits['peak_hours'])}点")

    # 计划统计
    lines.append(f"\n计划总数：{plans.get('total', 0)}  已完成计划：{plans.get('completed', 0)}")

    # 行为标签
    if tags:
        lines.append(f"\n行为特征：{'；'.join(tags)}")

    lines.append("=== 画像结束 ===\n")

    return "\n".join(lines)


def _get_basic_stats(db: Session, user_id: int) -> dict:
    """获取用户基础属性"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return {"level": 1, "exp": 0, "exp_needed": 100, "stats": {}}

    stats = user.stats
    return {
        "level": user.level,
        "exp": user.exp,
        "exp_needed": user.level * 100,
        "stats": {
            "str": stats.str_value if stats else 10,
            "int": stats.int_value if stats else 10,
            "sta": stats.sta_value if stats else 10,
            "cha": stats.cha_value if stats else 10,
        }
    }


def _get_task_stats(db: Session, user_id: int) -> dict:
    """获取用户任务统计"""
    tasks = db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.parent_id == None,  # 只统计主任务
    ).all()

    total = len(tasks)
    if total == 0:
        return {"total": 0, "completed": 0, "completion_rate": 0}

    completed = sum(1 for t in tasks if t.status == models.TaskStatus.DONE)
    completion_rate = round(completed / total * 100, 1)

    # 类型分布
    type_counts = Counter(t.task_type.value for t in tasks if t.task_type)
    type_distribution = dict(type_counts.most_common())

    # 优先级分布
    priority_counts = Counter(t.priority.value for t in tasks if t.priority)

    # 平均经验值
    avg_exp = sum(t.exp_reward or 10 for t in tasks) / total

    # 有截止日期的比例
    with_deadline = sum(1 for t in tasks if t.deadline)

    return {
        "total": total,
        "completed": completed,
        "completion_rate": completion_rate,
        "type_distribution": type_distribution,
        "priority_distribution": dict(priority_counts.most_common()),
        "avg_exp_reward": round(avg_exp, 1),
        "with_deadline_ratio": round(with_deadline / total * 100, 1),
    }


def _get_plan_stats(db: Session, user_id: int) -> dict:
    """获取用户计划统计"""
    plans = db.query(models.Plan).filter(models.Plan.user_id == user_id).all()
    total = len(plans)
    completed = sum(1 for p in plans if p.status == "completed")

    return {
        "total": total,
        "completed": completed,
        "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
    }


def _get_time_habits(db: Session, user_id: int) -> dict:
    """分析用户活跃时段（基于任务完成时间）"""
    completed_tasks = db.query(models.Task).filter(
        models.Task.user_id == user_id,
        models.Task.status == models.TaskStatus.DONE,
        models.Task.completed_at != None,
    ).all()

    if not completed_tasks:
        return {"peak_hours": [], "total_tracked": 0}

    # 按小时统计
    hour_counts = Counter()
    for t in completed_tasks:
        if t.completed_at:
            hour = t.completed_at.hour
            hour_counts[hour] += 1

    # 找 Top 3 活跃时段
    peak_hours = [f"{h}:00" for h, _ in hour_counts.most_common(3)]

    # 时段分类：早晨(6-12)、下午(12-18)、晚上(18-24)、深夜(0-6)
    period_counts = {"早晨": 0, "下午": 0, "晚上": 0, "深夜": 0}
    for h, count in hour_counts.items():
        if 6 <= h < 12:
            period_counts["早晨"] += count
        elif 12 <= h < 18:
            period_counts["下午"] += count
        elif 18 <= h < 24:
            period_counts["晚上"] += count
        else:
            period_counts["深夜"] += count

    dominant_period = max(period_counts, key=period_counts.get) if period_counts else "未知"

    return {
        "peak_hours": peak_hours,
        "dominant_period": dominant_period,
        "period_distribution": period_counts,
        "total_tracked": len(completed_tasks),
    }


def _generate_behavior_tags(profile: dict) -> list:
    """根据统计数据生成行为标签（自然语言描述）"""
    tags = []
    tasks = profile.get("tasks", {})
    plans = profile.get("plans", {})
    habits = profile.get("time_habits", {})
    basic = profile.get("basic", {})

    # 完成率标签
    cr = tasks.get("completion_rate", 0)
    if cr >= 80:
        tags.append("高效执行者")
    elif cr >= 50:
        tags.append("稳步推进")
    elif cr > 0:
        tags.append("需要督促")

    # 任务类型偏好
    type_dist = tasks.get("type_distribution", {})
    if type_dist:
        top_type = list(type_dist.keys())[0]
        type_labels = {
            "learning": "热爱学习",
            "work": "工作导向",
            "exercise": "注重健康",
            "social": "社交活跃",
            "other": "多元兴趣",
        }
        tags.append(type_labels.get(top_type, f"偏好{top_type}"))

    # 难度偏好
    avg_exp = tasks.get("avg_exp_reward", 10)
    if avg_exp >= 20:
        tags.append("喜欢挑战")
    elif avg_exp <= 8:
        tags.append("偏好简单任务")

    # 时间管理
    deadline_ratio = tasks.get("with_deadline_ratio", 0)
    if deadline_ratio >= 70:
        tags.append("时间规划型")
    elif deadline_ratio <= 20:
        tags.append("灵活安排型")

    # 活跃时段
    dominant = habits.get("dominant_period", "")
    if dominant:
        tags.append(f"{dominant}活跃")

    # 计划习惯
    plan_total = plans.get("total", 0)
    plan_cr = plans.get("completion_rate", 0)
    if plan_total >= 3:
        if plan_cr >= 60:
            tags.append("计划达人")
        else:
            tags.append("计划型但执行需加强")
    elif plan_total == 0 and tasks.get("total", 0) > 5:
        tags.append("习惯单线作战")

    # RPG 成长速度
    level = basic.get("level", 1)
    if level >= 10:
        tags.append("资深冒险者")
    elif level >= 5:
        tags.append("成长中")

    return tags
