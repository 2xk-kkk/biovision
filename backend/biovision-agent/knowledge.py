"""平台知识库的公共词表、中文分词与教材结构映射。

本模块只负责「文本 → 关键词」和「关键词 → 教材章节」这类基础能力，
真正的索引与检索在 platform.py。
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

from . import config

# ---------------------------------------------------------------- 词表

STOPWORDS = set(
    """的 了 是 在 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有 看 好 自己 这
    什么 怎么 为什么 哪些 哪个 如何 可以 能否 请 帮我 讲讲 解释 一下 关于 以及 还有 但是 因为
    所以 如果 那么 这个 那个 这些 那些 它们 他 她 它 我们 你们 他们 吗 呢 吧 啊 呀 嗯 哦 哎
    意思 区别 关系 作用 过程 内容 知识点 考点 讲解 分析 说明 介绍 题目 问题 老师 同学 请问
    高中 生物 教材 课本 章节 哪一 哪个 怎么 是否 一下 哪些 谁知 知道 觉得 应该 可能 一般
    就是 不是 有没有 什么样 什么样 多少 几个 什么 时候 地方 东西 事情""".split()
)

# 生物学科常见术语：中文分词容易切碎，作为整体保留，同时用于章节路由
BIO_TERMS = {
    # 必修一
    "细胞学说": "book1-ch1", "显微镜": "book1-ch1", "原核细胞": "book1-ch1",
    "真核细胞": "book1-ch1", "蓝细菌": "book1-ch1", "细胞多样性": "book1-ch1",
    "氨基酸": "book1-ch2", "蛋白质": "book1-ch2", "核酸": "book1-ch2", "糖类": "book1-ch2",
    "脂质": "book1-ch2", "无机盐": "book1-ch2", "生物大分子": "book1-ch2",
    "脱水缩合": "book1-ch2", "肽键": "book1-ch2", "核苷酸": "book1-ch2",
    "细胞膜": "book1-ch3", "细胞器": "book1-ch3", "线粒体": "book1-ch3", "叶绿体": "book1-ch3",
    "核糖体": "book1-ch3", "高尔基体": "book1-ch3", "内质网": "book1-ch3", "细胞核": "book1-ch3",
    "细胞壁": "book1-ch3", "溶酶体": "book1-ch3", "液泡": "book1-ch3", "中心体": "book1-ch3",
    "细胞骨架": "book1-ch3", "流动镶嵌模型": "book1-ch3",
    "被动运输": "book1-ch4", "主动运输": "book1-ch4", "自由扩散": "book1-ch4",
    "协助扩散": "book1-ch4", "质壁分离": "book1-ch4", "渗透作用": "book1-ch4",
    "胞吞": "book1-ch4", "胞吐": "book1-ch4", "半透膜": "book1-ch4",
    "酶": "book1-ch5", "ATP": "book1-ch5", "细胞呼吸": "book1-ch5", "有氧呼吸": "book1-ch5",
    "无氧呼吸": "book1-ch5", "光合作用": "book1-ch5", "光反应": "book1-ch5",
    "暗反应": "book1-ch5", "卡尔文循环": "book1-ch5", "色素": "book1-ch5",
    "呼吸作用": "book1-ch5", "化能合成": "book1-ch5", "活化能": "book1-ch5",
    "有丝分裂": "book1-ch6", "细胞分化": "book1-ch6", "细胞凋亡": "book1-ch6",
    "细胞衰老": "book1-ch6", "细胞癌变": "book1-ch6", "细胞周期": "book1-ch6",
    "细胞全能性": "book1-ch6", "干细胞": "book1-ch6",
    # 必修二
    "孟德尔": "book2-ch1", "分离定律": "book2-ch1", "自由组合定律": "book2-ch1",
    "测交": "book2-ch1", "自交": "book2-ch1", "性状分离": "book2-ch1", "豌豆": "book2-ch1",
    "显性": "book2-ch1", "隐性": "book2-ch1", "基因型": "book2-ch1", "表现型": "book2-ch1",
    "减数分裂": "book2-ch2", "染色体": "book2-ch2", "伴性遗传": "book2-ch2",
    "性别决定": "book2-ch2", "联会": "book2-ch2", "同源染色体": "book2-ch2",
    "四分体": "book2-ch2", "受精作用": "book2-ch2", "交叉互换": "book2-ch2",
    "基因": "book2-ch3", "DNA": "book2-ch3", "复制": "book2-ch3", "半保留复制": "book2-ch3",
    "碱基互补配对": "book2-ch3", "双螺旋": "book2-ch3", "噬菌体": "book2-ch3",
    "转录": "book2-ch4", "翻译": "book2-ch4", "密码子": "book2-ch4", "中心法则": "book2-ch4",
    "信使RNA": "book2-ch4", "tRNA": "book2-ch4", "基因表达": "book2-ch4", "反密码子": "book2-ch4",
    "基因突变": "book2-ch5", "基因重组": "book2-ch5", "染色体变异": "book2-ch5",
    "单倍体": "book2-ch5", "多倍体": "book2-ch5", "诱变育种": "book2-ch5",
    "基因频率": "book2-ch6", "自然选择": "book2-ch6", "现代生物进化理论": "book2-ch6",
    "隔离": "book2-ch6", "共同进化": "book2-ch6", "物种形成": "book2-ch6", "种群基因频率": "book2-ch6",
    # 选择性必修一
    "内环境": "book3-ch1", "稳态": "book3-ch1", "血浆": "book3-ch1", "组织液": "book3-ch1",
    "淋巴": "book3-ch1", "渗透压": "book3-ch1", "酸碱平衡": "book3-ch1", "血浆pH": "book3-ch1",
    "神经调节": "book3-ch2", "反射": "book3-ch2", "反射弧": "book3-ch2", "突触": "book3-ch2",
    "静息电位": "book3-ch2", "动作电位": "book3-ch2", "神经递质": "book3-ch2",
    "兴奋传导": "book3-ch2", "大脑皮层": "book3-ch2", "条件反射": "book3-ch2",
    "体液调节": "book3-ch3", "激素": "book3-ch3", "胰岛素": "book3-ch3",
    "甲状腺激素": "book3-ch3", "血糖": "book3-ch3", "体温调节": "book3-ch3",
    "水盐平衡": "book3-ch3", "反馈调节": "book3-ch3", "胰高血糖素": "book3-ch3",
    "免疫": "book3-ch4", "体液免疫": "book3-ch4", "细胞免疫": "book3-ch4", "抗体": "book3-ch4",
    "抗原": "book3-ch4", "淋巴细胞": "book3-ch4", "T细胞": "book3-ch4", "B细胞": "book3-ch4",
    "疫苗": "book3-ch4", "过敏": "book3-ch4", "免疫调节": "book3-ch4", "免疫缺陷": "book3-ch4",
    "生长素": "book3-ch5", "植物激素": "book3-ch5", "向光性": "book3-ch5",
    "赤霉素": "book3-ch5", "细胞分裂素": "book3-ch5", "脱落酸": "book3-ch5", "乙烯": "book3-ch5",
    # 选择性必修二
    "种群": "book4-ch1", "种群密度": "book4-ch1", "标志重捕法": "book4-ch1", "样方法": "book4-ch1",
    "出生率": "book4-ch1", "环境容纳量": "book4-ch1", "年龄结构": "book4-ch1",
    "群落": "book4-ch2", "群落演替": "book4-ch2", "物种丰富度": "book4-ch2",
    "种间关系": "book4-ch2", "竞争": "book4-ch2", "捕食": "book4-ch2",
    "互利共生": "book4-ch2", "寄生": "book4-ch2", "初生演替": "book4-ch2",
    "生态系统": "book4-ch3", "食物链": "book4-ch3", "食物网": "book4-ch3",
    "能量流动": "book4-ch3", "物质循环": "book4-ch3", "信息传递": "book4-ch3",
    "碳循环": "book4-ch3", "抵抗力稳定性": "book4-ch3", "营养结构": "book4-ch3",
    "生物多样性": "book4-ch4", "生态环境": "book4-ch4", "酸雨": "book4-ch4",
    "温室效应": "book4-ch4", "可持续发展": "book4-ch4",
    # 选择性必修三
    "发酵": "book5-ch1", "发酵工程": "book5-ch1", "微生物培养": "book5-ch1",
    "培养基": "book5-ch1", "灭菌": "book5-ch1", "菌种": "book5-ch1", "传统发酵": "book5-ch1",
    "细胞工程": "book5-ch2", "植物组织培养": "book5-ch2", "动物细胞培养": "book5-ch2",
    "克隆": "book5-ch2", "单克隆抗体": "book5-ch2", "细胞融合": "book5-ch2", "核移植": "book5-ch2",
    "基因工程": "book5-ch3", "限制酶": "book5-ch3", "DNA连接酶": "book5-ch3",
    "质粒": "book5-ch3", "载体": "book5-ch3", "PCR": "book5-ch3",
    "基因表达载体": "book5-ch3", "转基因": "book5-ch3", "电泳": "book5-ch3",
    "生物技术安全": "book5-ch4", "伦理": "book5-ch4", "转基因生物": "book5-ch4",
}

CHAPTER_NAME_TO_KEY = {
    "走近细胞": "book1-ch1",
    "组成细胞的分子": "book1-ch2",
    "细胞的基本结构": "book1-ch3",
    "细胞的物质输入和输出": "book1-ch4",
    "细胞的能量供应和利用": "book1-ch5",
    "细胞的生命历程": "book1-ch6",
    "遗传因子的发现": "book2-ch1",
    "基因和染色体的关系": "book2-ch2",
    "基因的本质": "book2-ch3",
    "基因的表达": "book2-ch4",
    "基因突变及其他变异": "book2-ch5",
    "生物的进化": "book2-ch6",
    "人体的内环境与稳态": "book3-ch1",
    "神经调节": "book3-ch2",
    "体液调节": "book3-ch3",
    "免疫调节": "book3-ch4",
    "植物生命活动的调节": "book3-ch5",
    "种群及其动态": "book4-ch1",
    "群落及其演替": "book4-ch2",
    "生态系统及其稳定性": "book4-ch3",
    "人与环境": "book4-ch4",
    "发酵工程": "book5-ch1",
    "细胞工程": "book5-ch2",
    "基因工程": "book5-ch3",
    "生物技术的安全性与伦理问题": "book5-ch4",
}

BOOK_LABELS = {
    "book1": "必修一：分子与细胞",
    "book2": "必修二：遗传与进化",
    "book3": "选择性必修一：稳态与调节",
    "book4": "选择性必修二：生物与环境",
    "book5": "选择性必修三：生物技术与工程",
}

# 用户可能写"必修1""选必二"等，统一成几种写法后再匹配
BOOK_ALIASES = {
    "book1": ("必修一", "必修1", "必修①", "分子与细胞"),
    "book2": ("必修二", "必修2", "必修②", "遗传与进化"),
    "book3": ("选择性必修一", "选择性必修1", "选必一", "选必1", "稳态与调节"),
    "book4": ("选择性必修二", "选择性必修2", "选必二", "选必2", "生物与环境"),
    "book5": ("选择性必修三", "选择性必修3", "选必三", "选必3", "生物技术与工程"),
}

# 章节在原教材里的顺序，用于把检索结果按教材顺序排列
CHAPTER_ORDER = {key: i for i, key in enumerate(CHAPTER_NAME_TO_KEY.values())}

CHAPTER_KEY_TO_NAME = {v: k for k, v in CHAPTER_NAME_TO_KEY.items()}

KNOWLEDGE_DIR = config.PROJECT_DIR / "frontend" / "knowledge"
TEACHING_BOOK_DIR = config.PROJECT_DIR / "frontend" / "textbooks"
MODEL3D_DIR = config.PROJECT_DIR / "frontend" / "3D model"

TEACHING_BOOKS = {
    "book1": "普通高中教科书-生物学必修1-分子与细胞.pdf",
    "book2": "普通高中教科书-生物学必修2-遗传与进化.pdf",
    "book3": "普通高中教科书-生物学选择性必修1-稳态与调节.pdf",
    "book4": "普通高中教科书-生物学选择性必修2-生物与环境.pdf",
    "book5": "普通高中教科书-生物学选择性必修3-生物技术与工程.pdf",
}


# ---------------------------------------------------------------- 分词

# 用一条正则一次性扫出所有学科术语，比对 400 个词逐个 `in` 快两个数量级
_BIO_RE = re.compile(
    "|".join(re.escape(t) for t in sorted(BIO_TERMS, key=len, reverse=True)),
    re.IGNORECASE,
)
_BIO_LOWER = {k.lower(): v for k, v in BIO_TERMS.items()}

_JIEBA = None
_JIEBA_TRIED = False


def _jieba():
    global _JIEBA, _JIEBA_TRIED
    if not _JIEBA_TRIED:
        _JIEBA_TRIED = True
        try:
            import jieba

            jieba.setLogLevel(60)
            _JIEBA = jieba
        except Exception:
            _JIEBA = None
    return _JIEBA


def tokenize(text: str) -> list[str]:
    """把一段文本切成用于检索的关键词，去重并丢掉停用词。

    注意：术语大小写会被统一成小写形式（ATP/atp 都算 atp），避免同一概念被拆开。
    """
    text = text or ""
    tokens: list[str] = []

    tokens.extend(_BIO_RE.findall(text))

    jb = _jieba()
    if jb is not None:
        tokens.extend(jb.cut_for_search(text))
    else:
        # 没有 jieba 时退化成中文 2-gram
        for run in re.findall(r"[一-鿿]+", text):
            tokens.extend(run[i : i + 2] for i in range(len(run) - 1))

    tokens.extend(re.findall(r"[A-Za-z][A-Za-z0-9\-]{1,}", text))

    seen, out = set(), []
    for t in tokens:
        t = (t or "").strip()
        if len(t) < 2 or t.isdigit():
            continue
        low = t.lower()
        if low in STOPWORDS or low in seen:
            continue
        seen.add(low)
        out.append(low)
    return out


def chapter_of_term(term: str) -> str:
    return _BIO_LOWER.get(term.lower(), "")


def is_bio_term(term: str) -> bool:
    """是不是一个学科术语（这类词命中一个就足够说明相关）。"""
    return term.lower() in _BIO_LOWER


def route_chapters(text: str, tokens: list[str] | None = None) -> list[str]:
    """判断问题涉及哪些教材章节，按相关度排序。"""
    tokens = tokens if tokens is not None else tokenize(text)
    score: dict[str, int] = {}

    for t in tokens:
        key = chapter_of_term(t)
        if key:
            score[key] = score.get(key, 0) + 3

    for name, key in CHAPTER_NAME_TO_KEY.items():
        if name in (text or ""):
            score[key] = score.get(key, 0) + 6

    compact = re.sub(r"\s+", "", text or "")
    for book_key, aliases in BOOK_ALIASES.items():
        if any(alias in compact for alias in aliases):
            for key in CHAPTER_NAME_TO_KEY.values():
                if key.startswith(book_key):
                    score[key] = score.get(key, 0) + 1

    return [k for k, _ in sorted(score.items(), key=lambda kv: (-kv[1], CHAPTER_ORDER.get(kv[0], 99)))]


# ---------------------------------------------------------------- HTML → 文本

_SKIP_TAGS = {"script", "style", "noscript", "svg"}
_BLOCK_TAGS = {
    "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6",
    "section", "article", "header", "footer", "blockquote", "pre", "br", "table",
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth:
            return
        text = data.strip()
        if text:
            self.parts.append(text + " ")


def html_to_text(html: str) -> str:
    """抽出 HTML 正文，去掉导航栏之类的模板噪声。"""
    parser = _TextExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    text = "".join(parser.parts)

    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t　]+", " ", line).strip()
        if not line:
            continue
        # 丢导航条：一行里出现两个以上章节名 / 两册以上课本名
        if len(re.findall(r"第[一二三四五六\d]+章", line)) >= 2:
            continue
        if len(re.findall(r"(必修|选必)", line)) >= 2:
            continue
        if re.fullmatch(r"(切换课本|返回首页|上一节|下一节|目录|生物学)", line):
            continue
        lines.append(line)

    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def split_chunks(text: str, size: int = 700, overlap: int = 80) -> list[str]:
    """按段落边界把长文本切成带少量重叠的块，避免检索时被长文档稀释。"""
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    paragraphs = [p.strip() for p in re.split(r"\n{2,}|\n", text) if p.strip()]
    chunks, buf = [], ""
    for para in paragraphs:
        if len(buf) + len(para) + 1 <= size:
            buf = f"{buf}\n{para}" if buf else para
            continue
        if buf:
            chunks.append(buf)
        if len(para) <= size:
            buf = para
        else:
            # 单段就超长：硬切
            step = max(1, size - overlap)
            for i in range(0, len(para), step):
                chunks.append(para[i : i + size])
            buf = ""
    if buf:
        chunks.append(buf)
    return chunks


# ---------------------------------------------------------------- 教材文件

def chapter_html_path(chapter_key: str) -> Path | None:
    parts = chapter_key.split("-")
    if len(parts) != 2:
        return None
    book, num = parts[0], parts[1].replace("ch", "")
    path = KNOWLEDGE_DIR / book / f"{book[-1]}.{num}.html"
    return path if path.exists() else None


def chapter_link(chapter_key: str) -> str:
    parts = chapter_key.split("-")
    if len(parts) != 2:
        return ""
    book, num = parts[0], parts[1].replace("ch", "")
    return f"/knowledge/{book}/{book[-1]}.{num}.html"
