import os
import json
from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
API_KEY = os.getenv("OPENAI_API_KEY", "")
BASE_URL = os.getenv("OPENAI_BASE_URL", "")

client = None
if API_KEY:
    kwargs = {"api_key": API_KEY}
    if BASE_URL:
        kwargs["base_url"] = BASE_URL
    client = OpenAI(**kwargs)

TASK_PARSE_PROMPT = """你是一个智能任务管理AI助手。请分析用户的自然语言描述，提取任务信息并返回标准JSON格式。

你需要判断：
1. 任务的标题（title）
2. 任务的详细描述（description）
3. 优先级（priority）：low / medium / high / urgent
4. 任务类型（task_type）：learning（学习）/ work（工作）/ exercise（运动）/ social（社交）/ other（其他）
5. 截止日期（deadline）：YYYY-MM-DD 格式，如没有则 null
6. 经验奖励（exp_reward）：基础任务10，困难20-50
7. 子任务列表（subtasks），每个子任务包含 title 和 priority
8. AI回复文本（reply）：用中文友好地回复用户

返回JSON格式示例：
{
  "title": "期末考试复习",
  "description": "为期末考试做准备，复习重点科目",
  "priority": "high",
  "task_type": "learning",
  "deadline": "2024-06-15",
  "exp_reward": 30,
  "subtasks": [
    {"title": "复习数学第三章", "priority": "high"},
    {"title": "整理英语单词", "priority": "medium"}
  ],
  "reply": "已为你规划期末考试复习任务！包含数学和英语两个子任务，预计可获得30点经验值。加油！"
}

规则：
- 学习类任务 → INT 智力属性
- 工作类任务 → STR 力量属性
- 运动类任务 → STA 体力属性
- 社交类任务 → CHA 魅力属性
- 只返回纯JSON，不要markdown代码块，不要其他文字
"""


def parse_task_from_text(user_input: str) -> dict:
    """调用LLM将自然语言解析为结构化任务JSON"""
    if not client:
        return _fallback_parse(user_input)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": TASK_PARSE_PROMPT},
                {"role": "user", "content": user_input},
            ],
            temperature=0.3,
            max_tokens=1500,
        )

        content = response.choices[0].message.content.strip()
        # 尝试提取JSON（可能包裹在markdown代码块中）
        content = _extract_json(content)
        result = json.loads(content)
        return _normalize_result(result)

    except Exception as e:
        return _fallback_parse(user_input, str(e))


def _extract_json(text: str) -> str:
    """从可能包含markdown代码块的文本中提取JSON"""
    text = text.strip()
    if text.startswith("```"):
        # 移除 ```json 或 ``` 开头
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _normalize_result(result: dict) -> dict:
    """规范化LLM返回的结果，确保字段存在"""
    return {
        "title": result.get("title", "新任务"),
        "description": result.get("description", ""),
        "priority": result.get("priority", "medium"),
        "task_type": result.get("task_type", "other"),
        "deadline": result.get("deadline") or None,
        "exp_reward": result.get("exp_reward", 10),
        "subtasks": result.get("subtasks", []),
        "reply": result.get("reply", "任务已生成"),
    }


def _fallback_parse(user_input: str, error_msg: str = "") -> dict:
    """当API不可用时，使用简单的规则解析"""
    exp_reward = 10
    task_type = "other"
    priority = "medium"

    # 简单的关键词匹配
    text_lower = user_input.lower()
    if any(k in text_lower for k in ["学习", "考试", "复习", "读书", "课程", "论文"]):
        task_type = "learning"
        exp_reward = 20
    elif any(k in text_lower for k in ["工作", "项目", "报告", "会议", "代码", "开发"]):
        task_type = "work"
        exp_reward = 20
    elif any(k in text_lower for k in ["运动", "健身", "跑步", "锻炼", "瑜伽"]):
        task_type = "exercise"
        exp_reward = 15
    elif any(k in text_lower for k in ["社交", "聚会", "朋友", "约会", "聊天"]):
        task_type = "social"
        exp_reward = 15

    if any(k in text_lower for k in ["紧急", "马上", "立即", " deadline", "明天"]):
        priority = "high"
    if any(k in text_lower for k in ["非常重要", "关键", "必须"]):
        priority = "urgent"

    reply = f"已为你生成任务：「{user_input[:30]}...」"
    if error_msg:
        reply = f"[API调用失败，使用本地规则] {reply}"

    return {
        "title": user_input[:30] if len(user_input) <= 30 else user_input[:30] + "...",
        "description": user_input,
        "priority": priority,
        "task_type": task_type,
        "deadline": None,
        "exp_reward": exp_reward,
        "subtasks": [],
        "reply": reply,
    }
