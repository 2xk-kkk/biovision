"""把整个平台做成知识库：索引构建 + BM25 检索 + 参考资料组装。

索引覆盖平台已有的全部教学内容：

    guide            平台使用指南（platform_guide.md，每个 ## 小节一条）
    knowledge        知识清单 HTML（必修一 ~ 选必三，26 章）
    knowledge_points 知识点表（474 条，带分类与关键词）
    questions        题库（4491 道，含选项/答案/解析）
    models           可视学习 3D 模型目录（30 个）
    textbook         电子教材 PDF 原文（5 册，约 480k 字）

分源缓存到 .cache/kb.json，缓存里同时存正文和分词结果（tf），因此进程重启只需
反序列化、不必重新分词。前四项是快源，教材 PDF 较慢，放在后台线程里建；
谁的缓存有效就用谁，首次请求不会卡在教材解析上。
"""

from __future__ import annotations

import json
import math
import re
import threading
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from . import config, knowledge

CACHE_DIR = config.BASE_DIR / ".cache"
CACHE_FILE = CACHE_DIR / "kb.json"
INDEX_VERSION = 3

SOURCE_ORDER = ["guide", "knowledge", "knowledge_points", "questions", "models", "textbook"]

# 教材原文最权威，知识清单经过整理，题库只作参考；
# 平台自述资料（使用指南）只在问平台功能时才该冒头，权重取中位。
SOURCE_WEIGHT = {
    "knowledge": 1.45,
    "textbook": 1.30,
    "knowledge_points": 1.20,
    "guide": 1.10,
    "models": 0.95,
    "questions": 0.80,
}

SOURCE_LABEL = {
    "knowledge": "知识清单",
    "textbook": "电子教材",
    "knowledge_points": "知识点",
    "guide": "平台指南",
    "questions": "题库",
    "models": "可视学习",
}

SLOW_SOURCES = {"textbook"}

BM25_K1 = 1.5
BM25_B = 0.75

_lock = threading.Lock()
_cache: dict | None = None
_index: "_Index | None" = None
_building: set[str] = set()
_errors: dict[str, str] = {}
_progress: dict[str, str] = {}
_checked = False


def log(msg: str) -> None:
    print(f"[KB] {msg}", flush=True)


# ---------------------------------------------------------------- 文档源

def _doc(doc_id, source, title, subtitle, link, text):
    return {
        "id": doc_id,
        "source": source,
        "title": title,
        "subtitle": subtitle,
        "link": link,
        "text": text,
    }


GUIDE_FILE = config.BASE_DIR / "platform_guide.md"

# 指南里只有 Markdown 标记，去掉后更贴近自然语言，检索和喂给模型都更干净
_MD_MARK = re.compile(r"(\*\*|`|^\s*[-*]\s+)", re.MULTILINE)
_ENTRY_RE = re.compile(r"入口：\s*(\S+)")


def _load_guide() -> tuple[str, list[dict]]:
    """把 platform_guide.md 按 ## 小节切成文档，每节一条，便于精确检索。"""
    if not GUIDE_FILE.exists():
        return "", []
    raw = GUIDE_FILE.read_text(encoding="utf-8", errors="ignore")
    st = GUIDE_FILE.stat()

    docs = []
    # 第一个 ## 之前是文件用途说明，不属于平台内容，跳过
    sections = re.split(r"(?m)^##\s+", raw)[1:]
    for i, section in enumerate(sections):
        lines = section.splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        body = _MD_MARK.sub("", "\n".join(lines[1:])).strip()
        if not title or not body:
            continue
        m = _ENTRY_RE.search(body)
        docs.append(
            _doc(
                f"guide:{i}",
                "guide",
                title,
                "平台使用指南",
                m.group(1) if m else "",
                body,
            )
        )
    return f"{int(st.st_mtime)}:{st.st_size}", docs


def _guide_signature() -> str:
    if not GUIDE_FILE.exists():
        return ""
    st = GUIDE_FILE.stat()
    return f"{int(st.st_mtime)}:{st.st_size}"


