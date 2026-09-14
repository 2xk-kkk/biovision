"""LLM 调用封装：OpenAI 兼容客户端 + 同步流式生成。

所有模型（DeepSeek / 通义千问 / OpenAI）都走 OpenAI 兼容协议，只是 base_url 与 Key 不同。
"""

from __future__ import annotations

from typing import Iterator

import openai

from . import config


class LLMError(RuntimeError):
    """调用模型失败（Key 缺失、网络异常、上游报错等）。"""


def resolve(model_name: str | None) -> str:
    if model_name and model_name in config.MODEL_CONFIG:
        return model_name
    return config.DEFAULT_MODEL


def is_available(model_name: str) -> bool:
    cfg = config.MODEL_CONFIG.get(model_name)
    return bool(cfg and cfg["api_key"])


def get_client(model_name: str) -> tuple[openai.OpenAI, str, dict]:
    cfg = config.MODEL_CONFIG.get(model_name)
    if cfg is None:
        raise LLMError(f"未知模型：{model_name}")
    if not cfg["api_key"]:
        raise LLMError(
            f"模型「{cfg['label']}」的 API Key 未配置。"
            f"请在 backend/biovision-agent/.env 或 backend/PPT/.env 中设置对应的环境变量。"
        )
    client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    return client, cfg["model"], dict(cfg.get("params") or {})


def _build_params(model_name: str, messages: list[dict], stream: bool) -> tuple:
    client, model_id, params = get_client(model_name)
    call = {"model": model_id, "messages": messages, "stream": stream}
    call.update(params)
    return client, call


def _wrap_error(exc: Exception) -> LLMError:
    return LLMError(f"调用模型失败：{exc}")


def chat(messages: list[dict], model_name: str) -> tuple[str, dict]:
    """非流式调用，返回 (正文, 用量)。"""
    client, call = _build_params(model_name, messages, stream=False)
    try:
        resp = client.chat.completions.create(**call)
    except Exception as exc:  # openai 的各种异常统一收口
        raise _wrap_error(exc) from exc
    content = resp.choices[0].message.content or ""
    usage = {}
    if resp.usage:
        usage = {
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens": resp.usage.total_tokens,
        }
    return content, usage


def stream_chat(messages: list[dict], model_name: str) -> Iterator[tuple[str, str]]:
    """流式调用，逐段产出 (kind, text)。

    kind 为 "reasoning"（DeepSeek 深度思考的思维链）或 "content"（正式回答）。
    """
    client, call = _build_params(model_name, messages, stream=True)
    try:
        stream = client.chat.completions.create(**call)
    except Exception as exc:
        raise _wrap_error(exc) from exc

    try:
        for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue  # 最后一个含 usage 的包没有 choices
            delta = chunk.choices[0].delta
            if delta is None:
                continue
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                yield "reasoning", reasoning
            if delta.content:
                yield "content", delta.content
    except Exception as exc:
        raise _wrap_error(exc) from exc
