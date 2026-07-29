from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any
from urllib.parse import quote

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ai_service import generate_deck
from generator import OUTPUT_DIR, ASSET_DIR, DeckError, render_deck, write_deck
from knowledge_reader import build_knowledge_context, CHAPTER_NAMES, BOOK_NAMES

PROJECT_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8770


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="课件主题")
    requirements: str = Field(default="", description="用户输入的详细需求")
    chapter_keys: list[str] = Field(default_factory=list, description="选中的知识点 key 列表，如 ['book1-ch1', 'book1-ch3']")
    model: str = Field(default="GPT-4.1", description="模型名称")
    slide_count: int = Field(default=8, ge=4, le=15, description="生成页数")
    style: str = Field(default="clean", description="风格：clean/edu/tech")
    theme: str = Field(default="light", description="主题：light/dark")


class GenerateResponse(BaseModel):
    success: bool
    deck_id: str
    filename: str
    html_url: str
    download_url: str
    deck_json: dict[str, Any] | None = None


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)


def quoted_api_path(path: str) -> str:
    return quote(path, safe="/")


def deck_path_from_id(deck_id: str) -> Path:
    if "/" in deck_id or "\\" in deck_id or deck_id in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="非法 deck_id。")
    path = (OUTPUT_DIR / f"{deck_id}.html").resolve()
    if OUTPUT_DIR.resolve() not in path.parents:
        raise HTTPException(status_code=400, detail="非法 deck_id。")
    if not path.exists():
        raise HTTPException(status_code=404, detail="课件不存在。")
    return path


app = FastAPI(
    title="AI 生物教学 PPT 生成 API",
    description="结合知识点库和 AI 大模型，自动生成结构化教学课件 HTML。",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_dirs()
app.mount("/assets", StaticFiles(directory=ASSET_DIR), name="assets")
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "project_dir": str(PROJECT_DIR),
        "outputs_dir": str(OUTPUT_DIR),
        "assets_dir": str(ASSET_DIR),
    }


@app.post("/api/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    """核心接口：根据知识点和需求，调用AI生成课件HTML。

    流程：知识内容提取 → AI生成JSON → 模板渲染HTML
    """
    try:
        # Step 1: Build knowledge context from selected chapters
        knowledge_context = build_knowledge_context(request.chapter_keys)

        # Step 2: Call AI to generate deck JSON
        deck = generate_deck(
            topic=request.topic,
            requirements=request.requirements,
            knowledge_context=knowledge_context,
            model_name=request.model,
            slide_count=request.slide_count,
            style=request.style,
        )

        # Step 3: Render and write HTML
        output = write_deck(deck)

        deck_id = output.stem
        html_url = quoted_api_path(f"/api/decks/{deck_id}/html")
        download_url = quoted_api_path(f"/api/decks/{deck_id}/download")

        return GenerateResponse(
            success=True,
            deck_id=deck_id,
            filename=output.name,
            html_url=html_url,
            download_url=download_url,
            deck_json=deck,
        )
    except DeckError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成失败：{exc}") from exc


@app.get("/api/decks/{deck_id}/html")
def get_deck_html(deck_id: str) -> FileResponse:
    path = deck_path_from_id(deck_id)
    return FileResponse(path, media_type="text/html; charset=utf-8")


@app.get("/api/decks/{deck_id}/download")
def download_deck(deck_id: str) -> FileResponse:
    path = deck_path_from_id(deck_id)
    return FileResponse(path, media_type="application/octet-stream", filename=path.name)


@app.get("/api/knowledge/chapters")
def list_chapters() -> dict[str, Any]:
    """返回所有可用的知识点章节列表（供前端参考）。"""
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


def main() -> None:
    uvicorn.run("api_server:app", host=HOST, port=PORT, reload=False, app_dir=str(PROJECT_DIR))


if __name__ == "__main__":
    main()
