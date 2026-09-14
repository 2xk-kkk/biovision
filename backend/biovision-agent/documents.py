"""上传文档的正文抽取。

支持 pdf / docx / doc / pptx / ppt / txt / md。
pptx、ppt 通过解压 OOXML/OLE 包读取 XML 文本，不额外引入 python-pptx 依赖。
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

from . import config

BACKEND_DIR = config.BACKEND_DIR
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

MAX_CHARS = config.MAX_ATTACHMENT_CHARS


class ParseError(RuntimeError):
    pass


def _clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _truncate(text: str) -> str:
    if len(text) <= MAX_CHARS:
        return text
    return text[:MAX_CHARS] + f"\n\n…（文档较长，仅保留前 {MAX_CHARS} 字）"


def _from_pdf(path: Path) -> str:
    import pdfplumber

    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"[第 {i} 页]\n{text}")
    return "\n\n".join(pages)


def _from_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def _from_doc(path: Path) -> str:
    """Word 97-2003 二进制格式，复用项目里已有的 OLE 解析器。"""
    from service.doc_parser import read_doc_text

    return read_doc_text(str(path))


def _slide_sort_key(name: str) -> int:
    m = re.search(r"(\d+)", name.rsplit("/", 1)[-1])
    return int(m.group(1)) if m else 0


def _from_pptx(path: Path) -> str:
    """pptx 就是 zip，逐个读 ppt/slides/slideN.xml。"""
    slides = []
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
        for name in sorted(names, key=_slide_sort_key):
            raw = zf.read(name).decode("utf-8", errors="ignore")
            raw = re.sub(r"<a:br\s*/>", "\n", raw)
            raw = re.sub(r"</a:p>", "\n", raw)
            raw = re.sub(r"<[^>]+>", "", raw)
            text = _clean(raw)
            if text:
                slides.append(f"[第 {_slide_sort_key(name)} 页]\n{text}")
    return "\n\n".join(slides)


def _from_ppt(path: Path) -> str:
    """老版 ppt（OLE）没有结构化解析器，退回按可打印串抽取。"""
    from service.doc_parser import read_doc_text

    return read_doc_text(str(path))


def _from_plain(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "gb18030", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


_DISPATCH = {
    ".pdf": _from_pdf,
    ".docx": _from_docx,
    ".doc": _from_doc,
    ".pptx": _from_pptx,
    ".ppt": _from_ppt,
    ".txt": _from_plain,
    ".md": _from_plain,
}


def extract(path: Path, filename: str) -> str:
    """抽取文档正文，失败时抛 ParseError（调用方转成 400）。"""
    ext = Path(filename).suffix.lower()
    handler = _DISPATCH.get(ext)
    if handler is None:
        raise ParseError(f"不支持的文件类型：{ext or '(无扩展名)'}")

    try:
        text = handler(path)
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError(f"文档解析失败：{exc}") from exc

    text = _truncate(_clean(text))
    if not text:
        raise ParseError("没有从文档中提取到文字（可能是扫描件或纯图片文档）")
    return text
