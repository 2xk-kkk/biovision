"""BioAgent 配置：API Key 加载、模型注册表、检索与上下文参数。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent        # backend/biovision-agent
BACKEND_DIR = BASE_DIR.parent                     # backend
PROJECT_DIR = BACKEND_DIR.parent                  # biovision2

# 包目录名带连字符，无法用 import 语句引入，这里把 backend 加入搜索路径，
# 方便包内模块直接 `from database.db import ...` 复用项目既有代码。
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 优先用智能体自己的 .env；没有则复用 PPT/.env 里已有的 Key，避免重复存放密钥。
# load_dotenv 默认不覆盖已有变量，所以先加载的优先级更高。
load_dotenv(BASE_DIR / ".env")
load_dotenv(BACKEND_DIR / "PPT" / ".env")
load_dotenv(PROJECT_DIR / ".env")

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
QWEN_KEY = os.getenv("QWEN_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))
QWEN_BASE = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# params 会原样透传给 chat.completions.create。
# deepseek-reasoner 不接受 temperature/top_p，故不配置。
MODEL_CONFIG: dict[str, dict] = {
    "deepseek-chat": {
        "label": "DeepSeek 快速",
        "desc": "响应快，适合日常答疑与知识点讲解",
        "base_url": DEEPSEEK_BASE,
        "api_key": DEEPSEEK_KEY,
        "model": os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat"),
        "params": {"temperature": 0.4, "max_tokens": 4000},
    },
    "deepseek-reasoner": {
        "label": "DeepSeek 深度思考",
        "desc": "先推理再作答，适合遗传计算、实验设计等难题",
        "base_url": DEEPSEEK_BASE,
        "api_key": DEEPSEEK_KEY,
        "model": "deepseek-reasoner",
        "params": {"max_tokens": 8000},
    },
    "qwen-plus": {
        "label": "通义千问 Plus",
        "desc": "阿里云百炼通道，中文长文本表现稳定",
        "base_url": QWEN_BASE,
        "api_key": QWEN_KEY,
        "model": "qwen-plus",
        "params": {"temperature": 0.4, "max_tokens": 4000},
    },
    "gpt-4.1": {
        "label": "GPT-4.1",
        "desc": "需要 OPENAI_API_KEY",
        "base_url": OPENAI_BASE,
        "api_key": OPENAI_KEY,
        "model": "gpt-4.1",
        "params": {"temperature": 0.4, "max_tokens": 4000},
    },
}

DEFAULT_MODEL = os.getenv("AGENT_DEFAULT_MODEL", "deepseek-chat")
if DEFAULT_MODEL not in MODEL_CONFIG:
    DEFAULT_MODEL = "deepseek-chat"

# ---- 检索与上下文 ----
TOP_K_DOCS = 8                # 送进模型的资料块数
MAX_CONTEXT_CHARS = 9000      # 参考资料总长度上限

# ---- 会话 ----
MAX_HISTORY_TURNS = 6         # 送入模型的历史轮数（1 轮 = 用户 + 助手）
MAX_HISTORY_CHARS = 6000      # 历史消息总长度上限

# ---- 附件 ----
MAX_ATTACHMENTS = 5
MAX_ATTACHMENT_CHARS = 12000  # 单个附件抽取文本上限
MAX_UPLOAD_BYTES = 20 * 1024 * 1024

ALLOWED_UPLOAD_EXT = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".md"}


def public_models() -> list[dict]:
    """给前端用的模型列表，只暴露是否已配置 Key，不泄露密钥。"""
    return [
        {
            "key": key,
            "label": cfg["label"],
            "desc": cfg["desc"],
            "available": bool(cfg["api_key"]),
        }
        for key, cfg in MODEL_CONFIG.items()
    ]
