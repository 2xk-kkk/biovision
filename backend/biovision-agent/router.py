"""BioAgent 智能体 API 路由。

在 app.py 里以 prefix="/api" 注册（必须放在静态目录挂载之前，否则会被遮蔽）：

    POST   /api/agent/chat                   对话（默认 SSE 流式）
    POST   /api/agent/upload                 上传文档并抽取正文
    GET    /api/agent/conversations          会话列表
    GET    /api/agent/conversations/{id}     某个会话的消息
    DELETE /api/agent/conversations/{id}     删除会话
    GET    /api/agent/models                 可用模型
    GET    /api/agent/status                 知识库状态
    POST   /api/agent/kb/rebuild             重建知识库索引
"""

from __future__ import annotations

import json
import re
import tempfile
import threading
import traceback
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import config, documents, llm, platform, prompts, storage
from utils.jwt_utils import verify_jwt
from utils.response import ApiResponse

router = APIRouter()

storage.ensure_tables()

# 应用启动后就在后台把知识库索引准备好，别等用户发第一条消息才开始
threading.Thread(target=platform.ensure_ready, daemon=True).start()


# ---------------------------------------------------------------- 身份

def resolve_owner(request: Request, client_id: str | None = None) -> str:
    """登录用户按 user_id 归属，游客按前端生成的 client_id 归属。"""
    token = ""
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    if not token:
        token = request.headers.get("x-token") or request.query_params.get("token") or ""

    if token:
        try:
            res = verify_jwt(token)
            if res.get("success"):
                uid = (res.get("msg") or {}).get("user_id")
                if uid is not None:
                    return f"u:{uid}"
        except Exception:
            pass

    cid = (
        client_id
        or request.headers.get("x-client-id")
        or request.query_params.get("client_id")
        or ""
    )
    cid = re.sub(r"[^A-Za-z0-9_-]", "", cid)[:64]
    return f"c:{cid}" if cid else "c:anon"


# ---------------------------------------------------------------- 对话

class ChatRequest(BaseModel):
    message: str = Field(default="", description="用户输入")
    conversation_id: int | None = Field(default=None, description="不传则新建会话")
    attachment_ids: list[str] = Field(default_factory=list, description="已上传附件的 id")
    model: str | None = Field(default=None, description="模型 key")
    use_knowledge: bool = Field(default=True, description="是否检索平台知识库")
    stream: bool = Field(default=True, description="是否流式返回")


def _sse(payload: dict) -> str:
    return "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"


def _title_from(message: str, attachments: list[dict]) -> str:
    base = re.sub(r"\s+", " ", message or "").strip()
    if not base and attachments:
        base = attachments[0]["filename"]
    if not base:
        return "新对话"
    return base[:24] + ("…" if len(base) > 24 else "")


def _compose(messages_history: list[dict], user_content: str) -> list[dict]:
    return [
        {"role": "system", "content": prompts.SYSTEM_PROMPT},
        *[{"role": m["role"], "content": m["content"]} for m in messages_history],
        {"role": "user", "content": user_content},
    ]


