from __future__ import annotations

import re
from pathlib import Path
from html.parser import HTMLParser

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "knowledge"


def _chapter_key_to_path(key: str) -> Path:
    parts = key.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid chapter key: {key}")
    book = parts[0]
    num = parts[1].replace("ch", "")
    filename = f"{book[-1]}.{num}.html"
    return KNOWLEDGE_DIR / book / filename


BOOK_NAMES = {
    "book1": "必修一：分子与细胞",
    "book2": "必修二：遗传与进化",
    "book3": "选择性必修一：稳态与调节",
    "book4": "选择性必修二：生物与环境",
    "book5": "选择性必修三：生物技术与工程",
}

CHAPTER_NAMES = {
    "book1-ch1": "走进细胞",
    "book1-ch2": "组成细胞的分子",
    "book1-ch3": "细胞的基本结构",
    "book1-ch4": "细胞的物质输入与输出",
    "book1-ch5": "细胞的能量供应与应用",
    "book1-ch6": "细胞的生命历程",
    "book2-ch1": "遗传因子的发现",
    "book2-ch2": "基因和染色体的关系",
    "book2-ch3": "基因的本质",
    "book2-ch4": "基因的表达",
    "book2-ch5": "基因突变及其他变异",
    "book2-ch6": "生物的进化",
    "book3-ch1": "人体的内环境与稳态",
    "book3-ch2": "神经调节",
    "book3-ch3": "体液调节",
    "book3-ch4": "免疫调节",
    "book3-ch5": "植物生命活动的调节",
    "book4-ch1": "种群及其动态",
    "book4-ch2": "群落及其演替",
    "book4-ch3": "生态系统及其稳定性",
    "book4-ch4": "人与环境",
    "book5-ch1": "发酵工程",
    "book5-ch2": "细胞工程",
    "book5-ch3": "基因工程",
    "book5-ch4": "生物技术的安全性与伦理问题",
}


class _TextExtractor(HTMLParser):
    """HTML parser that extracts clean text, skipping script/style tags."""

    def __init__(self):
        super().__init__()
        self.text_parts: list[str] = []
        self.skip = False
        self._skip_tag = ""

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip = True
            self._skip_tag = tag

    def handle_endtag(self, tag):
        if tag == self._skip_tag:
            self.skip = False
            self._skip_tag = ""
        # Insert newlines after block-level elements for readability
        if tag in ("p", "div", "li", "tr", "h1", "h2", "h3", "h4", "br", "section", "article"):
            self.text_parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            text = data.strip()
            if text:
                self.text_parts.append(text + " ")


def _clean_navigation_noise(text: str) -> str:
    """Remove navigation/UI text that leaks from the knowledge HTML template."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append(line)
            continue
        # Skip lines listing multiple chapters (navigation bar)
        chapter_count = len(re.findall(r"第[一二三四五六\d]+章", stripped))
        if chapter_count >= 2:
            continue
        # Skip lines listing multiple textbooks (textbook switcher bar)
        textbook_count = len(re.findall(r"(必修|选必)[一二三\d]", stripped))
        if textbook_count >= 2:
            continue
        # Skip UI navigation elements
        if re.match(r"^(切换课本|返回首页|生物学|必修[一二三\d]\s*$|选必[一二三\d]\s*$)$", stripped):
            continue
        # Remove breadcrumb trail fragments from within a line
        stripped = re.sub(r"←\s*返回首页\s*", "", stripped)
        stripped = re.sub(r"\s*生物学\s+必修[一二三\d]\s+分子与细胞\s*$", "", stripped)
        stripped = stripped.strip()
        if not stripped:
            continue
        cleaned.append(stripped)
    return "\n".join(cleaned)


def extract_text_from_html(html_content: str) -> str:
    parser = _TextExtractor()
    parser.feed(html_content)
    raw = "".join(parser.text_parts)
    # Collapse multiple newlines and spaces
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    raw = re.sub(r"[ \t]{2,}", " ", raw)
    raw = re.sub(r" {2,}", " ", raw)
    raw = raw.strip()
    # Remove navigation bar noise
    raw = _clean_navigation_noise(raw)
    # Truncate per file
    max_len = 8000
    if len(raw) > max_len:
        raw = raw[:max_len] + "\n...(内容已截断)"
    return raw


def get_knowledge_content(chapter_keys: list[str]) -> dict[str, str]:
    result = {}
    for key in chapter_keys:
        try:
            file_path = _chapter_key_to_path(key)
            if file_path.exists():
                html_content = file_path.read_text(encoding="utf-8")
                text_content = extract_text_from_html(html_content)
                chapter_name = CHAPTER_NAMES.get(key, key)
                book_key = key.split("-")[0]
                book_name = BOOK_NAMES.get(book_key, book_key)
                result[key] = f"[{book_name} - {chapter_name}]\n{text_content}"
            else:
                result[key] = f"[{CHAPTER_NAMES.get(key, key)}] 知识点文件未找到：{file_path}"
        except Exception as e:
            result[key] = f"[{CHAPTER_NAMES.get(key, key)}] 读取失败：{e}"
    return result


def build_knowledge_context(chapter_keys: list[str]) -> str:
    contents = get_knowledge_content(chapter_keys)
    if not contents:
        return ""
    parts = []
    for key, text_content in contents.items():
        parts.append(f"【{CHAPTER_NAMES.get(key, key)}】\n{text_content}")
    return "\n\n---\n\n".join(parts)
