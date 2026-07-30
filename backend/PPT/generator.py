from __future__ import annotations

import copy
import shutil
import json
import re
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = PROJECT_DIR / "templates" / "deck_template.html"
OUTPUT_DIR = PROJECT_DIR / "outputs"
ASSET_DIR = PROJECT_DIR / "assets"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


class DeckError(ValueError):
    pass


def text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def html(value: Any, default: str = "") -> str:
    return escape(text(value, default), quote=True)


def attr(value: Any, default: str = "") -> str:
    return escape(text(value, default), quote=True)


def class_token(value: Any, default: str = "") -> str:
    raw = text(value, default)
    return re.sub(r"[^a-zA-Z0-9_-]", "", raw)


def is_remote_or_data_uri(src: str) -> bool:
    src = src.lower()
    return src.startswith(("http://", "https://", "data:", "blob:"))


def asset_url(filename: str) -> str:
    return f"../assets/{filename}"


def render_rich_text(value: Any) -> str:
    safe = html(value)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"`(.+?)`", r"<strong>\1</strong>", safe)
    return safe


def normalize_items(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            normalized.append(item)
        else:
            normalized.append({"text": str(item)})
    return normalized


def grid_class(count: int, preferred: Any = None) -> str:
    explicit = class_token(preferred)
    if explicit in {"cols-2", "cols-3", "cols-4", "cols-5"}:
        return explicit
    if count <= 2:
        return "cols-2"
    if count == 3:
        return "cols-3"
    if count == 4:
        return "cols-4"
    return "cols-5"


def render_header(slide: dict[str, Any], eyebrow_default: str = "教学课件") -> str:
    eyebrow = text(slide.get("eyebrow"), eyebrow_default)
    title = text(slide.get("title"), "未命名页面")
    lead = text(slide.get("lead") or slide.get("subtitle"))
    parts = [
        "<div>",
        f'  <div class="eyebrow fragment">{html(eyebrow)}</div>',
        f'  <h2 class="h2 fragment">{render_rich_text(title)}</h2>',
    ]
    if lead:
        parts.append(f'  <p class="lead fragment">{render_rich_text(lead)}</p>')
    parts.append("</div>")
    return "\n".join(parts)


def render_cover(slide: dict[str, Any]) -> str:
    tags = normalize_items(slide.get("tags"))
    tag_html = "\n".join(
        f'            <span class="pill {class_token(tag.get("tone"), "")}">{html(tag.get("text") or tag.get("title"))}</span>'
        for tag in tags
    )
    if tag_html:
        tag_html = f'\n          <div class="pill-list fragment">\n{tag_html}\n          </div>'
    return f"""<section class="slide current" data-title="{attr(slide.get("title"), "封面")}">
      <div class="stage center">
        <div>
          <div class="eyebrow fragment">{html(slide.get("eyebrow"), "高中生物")}</div>
          <h1 class="title fragment"><span class="grad">{render_rich_text(slide.get("title"))}</span></h1>
          <p class="subtitle fragment">{render_rich_text(slide.get("subtitle") or slide.get("lead"))}</p>{tag_html}
        </div>
      </div>
    </section>"""


def render_cards(slide: dict[str, Any]) -> str:
    cards = normalize_items(slide.get("cards") or slide.get("items"))
    card_html = []
    for card in cards:
        title = html(card.get("title"), "要点")
        body = render_rich_text(card.get("text") or card.get("body"))
        tone = class_token(card.get("tone"), "")
        card_html.append(
            f"""          <div class="glass card fragment {tone}">
            <h3>{title}</h3>
            <p>{body}</p>
          </div>"""
        )
    return f"""<section class="slide" data-title="{attr(slide.get("title"))}">
      <div class="stage">
        {render_header(slide)}
        <div class="grid {grid_class(len(cards), slide.get("columns"))}">
{chr(10).join(card_html)}
        </div>
      </div>
    </section>"""


def render_metrics(slide: dict[str, Any]) -> str:
    items = normalize_items(slide.get("metrics") or slide.get("items"))
    metric_html = []
    for item in items:
        metric_html.append(
            f"""          <div class="metric fragment">
            <div class="num">{html(item.get("label") or item.get("num") or item.get("title"), "指标")}</div>
            <div class="label"><strong>{html(item.get("title"), "说明")}</strong><br>{render_rich_text(item.get("text") or item.get("body"))}</div>
          </div>"""
        )
    return f"""<section class="slide" data-title="{attr(slide.get("title"))}">
      <div class="stage">
        <div class="between">
          {render_header(slide)}
          <div class="tag {class_token(slide.get("tag_tone"), "cyan")} fragment">{html(slide.get("tag"), "关键判断")}</div>
        </div>
        <div class="grid {grid_class(len(items), slide.get("columns"))}">
{chr(10).join(metric_html)}
        </div>
      </div>
    </section>"""


def render_compare(slide: dict[str, Any]) -> str:
    items = normalize_items(slide.get("columns") or slide.get("items"))[:2]
    while len(items) < 2:
        items.append({"title": "对比项", "points": []})
    blocks = []
    for item in items:
        points = item.get("points") or item.get("list") or []
        if isinstance(points, str):
            points = [points]
        list_html = "\n".join(f"              <li>{render_rich_text(point)}</li>" for point in points)
        blocks.append(
            f"""          <div class="glass card fragment">
            <h3>{html(item.get("title"), "对比项")}</h3>
            <ul>
{list_html}
            </ul>
          </div>"""
        )
    return f"""<section class="slide" data-title="{attr(slide.get("title"))}">
      <div class="stage">
        {render_header(slide, "Compare")}
        <div class="grid cols-2">
{chr(10).join(blocks)}
        </div>
      </div>
    </section>"""


def render_process(slide: dict[str, Any]) -> str:
    steps = normalize_items(slide.get("steps") or slide.get("items"))
    step_html = []
    for index, step in enumerate(steps, start=1):
        step_html.append(
            f"""          <div class="step fragment">
            <b>{index:02d}</b>
            <h3>{html(step.get("title"), "步骤")}</h3>
            <p>{render_rich_text(step.get("text") or step.get("body"))}</p>
          </div>"""
        )
    return f"""<section class="slide" data-title="{attr(slide.get("title"))}">
      <div class="stage">
        {render_header(slide, "Process")}
        <div class="timeline">
{chr(10).join(step_html)}
        </div>
      </div>
    </section>"""


def render_image_text(slide: dict[str, Any]) -> str:
    image = slide.get("image") or {}
    if isinstance(image, str):
        image = {"src": image}
    points = slide.get("points") or slide.get("items") or []
    if isinstance(points, str):
        points = [points]
    point_html = "\n".join(f"              <li><span>{render_rich_text(point)}</span></li>" for point in points)
    reverse = " reverse" if slide.get("reverse") else ""
    return f"""<section class="slide" data-title="{attr(slide.get("title"))}">
      <div class="stage">
        <div class="split{reverse}">
          <div>
            {render_header(slide, "Image")}
            <ul class="list-clean fragment">
{point_html}
            </ul>
          </div>
          <div class="mock-browser fragment">
            <div class="mock-bar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="tag cyan">{html(image.get("caption"), "课程素材")}</span></div>
            <img src="{attr(image.get("src"))}" alt="{attr(image.get("alt") or image.get("caption") or slide.get("title"))}">
          </div>
        </div>
      </div>
    </section>"""


def render_code(slide: dict[str, Any]) -> str:
    code = html(slide.get("code"))
    lang = html(slide.get("language"), "code")
    notes = slide.get("notes") or slide.get("points") or []
    if isinstance(notes, str):
        notes = [notes]
    note_html = "\n".join(f"              <li><span>{render_rich_text(note)}</span></li>" for note in notes)
    return f"""<section class="slide" data-title="{attr(slide.get("title"))}">
      <div class="stage">
        {render_header(slide, "Code")}
        <div class="grid cols-2">
          <pre class="glass card fragment" style="white-space:pre-wrap"><code>{code}</code></pre>
          <div class="glass card fragment">
            <h3>{lang}</h3>
            <ul class="list-clean">
{note_html}
            </ul>
          </div>
        </div>
      </div>
    </section>"""


def render_section(slide: dict[str, Any]) -> str:
    return f"""<section class="slide" data-title="{attr(slide.get("title"))}">
      <div class="stage center">
        <div>
          <div class="eyebrow fragment">{html(slide.get("eyebrow"), "Section")}</div>
          <h1 class="title fragment"><span class="grad">{render_rich_text(slide.get("title"))}</span></h1>
          <p class="subtitle fragment">{render_rich_text(slide.get("subtitle") or slide.get("lead"))}</p>
        </div>
      </div>
    </section>"""


def render_summary(slide: dict[str, Any]) -> str:
    items = normalize_items(slide.get("items") or slide.get("cards"))
    pills = "\n".join(
        f'            <span class="pill {class_token(item.get("tone"), "")}">{html(item.get("title") or item.get("text"))}</span>'
        for item in items
    )
    return f"""<section class="slide" data-title="{attr(slide.get("title"), "总结")}">
      <div class="stage center">
        <div>
          <div class="eyebrow fragment">{html(slide.get("eyebrow"), "Summary")}</div>
          <h1 class="title fragment"><span class="grad">{render_rich_text(slide.get("title"))}</span></h1>
          <p class="subtitle fragment">{render_rich_text(slide.get("subtitle") or slide.get("lead"))}</p>
          <div class="pill-list fragment">
{pills}
          </div>
        </div>
      </div>
    </section>"""


RENDERERS = {
    "cover": render_cover,
    "cards": render_cards,
    "metrics": render_metrics,
    "compare": render_compare,
    "process": render_process,
    "image_text": render_image_text,
    "code": render_code,
    "section": render_section,
    "summary": render_summary,
}


def validate_deck(deck: dict[str, Any]) -> None:
    if not isinstance(deck, dict):
        raise DeckError("课件数据必须是 JSON 对象。")
    slides = deck.get("slides")
    if not isinstance(slides, list) or not slides:
        raise DeckError("课件数据必须包含非空 slides 数组。")
    for index, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            raise DeckError(f"第 {index} 页必须是对象。")
        if not text(slide.get("title")):
            raise DeckError(f"第 {index} 页缺少 title。")
        slide_type = text(slide.get("type"), "cards")
        if slide_type not in RENDERERS:
            raise DeckError(f"第 {index} 页 type={slide_type} 暂不支持。可用的类型：{', '.join(RENDERERS.keys())}")


def render_slides(deck: dict[str, Any]) -> str:
    validate_deck(deck)
    rendered: list[str] = []
    for index, slide in enumerate(deck["slides"]):
        slide = dict(slide)
        if index == 0 and text(slide.get("type"), "cover") != "cover":
            slide.setdefault("type", "cover")
        rendered.append(RENDERERS[text(slide.get("type"), "cards")](slide))
    return "\n\n".join(rendered)


def build_theme_css(theme: str = "light", style: str = "clean", hue: int = 215) -> str:
    """Generate CSS overrides based on theme (light/dark), style (clean/edu/tech), and hue."""
    h = hue % 360
    if theme == "light":
        css = f"""<style>
      :root {{
        --bg0: #f0f4f8;
        --bg1: #e2e8f0;
        --bg2: #cbd5e1;
        --ink: #1a202c;
        --muted: #4a5568;
        --subtle: #718096;
        --line: rgba(0,0,0,0.12);
        --glass: rgba(255,255,255,0.7);
        --glass2: rgba(255,255,255,0.4);
        --glass-a: 0.7;
        --glass-b: 0.4;
        --glass-blur: 20px;
        --shadow: 0 18px 50px rgba(0,0,0,0.08);
        --cyan: hsl({h}, 62%, 44%);
        --violet: hsl({(h + 40) % 360}, 55%, 35%);
        --green: hsl({(h + 80) % 360}, 55%, 50%);
        --amber: hsl({h}, 62%, 44%);
        --orange: hsl({(h + 80) % 360}, 55%, 50%);
      }}
      body {{
        background: linear-gradient(135deg, #f0f4f8 0%, #e8eef5 40%, #f5f7fa 100%) !important;
        color: #1a202c;
      }}
      body::before, body::after {{ opacity: 0.15 !important; }}
      .topline {{ color: hsl({h}, 30%, 30%) !important; }}
    </style>"""
    else:
        css = f"""<style>
      :root {{
        --cyan: hsl({h}, 62%, 44%);
        --violet: hsl({(h + 40) % 360}, 55%, 35%);
        --green: hsl({(h + 80) % 360}, 55%, 50%);
        --amber: hsl({h}, 62%, 44%);
        --orange: hsl({(h + 80) % 360}, 55%, 50%);
      }}
    </style>"""

    if style == "clean":
        css += """<style>
      :root { --radius: 22px; }
      .slide { font-family: "PingFang SC", "Microsoft YaHei", sans-serif; }
    </style>"""
    elif style == "edu":
        css += """<style>
      :root { --radius: 30px; }
      .h2, h2 { font-weight: 900; }
    </style>"""

    return css


def render_deck(deck: dict[str, Any], template_path: Path | None = None,
                theme: str = "light", style: str = "clean", hue: int = 215) -> str:
    slides_html = render_slides(deck)
    template = (template_path or TEMPLATE_PATH).read_text(encoding="utf-8")
    title = text(deck.get("title"), deck["slides"][0]["title"])
    description = text(deck.get("description"), f"{title} 的 PPT 式可滚动播放网页。")
    topline = text(deck.get("topline"), title)
    return (
        template.replace("{{DOCUMENT_TITLE}}", html(title))
        .replace("{{DOCUMENT_DESCRIPTION}}", html(description))
        .replace("{{TOPLINE_TEXT}}", html(topline))
        .replace("{{SLIDES_HTML}}", slides_html)
        .replace("{{THEME_CSS}}", build_theme_css(theme, style, hue))
    )


def slugify(value: str) -> str:
    value = re.sub(r"\s+", "-", value.strip().lower())
    kept = []
    for char in value:
        if char == "-" or char == "_" or char.isalnum() or "一" <= char <= "鿿":
            kept.append(char)
    return "".join(kept).strip("-") or "deck"


def write_deck(deck: dict[str, Any], output: Path | None = None,
               theme: str = "light", style: str = "clean", hue: int = 215) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if output is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = OUTPUT_DIR / f"{slugify(text(deck.get('title'), 'deck'))}-{stamp}.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_deck(deck, theme=theme, style=style, hue=hue), encoding="utf-8")
    return output