@router.post("/agent/chat")
def chat(payload: ChatRequest, request: Request):
    owner = resolve_owner(request)
    message = (payload.message or "").strip()
    attachments = storage.get_attachments(payload.attachment_ids, owner)

    if not message and not attachments:
        raise HTTPException(status_code=400, detail="请先输入内容或上传文档")

    model = llm.resolve(payload.model)
    if not llm.is_available(model):
        raise HTTPException(
            status_code=400,
            detail=f"模型「{model}」尚未配置 API Key，请在 backend/biovision-agent/.env "
                   f"或 backend/PPT/.env 中补上",
        )

    # 会话：给了 id 就续聊，没有就新建
    conversation = None
    if payload.conversation_id:
        conversation = storage.get_conversation(payload.conversation_id, owner)
    is_new = conversation is None
    if is_new:
        conv_id = storage.create_conversation(owner, _title_from(message, attachments), model)
    else:
        conv_id = conversation["id"]

    # 历史要在写入本轮用户消息之前取，避免把自己也当成上下文
    history = [] if is_new else storage.recent_history(conv_id)

    doc_text = "\n\n".join(
        f"【{a['filename']}】\n{a['content']}" for a in attachments
    )
    sources: list[dict] = []
    knowledge_text = ""
    if payload.use_knowledge and message:
        try:
            found = platform.retrieve(message)
            knowledge_text = found["context"]
            sources = found["sources"]
        except Exception:
            traceback.print_exc()  # 检索失败不该阻断对话，降级为纯模型回答

    block = prompts.build_context_block(knowledge=knowledge_text, documents=doc_text)
    parts = [block] if block else []
    parts.append(f"【我的问题】{message}" if message else prompts.DOC_ONLY_NOTE)
    user_content = "\n\n".join(parts)

    storage.add_message(
        conv_id,
        "user",
        message,
        {
            "attachments": [{"id": a["id"], "filename": a["filename"]} for a in attachments],
            "model": model,
        },
    )
    storage.touch_conversation(conv_id, model=model)
    messages = _compose(history, user_content)

    if not payload.stream:
        try:
            answer, usage = llm.chat(messages, model)
        except llm.LLMError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        msg_id = storage.add_message(
            conv_id, "assistant", answer, {"model": model, "sources": sources, "usage": usage}
        )
        storage.touch_conversation(conv_id)
        return ApiResponse.success(
            {
                "conversation_id": conv_id,
                "message_id": msg_id,
                "content": answer,
                "sources": sources,
                "model": model,
            }
        )

    def generate():
        yield _sse(
            {
                "type": "meta",
                "conversation_id": conv_id,
                "is_new": is_new,
                "model": model,
                "sources": sources,
            }
        )
        chunks: list[str] = []
        try:
            for kind, text in llm.stream_chat(messages, model):
                if kind == "content":
                    chunks.append(text)
                yield _sse({"type": kind, "delta": text})
        except llm.LLMError as exc:
            yield _sse({"type": "error", "message": str(exc)})
            return
        except Exception as exc:  # 客户端中断等
            yield _sse({"type": "error", "message": f"生成中断：{exc}"})
            return

        answer = "".join(chunks) or "（模型没有返回内容，请重新提问）"
        msg_id = storage.add_message(
            conv_id, "assistant", answer, {"model": model, "sources": sources}
        )
        storage.touch_conversation(conv_id)
        yield _sse(
            {
                "type": "done",
                "conversation_id": conv_id,
                "message_id": msg_id,
                "content": answer,
            }
        )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------- 附件

@router.post("/agent/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    owner = resolve_owner(request)
    filename = file.filename or "未命名"
    ext = Path(filename).suffix.lower()

    if ext not in config.ALLOWED_UPLOAD_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"暂不支持 {ext or '该'} 格式，可上传："
                   + " / ".join(sorted(config.ALLOWED_UPLOAD_EXT)),
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件是空的")
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"文件不能超过 {config.MAX_UPLOAD_BYTES // 1024 // 1024} MB",
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        text = documents.extract(tmp_path, filename)
    except documents.ParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)

    saved = storage.save_attachment(owner, filename, ext, len(data), text)
    storage.purge_old_attachments(owner)
    return ApiResponse.success({**saved, "preview": text[:300]})


# ---------------------------------------------------------------- 会话

@router.get("/agent/conversations")
def list_conversations(request: Request, client_id: str | None = None):
    owner = resolve_owner(request, client_id)
    return ApiResponse.success(storage.list_conversations(owner))


@router.get("/agent/conversations/{conv_id}")
def get_conversation(conv_id: int, request: Request, client_id: str | None = None):
    owner = resolve_owner(request, client_id)
    conv = storage.get_conversation(conv_id, owner)
    if conv is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return ApiResponse.success({**conv, "messages": storage.get_messages(conv_id)})


@router.delete("/agent/conversations/{conv_id}")
def delete_conversation(conv_id: int, request: Request, client_id: str | None = None):
    owner = resolve_owner(request, client_id)
    if not storage.delete_conversation(conv_id, owner):
        raise HTTPException(status_code=404, detail="会话不存在")
    return ApiResponse.success(msg="已删除")


# ---------------------------------------------------------------- 元信息

@router.get("/agent/models")
def models():
    return ApiResponse.success(
        {"models": config.public_models(), "default": config.DEFAULT_MODEL}
    )


@router.get("/agent/status")
def kb_status():
    return ApiResponse.success(platform.status())


@router.post("/agent/kb/rebuild")
def kb_rebuild(sources: str = "", force: bool = True):
    """重建知识库索引。sources 用逗号分隔，留空则全部重建（含教材 PDF，较慢）。"""
    names = [s.strip() for s in sources.split(",") if s.strip()] or None
    result = platform.build(names, force=force)
    return ApiResponse.success({"result": result, "status": platform.status()})