def _load_knowledge() -> tuple[str, list[dict]]:
    docs, sig = [], []
    for name, chapter_key in knowledge.CHAPTER_NAME_TO_KEY.items():
        path = knowledge.chapter_html_path(chapter_key)
        if path is None:
            continue
        st = path.stat()
        sig.append(f"{path.name}:{int(st.st_mtime)}:{st.st_size}")
        text = knowledge.html_to_text(path.read_text(encoding="utf-8", errors="ignore"))
        book = knowledge.BOOK_LABELS.get(chapter_key.split("-")[0], "")
        link = knowledge.chapter_link(chapter_key)
        for i, chunk in enumerate(knowledge.split_chunks(text)):
            docs.append(_doc(f"knowledge:{chapter_key}:{i}", "knowledge", name, book, link, chunk))
    return "|".join(sig), docs


def _load_knowledge_points() -> tuple[str, list[dict]]:
    from database.db import get_db_connection

    db = get_db_connection()
    try:
        rows = db.cursor().execute(
            "SELECT id, chapter_key, book, chapter, section_name, label_text, category, key_terms "
            "FROM knowledge_points ORDER BY id"
        ).fetchall()
    finally:
        db.close()

    docs = []
    for pid, chapter_key, book, chapter, section, label, category, key_terms in rows:
        try:
            terms = " ".join(json.loads(key_terms)) if key_terms else ""
        except (json.JSONDecodeError, TypeError):
            terms = ""
        link = knowledge.chapter_link(chapter_key) if chapter_key else ""
        docs.append(
            _doc(
                f"kp:{pid}",
                "knowledge_points",
                (label or "").strip(),
                f"{book} · {chapter} · {section or ''}".strip(" ·"),
                link,
                f"{label}\n关键词：{terms}".strip(),
            )
        )
    return _db_signature(rows), docs


def _load_questions() -> tuple[str, list[dict]]:
    from database.db import get_db_connection

    db = get_db_connection()
    try:
        rows = db.cursor().execute(
            "SELECT id, textbook, chapter, section, type, stem, "
            "option_a, option_b, option_c, option_d, answer, analysis FROM questions ORDER BY id"
        ).fetchall()
    finally:
        db.close()

    type_label = {"choice": "选择题", "fill": "填空题", "essay": "简答题"}
    docs = []
    for qid, textbook, chapter, section, qtype, stem, a, b, c, d, ans, analysis in rows:
        stem = (stem or "").strip()
        if not stem:
            continue
        parts = [stem]
        options = [f"{chr(64 + i)}. {o}" for i, o in enumerate((a, b, c, d), 1) if o]
        if options:
            parts.append("选项：" + "  ".join(options))
        if ans:
            parts.append(f"答案：{ans}")
        if analysis:
            parts.append(f"解析：{analysis}")
        docs.append(
            _doc(
                f"q:{qid}",
                "questions",
                re.sub(r"\s+", " ", stem)[:40],
                f"{textbook or ''} · {chapter or ''} · {type_label.get(qtype, qtype or '')}".strip(" ·"),
                "",
                "\n".join(parts),
            )
        )
    return _db_signature(rows), docs


def _load_models() -> tuple[str, list[dict]]:
    from model.model_favorite import MODEL_CATALOG

    docs = []
    for m in MODEL_CATALOG:
        page = m.get("page") or ""
        docs.append(
            _doc(
                f"model:{m['id']}",
                "models",
                f"{m.get('name', '')}（3D 模型）",
                f"{m.get('book', '')} · {m.get('tag', '')}".strip(" ·"),
                "/3D%20model/" + page if page else "",
                f"{m.get('name', '')}：{m.get('desc', '')}",
            )
        )
    return _models_signature(), docs


def _load_textbook() -> tuple[str, list[dict]]:
    import logging

    import pdfplumber

    # 教材 PDF 里有些颜色格式不规范，pdfminer 会刷一屏警告，压掉
    logging.getLogger("pdfminer").setLevel(logging.ERROR)

    docs = []
    for book_key, filename in knowledge.TEACHING_BOOKS.items():
        path = knowledge.TEACHING_BOOK_DIR / filename
        if not path.exists():
            continue
        label = knowledge.BOOK_LABELS[book_key]
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(text)
        body = knowledge.html_to_text("\n\n".join(pages))
        for i, chunk in enumerate(knowledge.split_chunks(body, size=800)):
            docs.append(_doc(f"tb:{book_key}:{i}", "textbook", label, "电子教材原文", "", chunk))
    return _textbook_signature(), docs


LOADERS = {
    "guide": _load_guide,
    "knowledge": _load_knowledge,
    "knowledge_points": _load_knowledge_points,
    "questions": _load_questions,
    "models": _load_models,
    "textbook": _load_textbook,
}


