"""PPT 生成相关接口"""
import os
import sys
import traceback
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Ensure PPT package is importable
_PPT_DIR = Path(__file__).resolve().parent.parent / "PPT"
if str(_PPT_DIR) not in sys.path:
    sys.path.insert(0, str(_PPT_DIR))

from generator import OUTPUT_DIR, ASSET_DIR, DeckError, write_deck
from knowledge_reader import build_knowledge_context, CHAPTER_NAMES, BOOK_NAMES

router = APIRouter()

ASSETS_DIR = str(ASSET_DIR)
OUTPUTS_DIR = str(OUTPUT_DIR)


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="课件主题")
    requirements: str = Field(default="", description="用户输入的详细需求")
    chapter_keys: list[str] = Field(default_factory=list, description="选中的知识点 key 列表")
    model: str = Field(default="GPT-4.1", description="模型名称")
    slide_count: int = Field(default=8, ge=4, le=15, description="生成页数")
    style: str = Field(default="clean", description="风格：clean/edu/tech")
    theme: str = Field(default="light", description="主题：light/dark")
    hue: int = Field(default=215, ge=0, le=360, description="主题色相值")


def _quoted_path(path: str) -> str:
    return quote(path, safe="/")


def _deck_file_path(deck_id: str) -> Path:
    if "/" in deck_id or "\\" in deck_id or deck_id in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="非法 deck_id")
    path = (OUTPUT_DIR / f"{deck_id}.html").resolve()
    if OUTPUT_DIR.resolve() not in path.parents:
        raise HTTPException(status_code=400, detail="非法 deck_id")
    if not path.exists():
        raise HTTPException(status_code=404, detail="课件不存在")
    return path


@router.post("/ppt/generate")
def generate(request: GenerateRequest):
    """核心接口：根据知识点和需求，调用AI生成课件HTML"""
    try:
        from ai_service import generate_deck

        knowledge_context = build_knowledge_context(request.chapter_keys)

        deck = generate_deck(
            topic=request.topic,
            requirements=request.requirements,
            knowledge_context=knowledge_context,
            model_name=request.model,
            slide_count=request.slide_count,
            style=request.style,
        )

        output = write_deck(deck, theme=request.theme, style=request.style, hue=request.hue)

        deck_id = output.stem
        return {
            "success": True,
            "deck_id": deck_id,
            "filename": output.name,
            "html_url": f"/api/ppt/decks/{deck_id}/html",
            "download_url": f"/api/ppt/decks/{deck_id}/download",
            "deck_json": deck,
        }
    except DeckError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="AI 模块未安装依赖，请运行: pip install openai python-dotenv"
        ) from exc
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成失败：{exc}") from exc


@router.get("/ppt/decks/{deck_id}/html")
def get_deck_html(deck_id: str):
    path = _deck_file_path(deck_id)
    return FileResponse(path, media_type="text/html; charset=utf-8")


@router.get("/ppt/decks/{deck_id}/download")
def download_deck(deck_id: str):
    path = _deck_file_path(deck_id)
    return FileResponse(path, media_type="application/octet-stream", filename=path.name)


@router.get("/ppt/decks")
def list_decks():
    """列出已生成的所有课件"""
    import re
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    decks = []
    for f in sorted(OUTPUT_DIR.glob("*.html"), key=lambda x: x.stat().st_mtime, reverse=True):
        # Extract title from filename: "走进细胞-20260729-201904.html" → title part
        stem = f.stem
        title_match = re.match(r"(.+?)-\d{8}-\d{6}", stem)
        title = title_match.group(1) if title_match else stem
        mtime = f.stat().st_mtime
        decks.append({
            "deck_id": stem,
            "filename": f.name,
            "title": title,
            "html_url": f"/api/ppt/decks/{stem}/html",
            "download_url": f"/api/ppt/decks/{stem}/download",
        })
    return {"decks": decks}


@router.get("/ppt/knowledge/chapters")
def list_chapters():
    chapters = []
    for key, name in CHAPTER_NAMES.items():
        book_key = key.split("-")[0]
        chapters.append({
            "key": key,
            "name": name,
            "book_key": book_key,
            "book_name": BOOK_NAMES.get(book_key, book_key),
        })
    return {"chapters": chapters}


@router.get("/ppt/knowledge/{chapter_key}")
def get_chapter_content(chapter_key: str):
    """获取单个章节的知识点文本内容"""
    content = build_knowledge_context([chapter_key])
    return {"chapter_key": chapter_key, "content": content}
