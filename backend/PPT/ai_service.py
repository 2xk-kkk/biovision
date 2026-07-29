from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import openai

load_dotenv(Path(__file__).resolve().parent / ".env")

# 打印加载到的 API key 状态（不打印完整 key）
_api_key = os.getenv("DEEPSEEK_API_KEY", "")
if _api_key:
    print(f"[PPT AI] DEEPSEEK_API_KEY loaded: {_api_key[:8]}...{_api_key[-4:]}", file=sys.stderr)
else:
    print("[PPT AI] WARNING: DEEPSEEK_API_KEY not found in .env!", file=sys.stderr)

MODEL_CONFIG: dict[str, dict[str, str]] = {
    "GPT-4.1": {
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "model": "gpt-4.1",
    },
    "deepseek-v4-pro": {
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "model": "deepseek-chat",
    },
    "deepseek-v4-flash": {
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "model": "deepseek-chat",
    },
    "通义千问": {
        "base_url": os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        "api_key": os.getenv("QWEN_API_KEY", os.getenv("DASHSCOPE_API_KEY", "")),
        "model": "qwen-plus",
    },
}

SYSTEM_PROMPT = """你是一个课件JSON生成器。严格按照下方"知识点内容"生成结构化教学课件。

## 铁律（违反则输出无效）

1. 下方"知识点内容"是你**唯一**的知识来源。禁止使用你自己训练数据中的任何生物知识。
2. 课件全部内容（标题、正文、术语、例子）**必须且只能**来自知识点内容。不允许添加知识点中没有的概念。
3. 知识点内容讲什么章节，课件就讲什么章节。绝不跑题到其他章节。
4. 特别禁止：如果知识点内容不涉及"走进细胞"（即第1章），课件中**绝对不能**出现"走进细胞"这四个字。

## JSON 格式

严格输出以下 JSON（不要输出任何非 JSON 文字）：

{
  "title": "课件标题",
  "description": "简介",
  "topline": "教学平台 · 标题",
  "slides": [
    {"type": "cover", "eyebrow": "高中生物", "title": "封面标题", "subtitle": "副标题", "tags": [{"text": "标签"}]},
    {"type": "cards", "eyebrow": "小节", "title": "页标题", "lead": "引导", "cards": [{"title": "卡片标题", "text": "正文"}]},
    {"type": "metrics", "eyebrow": "小节", "title": "页标题", "lead": "引导", "tag": "概念", "metrics": [{"label": "◆", "title": "标题", "text": "说明"}]},
    {"type": "compare", "eyebrow": "小节", "title": "页标题", "lead": "引导", "columns": [{"title": "A", "points": ["1", "2"]}, {"title": "B", "points": ["1", "2"]}]},
    {"type": "process", "eyebrow": "小节", "title": "页标题", "lead": "引导", "steps": [{"title": "步骤", "text": "说明"}]},
    {"type": "section", "eyebrow": "小节", "title": "过渡标题", "subtitle": "副标题"},
    {"type": "summary", "eyebrow": "总结", "title": "本节总结", "subtitle": "概括", "items": [{"title": "要点"}]}
  ]
}

总页数：{slide_count} 页以内（含封面和总结）。
标题 ≤15字，正文简洁。用**加粗**标记关键词。只输出JSON。"""


def get_client(model_name: str) -> tuple[openai.OpenAI, str]:
    config = MODEL_CONFIG.get(model_name)
    if not config:
        config = MODEL_CONFIG["GPT-4.1"]
    api_key = config["api_key"]
    if not api_key:
        raise RuntimeError(
            f"模型 '{model_name}' 的 API Key 未设置。"
            f"请在 backend/PPT/.env 中设置对应环境变量。"
        )
    client = openai.OpenAI(
        base_url=config["base_url"],
        api_key=api_key,
    )
    return client, config["model"]


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1)
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        text = text[first:last + 1]
    return json.loads(text)


def generate_deck(
    topic: str,
    requirements: str,
    knowledge_context: str,
    model_name: str = "GPT-4.1",
    slide_count: int = 8,
    style: str = "clean",
) -> dict[str, Any]:
    client, model_id = get_client(model_name)

    prompt = SYSTEM_PROMPT.replace("{slide_count}", str(slide_count))

    if knowledge_context:
        user_message = f"""## 知识点内容 —— 这是你生成课件的唯一依据

{knowledge_context}

---
课件主题：{topic}
额外要求：{requirements if requirements else '无'}
风格倾向：{style}

请严格基于上方"知识点内容"生成 JSON。不要输出任何 JSON 之外的内容。"""
    else:
        user_message = f"""课件主题：{topic}
用户需求：{requirements if requirements else '无'}
风格：{style}

注意：用户未指定知识点。请基于主题生成通用课件 JSON。只输出 JSON。"""

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"[PPT AI] Model: {model_name} -> {model_id}", file=sys.stderr)
    print(f"[PPT AI] Base URL: {client.base_url}", file=sys.stderr)
    print(f"[PPT AI] API Key used: {client.api_key[:8]}...{client.api_key[-4:]}", file=sys.stderr)
    print(f"[PPT AI] Topic: {topic}", file=sys.stderr)
    print(f"[PPT AI] Knowledge context: {len(knowledge_context)} chars", file=sys.stderr)
    if knowledge_context:
        print(f"[PPT AI] Knowledge preview: {knowledge_context[:200]}...", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=8000,
    )

    content = response.choices[0].message.content or ""
    usage = response.usage
    print(f"[PPT AI] Tokens used: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}", file=sys.stderr)
    print(f"[PPT AI] Response preview: {content[:400]}...", file=sys.stderr)

    return extract_json(content)