# ---------------------------------------------------------------- 源签名
# 签名只比 mtime/size/行数，不解析正文；用于判断缓存是否还有效。

def _db_signature(rows) -> str:
    last_id = rows[-1][0] if rows else 0
    return f"{len(rows)}:{last_id}"


def _knowledge_signature() -> str:
    parts = []
    for chapter_key in knowledge.CHAPTER_NAME_TO_KEY.values():
        path = knowledge.chapter_html_path(chapter_key)
        if path is None:
            continue
        st = path.stat()
        parts.append(f"{path.name}:{int(st.st_mtime)}:{st.st_size}")
    return "|".join(parts)


def _textbook_signature() -> str:
    parts = []
    for book_key, filename in knowledge.TEACHING_BOOKS.items():
        path = knowledge.TEACHING_BOOK_DIR / filename
        if not path.exists():
            continue
        st = path.stat()
        parts.append(f"{book_key}:{int(st.st_mtime)}:{st.st_size}")
    return "|".join(parts)


def _models_signature() -> str:
    from model.model_favorite import MODEL_CATALOG

    return ",".join(m["id"] for m in MODEL_CATALOG)


def _questions_signature() -> str:
    from database.db import get_db_connection

    db = get_db_connection()
    try:
        row = db.cursor().execute("SELECT COUNT(*), COALESCE(MAX(id), 0) FROM questions").fetchone()
    finally:
        db.close()
    return f"{row[0]}:{row[1]}"


def _points_signature() -> str:
    from database.db import get_db_connection

    db = get_db_connection()
    try:
        row = db.cursor().execute(
            "SELECT COUNT(*), COALESCE(MAX(id), 0) FROM knowledge_points"
        ).fetchone()
    finally:
        db.close()
    return f"{row[0]}:{row[1]}"


SIGNATURE_FN = {
    "guide": _guide_signature,
    "knowledge": _knowledge_signature,
    "textbook": _textbook_signature,
    "models": _models_signature,
    "questions": _questions_signature,
    "knowledge_points": _points_signature,
}


def current_signature(name: str) -> str:
    try:
        return SIGNATURE_FN[name]()
    except Exception:
        return ""


# ---------------------------------------------------------------- 缓存

def _load_cache(force: bool = False) -> dict:
    global _cache
    if _cache is not None and not force:
        return _cache
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        if data.get("version") != INDEX_VERSION:
            data = {}
    except (OSError, json.JSONDecodeError):
        data = {}
    data.setdefault("version", INDEX_VERSION)
    data.setdefault("sources", {})
    _cache = data
    return _cache


def _flush_cache() -> None:
    if _cache is None:
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(_cache, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CACHE_FILE)


def _tokenize_docs(docs: list[dict]) -> list[dict]:
    """预先算好每块的词频，存进缓存，避免每次启动重新分词。"""
    out = []
    for d in docs:
        counts: dict[str, int] = defaultdict(int)
        for t in knowledge.tokenize(f"{d['title']} {d['text']}"):
            counts[t] += 1
        out.append(dict(counts))
    return out


def _store_source(name: str, signature: str, docs: list[dict]) -> None:
    assert _cache is not None
    _cache["sources"][name] = {
        "signature": signature,
        "built_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "docs": docs,
        "tf": _tokenize_docs(docs),
    }


def build(sources: list[str] | None = None, force: bool = False) -> dict:
    """构建（或重建）指定源的索引，返回 {源: 结果说明}。"""
    names = sources or SOURCE_ORDER
    cache = _load_cache()
    result = {}

    for name in names:
        if name not in LOADERS:
            result[name] = "未知数据源"
            continue
        with _lock:
            if name in _building:
                result[name] = "正在构建中"
                continue
            old = cache["sources"].get(name)
            if not force and old and old.get("signature") == current_signature(name):
                _progress[name] = "缓存有效"
                result[name] = "跳过（缓存有效）"
                continue
            _building.add(name)
            _progress[name] = "构建中…"

        try:
            t0 = time.time()
            log(f"正在构建 {name} …")
            signature, docs = LOADERS[name]()
            with _lock:
                _store_source(name, signature, docs)
                _flush_cache()
            _progress[name] = f"完成（{len(docs)} 块，{time.time() - t0:.1f}s）"
            _errors.pop(name, None)
            result[name] = "已重建"
            log(f"{name} 完成：{len(docs)} 块，耗时 {time.time() - t0:.1f}s")
        except Exception as exc:
            _errors[name] = str(exc)
            _progress[name] = f"失败：{exc}"
            result[name] = f"失败：{exc}"
            log(f"{name} 构建失败：{exc}")
        finally:
            with _lock:
                _building.discard(name)

    reload_index()
    return result


# ---------------------------------------------------------------- 内存索引

class _Index:
    def __init__(self, docs: list[dict], tfs: list[dict | None]) -> None:
        self.docs = docs
        self.postings: dict[str, dict[int, int]] = defaultdict(dict)
        self.df: dict[str, int] = {}
        self.dl: list[int] = []
        self.title_tokens: list[frozenset[str]] = []

        for i, doc in enumerate(docs):
            tf = tfs[i] if i < len(tfs) else None
            if not tf:
                counts: dict[str, int] = defaultdict(int)
                for t in knowledge.tokenize(f"{doc['title']} {doc['text']}"):
                    counts[t] += 1
                tf = counts
            for t, c in tf.items():
                self.postings[t][i] = c
                self.df[t] = self.df.get(t, 0) + 1
            self.dl.append(max(sum(tf.values()), 1))
            self.title_tokens.append(frozenset(knowledge.tokenize(doc["title"])))

        self.n = len(docs)
        self.avgdl = (sum(self.dl) / self.n) if self.n else 1.0

    def search(self, query: str, limit: int) -> list[int]:
        tokens = knowledge.tokenize(query)
        if not tokens or not self.n:
            return []

        scores: dict[int, float] = defaultdict(float)
        matched: dict[int, int] = defaultdict(int)
        strong: set[int] = set()
        title_hits: dict[int, int] = defaultdict(int)

        for t in tokens:
            df = self.df.get(t)
            if not df:
                continue
            idf = math.log(1 + (self.n - df + 0.5) / (df + 0.5))
            is_term = knowledge.is_bio_term(t)
            for i, tf in self.postings[t].items():
                denom = tf + BM25_K1 * (1 - BM25_B + BM25_B * self.dl[i] / self.avgdl)
                scores[i] += idf * tf * (BM25_K1 + 1) / denom
                matched[i] += 1
                if is_term:
                    strong.add(i)
                if t in self.title_tokens[i]:
                    title_hits[i] += 1

        ranked = []
        for i, s in scores.items():
            # 相关度闸门：只命中一个普通词、且不是术语也没进标题的，判为噪声丢掉。
            # 否则问「今天天气怎么样」也会捞出一堆刚好提到"天气"的教材段落。
            if matched[i] < 2 and i not in strong and not title_hits[i]:
                continue
            s *= SOURCE_WEIGHT.get(self.docs[i]["source"], 1.0)
            # 标题命中额外加权：问「光合作用」时，标题就叫光合作用的资料更该靠前
            if title_hits[i]:
                s *= 1 + min(title_hits[i], 4) * 0.15
            ranked.append((s, i))

        if not ranked:
            return []
        ranked.sort(key=lambda x: (-x[0], self.docs[x[1]]["id"]))
        # 再砍掉长尾：明显弱于首条的就不必塞进提示词了
        floor = ranked[0][0] * 0.2
        # 同源限流：模型目录（30 条）、题库（4491 条）这类同质条目标题高度相似，
        # 不限流的话一次检索会被同一个源占满——问「3D 模型有多少个」全是单个模型，
        # 平台指南反而进不来；问「试卷练习在哪」则全是答题须知。
        cap = max(2, limit // 2)
        per_source: dict[str, int] = defaultdict(int)
        picked: list[int] = []
        for s, i in ranked:
            if s < floor and len(ranked) > 3:
                break
            src = self.docs[i]["source"]
            if per_source[src] >= cap:
                continue
            per_source[src] += 1
            picked.append(i)
            if len(picked) >= limit:
                break
        return picked


def reload_index() -> None:
    global _index
    cache = _load_cache()
    docs: list[dict] = []
    tfs: list[dict | None] = []
    for name in SOURCE_ORDER:
        entry = cache["sources"].get(name) or {}
        entry_docs = entry.get("docs") or []
        entry_tf = entry.get("tf") or []
        docs.extend(entry_docs)
        tfs.extend(entry_tf[i] if i < len(entry_tf) else None for i in range(len(entry_docs)))
    _index = _Index(docs, tfs) if docs else None
    log(f"内存索引就绪：{len(docs)} 块")


def ensure_ready() -> None:
    """进程内首次调用时加载缓存、补齐缺失的源；之后只做一次廉价检查。

    快的源（知识清单/知识点/题库/模型）同步建，教材 PDF 交给后台线程，
    这样第一个请求不会被几十秒的 PDF 解析挡住。
    """
    global _checked
    with _lock:
        first = not _checked
        _checked = True

    if not first:
        # 后台建完索引后，这里把新缓存挂到内存里
        if _index is None:
            reload_index()
        return

    cache = _load_cache()
    stored = cache["sources"]

    stale = [
        n
        for n in SOURCE_ORDER
        if not stored.get(n, {}).get("docs") or stored[n].get("signature") != current_signature(n)
    ]
    if stale:
        log(f"需要构建的数据源：{', '.join(stale)}")

    fast = [n for n in stale if n not in SLOW_SOURCES]
    slow = [n for n in stale if n in SLOW_SOURCES]

    if fast:
        build(fast)
    else:
        reload_index()

    if slow:
        threading.Thread(target=build, args=(slow,), daemon=True).start()
        _progress.update({n: "后台构建中…" for n in slow})


# ---------------------------------------------------------------- 检索与上下文

def _snippet(text: str, tokens: list[str], width: int = 110) -> str:
    flat = re.sub(r"\s+", " ", text or "").strip()
    if not flat:
        return ""
    pos = -1
    for t in tokens:
        pos = flat.find(t)
        if pos >= 0:
            break
    if pos < 0:
        return flat[:width] + ("…" if len(flat) > width else "")
    start = max(0, pos - width // 2)
    frag = flat[start : start + width]
    return ("…" if start else "") + frag + ("…" if start + width < len(flat) else "")


def retrieve(query: str, limit: int = config.TOP_K_DOCS) -> dict:
    """检索平台知识库，返回 {context, sources}。"""
    ensure_ready()
    tokens = knowledge.tokenize(query)

    picked: list[dict] = []
    if _index is not None:
        selected = list(_index.search(query, limit))
        # 问题点名了某章节时，即使 BM25 没排进前几名也把该章节补进来
        wanted = {knowledge.CHAPTER_KEY_TO_NAME.get(c, "") for c in knowledge.route_chapters(query, tokens)}
        wanted.discard("")
        chosen = {i for i in selected}
        for i, d in enumerate(_index.docs):
            if not wanted:
                break
            if len(chosen) >= limit + 3:
                break
            if d["source"] == "knowledge" and d["title"] in wanted and i not in chosen:
                chosen.add(i)
                selected.append(i)
        picked = [_index.docs[i] for i in selected]

    if not picked:
        return {"context": "", "sources": []}

    total = 0
    blocks, sources, seen = [], [], set()
    for d in picked:
        body = (d["text"] or "").strip()
        if not body:
            continue
        remain = config.MAX_CONTEXT_CHARS - total
        if remain <= 0:
            break
        if len(body) > remain:
            body = body[:remain]

        label = SOURCE_LABEL.get(d["source"], d["source"])
        head = f"### [{label}] {d['title']}"
        if d["subtitle"]:
            head += f" —— {d['subtitle']}"
        blocks.append(f"{head}\n{body}")
        total += len(body)

        key = (d["title"], d["subtitle"])
        if key not in seen and len(sources) < 8:
            seen.add(key)
            sources.append(
                {
                    "title": d["title"],
                    "subtitle": d["subtitle"],
                    "type": label,
                    "link": d.get("link") or "",
                    "snippet": _snippet(d["text"], tokens),
                }
            )

    return {"context": "\n\n".join(blocks), "sources": sources}


# ---------------------------------------------------------------- 状态

def status() -> dict:
    cache = _load_cache()
    stored = cache["sources"]
    out = {
        "ready": _index is not None,
        "docs": len(_index.docs) if _index else 0,
        "cache_file": str(CACHE_FILE),
        "sources": {},
    }
    for name in SOURCE_ORDER:
        entry = stored.get(name)
        out["sources"][name] = {
            "label": SOURCE_LABEL.get(name, name),
            "docs": len(entry.get("docs", [])) if entry else 0,
            "built_at": entry.get("built_at") if entry else None,
            "state": (
                "构建中"
                if name in _building
                else (_progress.get(name) or ("未构建" if not entry else "已就绪"))
            ),
            "error": _errors.get(name, ""),
        }
    return out
