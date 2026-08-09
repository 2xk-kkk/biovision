"""
知识点解析器 — 从 knowledge HTML 文件中提取结构化知识点。

解析 frontend/knowledge/bookN/N.M.html 文件，
提取所有 ul.checklist li 项作为知识点记录，
生成用于题目匹配的关键词列表。
"""

from html.parser import HTMLParser
from pathlib import Path
import re
import os

# 复用 PPT 模块的映射表
BASE_DIR = Path(__file__).resolve().parent.parent
import sys
_ppt_dir = BASE_DIR / 'PPT'
if str(_ppt_dir) not in sys.path:
    sys.path.insert(0, str(_ppt_dir))

from knowledge_reader import BOOK_NAMES, CHAPTER_NAMES

KNOWLEDGE_DIR = BASE_DIR.parent / 'frontend' / 'knowledge'

# 标签 CSS 类 → 分类名映射
TAG_CATEGORY_MAP = {
    'tag-important': '重点',
    'tag-understand': '理解',
    'tag-memorize': '记忆',
    'tag-super': '必考',
    'tag-concept': '概念',
}

# 中文停用词（虚词/功能词，不构成知识点关键词）
STOP_WORDS = {
    '的', '了', '是', '在', '和', '与', '或', '等', '不', '也', '都',
    '就', '要', '对', '从', '到', '被', '把', '由', '但', '而', '且',
    '所', '以', '为', '及', '可', '能', '会', '这', '那', '其', '有',
    '中', '上', '下', '前', '后', '左', '右', '内', '外', '大', '小',
    '个', '每', '各', '某', '哪', '什么', '怎么', '如何', '着', '过',
    '地', '得', '之', '已', '将', '更', '最', '很', '共', '则', '此',
    '该', '它', '她', '他', '们', '你', '我',
}

# 标点符号
PUNCTUATION = set('，。！？、；：""''（）【】《》…—·,.;:!?\"\'()[]{}<>/@#$%^&*+=_\n\r\t ')


class _KnowledgeExtractor(HTMLParser):
    """解析知识 HTML，提取结构化知识点列表。"""

    def __init__(self):
        super().__init__()
        self.in_label = False
        self.in_tag_span = False
        self.in_strong = False
        self.in_section_header = False
        self.in_checklist = 0  # 嵌套层级计数器

        # 当前解析状态
        self.current_section = ''
        self.current_section_name = ''
        self.current_items = []  # 当前节下的清单项
        self._data_id_counter = 1  # 无 data-id 时自动编号

        # 单个清单项的状态
        self.current_label_parts = []  # label 的纯文本片段
        self.current_strong_terms = []  # <strong> 内的粗体词
        self.current_tag_classes = []  # tag span 的 class
        self.current_data_id = None
        self._in_li = False  # 是否在 checklist li 内

        # 结果
        self.sections = []  # [(section_title, section_name, items)]

        # 章节标题
        self.chapter_title = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag in ('script', 'style'):
            return

        # 检测进入 checklist
        cls = attrs.get('class', '')
        if tag == 'ul' and 'checklist' in cls:
            self.in_checklist += 1

        # 检测 section 开始
        if 'section-header' in cls:
            self.in_section_header = True
            # 发现新 section，先保存旧 section 的 items
            self._flush_section()
            self.current_section = ''
            self.current_section_name = ''

        if self.in_section_header and tag == 'h2':
            self.current_section = ''

        # 检测 checklist 中的 li（支持 data-id 和普通 li）
        if self.in_checklist > 0 and tag == 'li':
            self._in_li = True
            self.current_label_parts = []
            self.current_strong_terms = []
            self.current_tag_classes = []
            if 'data-id' in attrs:
                self.current_data_id = int(attrs['data-id'])
            else:
                self.current_data_id = self._data_id_counter
                self._data_id_counter += 1

        # 进入 label span
        if 'label' in cls:
            self.in_label = True

        # 进入 tag span
        if 'tag' in cls and ('tag-important' in cls or
                              'tag-understand' in cls or
                              'tag-memorize' in cls or
                              'tag-super' in cls or
                              'tag-concept' in cls):
            self.in_tag_span = True
            self.current_tag_classes = [c for c in cls.split() if c.startswith('tag-')]

        if self.in_label and tag == 'strong':
            self.in_strong = True

    def handle_endtag(self, tag):
        if tag == 'ul' and self.in_checklist > 0:
            self.in_checklist -= 1

        if self.in_section_header and tag == 'h2':
            self.in_section_header = False

        if self.in_label and tag == 'span':
            self.in_label = False

        if self.in_tag_span and tag == 'span':
            self.in_tag_span = False

        if self.in_strong and tag == 'strong':
            self.in_strong = False

        if tag == 'li' and self._in_li:
            self._in_li = False
            # 完成一个清单项的解析
            label_text = ''.join(self.current_label_parts).strip()
            if label_text:
                item = {
                    'data_id': self.current_data_id,
                    'label_text': label_text,
                    'strong_terms': list(self.current_strong_terms),
                    'tag_classes': list(self.current_tag_classes),
                }
                self.current_items.append(item)
            self.current_data_id = None
            self.current_label_parts = []
            self.current_strong_terms = []
            self.current_tag_classes = []

    def handle_data(self, data):
        if self.in_section_header:
            self.current_section += data
            self.current_section_name += data
            return

        if self.in_label:
            stripped = data.strip()
            if stripped:
                self.current_label_parts.append(stripped)
            if self.in_strong:
                self.current_strong_terms.append(stripped)

    def _flush_section(self):
        """保存当前 section 的 items 并重置。"""
        if self.current_items:
            section_title = self.current_section.strip()
            # 提取节名（去除序号前缀，如 "第1节 "）
            section_name = re.sub(r'^[📖🔬🧬🧪🔍💡📝🔥🎯\s]*第?\d*\s*节?\s*', '', section_title)
            self.sections.append((section_title, section_name, list(self.current_items)))
            self.current_items = []

    def finalize(self):
        """解析完成后，刷新最后一个 section。"""
        self._flush_section()


def _chapter_key_from_path(file_path: Path) -> str:
    """从文件路径推导 chapter_key。

    例如 book1/1.1.html → book1-ch1
    """
    parts = file_path.parts
    book = None
    chapter_num = None

    for p in parts:
        if p.startswith('book') and p[4:].isdigit():
            book = p
        # 匹配 N.N.html 格式
        m = re.match(r'(\d+)\.(\d+)\.html', p)
        if m:
            chapter_num = int(m.group(1))

    if book and chapter_num:
        return f"{book}-ch{chapter_num}"
    return ''


def _extract_chapter_name(label_text: str) -> str:
    """从标题文本中提取章节全名（匹配 DB 格式：第N章 ...）。

    例如 '第1章 走近细胞' → '第1章 走近细胞'
    """
    m = re.match(r'第\d+章\s*.+', label_text)
    if m:
        return m.group().strip()
    return ''


def _generate_key_terms(label_text: str, strong_terms: list, exclude_terms: set = None) -> list:
    """从知识点文本生成用于匹配的关键词列表。

    Args:
        label_text: 纯文本知识点描述
        strong_terms: 粗体词列表（最重要）
        exclude_terms: 需要排除的高频/通用词集合

    Returns:
        去重排序后的关键词列表（最多 15 个）
    """
    if exclude_terms is None:
        exclude_terms = set()
    terms = []

    # 1. 粗体词权重最高，排在最前面
    for t in strong_terms:
        t = t.strip()
        if t and len(t) >= 2 and t not in exclude_terms:
            terms.append(t)

    # 2. 提取英文专业术语 (ATP, DNA, RNA, NADPH, etc.)
    english_terms = re.findall(r'[A-Za-z][A-Za-z0-9+]+', label_text)
    for t in english_terms:
        if len(t) >= 2 and t.upper() not in ('C', 'D') and t not in exclude_terms:
            terms.append(t)

    # 3. 提取中文命名实体（人名、概念名）
    concept_patterns = [
        r'[一-鿿]{2,4}(学说|法则|定律|原理|效应|现象|过程)',
        r'[一-鿿]{2,3}(细胞|组织|器官|系统|生物|基因|蛋白|染色体)',
        r'(细胞|基因|染色体|蛋白质|酶|激素|核酸)[一-鿿]{1,4}',
        r'[一-鿿]{2,4}(作用|反应|分裂|分化|合成|运输|调节|免疫)',
        r'[一-鿿]{4,6}',
    ]
    for pattern in concept_patterns:
        matches = re.findall(pattern, label_text)
        for m in matches:
            if m not in exclude_terms:
                terms.append(m)

    # 4. 提取中文人物名 (2-4 字 + 常见后缀)
    person_matches = re.findall(r'[一-鿿]{2,4}(夫|德|尔|斯|特|文|克|格|曼|森)', label_text)
    for m in person_matches:
        if m not in exclude_terms:
            terms.append(m)

    # 5. 清理：去标点、去数字、去停用词
    clean = ''
    for ch in label_text:
        if ch in PUNCTUATION:
            clean += ' '
        else:
            clean += ch

    # 6. 提取 2-4 字 CJK 词组
    words = clean.split()
    for w in words:
        w_clean = w.strip()
        if 2 <= len(w_clean) <= 6 and not w_clean.isdigit() and w_clean not in STOP_WORDS:
            if w_clean not in exclude_terms:
                terms.append(w_clean)

    # 7. 如果上一步没有足够词组，尝试从整个文本中取 2-3 字 n-gram
    if len(terms) < 5:
        text_no_punct = ''.join(ch for ch in label_text if ch not in PUNCTUATION)
        for i in range(len(text_no_punct) - 1):
            bigram = text_no_punct[i:i+2]
            if bigram not in STOP_WORDS and not bigram.isdigit() and bigram not in exclude_terms:
                terms.append(bigram)
        for i in range(len(text_no_punct) - 2):
            trigram = text_no_punct[i:i+3]
            if trigram not in STOP_WORDS and not trigram.isdigit() and trigram not in exclude_terms:
                terms.append(trigram)

    # 8. 去重，按长度降序排列（长词更独特，优先匹配）
    seen = set()
    unique = []
    for t in terms:
        if t not in seen and len(t) >= 2 and t not in exclude_terms:
            seen.add(t)
            unique.append(t)

    unique.sort(key=lambda x: len(x), reverse=True)

    # 过滤太短的词（2字中文词区分度太低）和仅保留适当数量
    result = []
    for t in unique:
        # 英文缩写和数字组合可以短一些
        if t.encode('utf-8').isascii() and len(t) >= 2:
            result.append(t)
        elif len(t) >= 3:
            result.append(t)

    return result[:15]


def _compute_high_frequency_terms(all_points: list[dict], threshold_pct: float = 15.0) -> set:
    """计算在所有知识点中出现频率过高的通用词，用于过滤。

    如在超过 threshold_pct% 知识点中都出现的词，视为无区分度的通用词。
    """
    from collections import Counter
    term_count = Counter()
    total = len(all_points)

    for p in all_points:
        seen_in_point = set()
        for t in p.get('key_terms_temp', []):
            if t not in seen_in_point:
                term_count[t] += 1
                seen_in_point.add(t)

    threshold = total * threshold_pct / 100.0
    high_freq = {t for t, cnt in term_count.items() if cnt > threshold}
    return high_freq


def parse_all_knowledge_files() -> list[dict]:
    """解析所有知识 HTML 文件，返回知识点列表。

    Returns:
        list of dict: 每个 dict 含 chapter_key, book, chapter, section,
                      section_name, label_text, category, key_terms,
                      data_id, file_path
    """
    all_points = []

    if not KNOWLEDGE_DIR.exists():
        print(f"[KnowledgeParser] 知识目录不存在: {KNOWLEDGE_DIR}")
        return all_points

    # 遍历所有 bookN/N.M.html 文件
    for book_dir in sorted(KNOWLEDGE_DIR.iterdir()):
        if not book_dir.is_dir() or not book_dir.name.startswith('book'):
            continue

        for html_file in sorted(book_dir.glob('*.html')):
            chapter_key = _chapter_key_from_path(html_file)
            if not chapter_key:
                continue

            book_name = BOOK_NAMES.get(book_dir.name, book_dir.name)
            chapter_name_short = CHAPTER_NAMES.get(chapter_key, '')

            try:
                html_content = html_file.read_text(encoding='utf-8')
            except Exception as e:
                print(f"[KnowledgeParser] 读取失败: {html_file} — {e}")
                continue

            # 解析 HTML
            extractor = _KnowledgeExtractor()
            extractor.feed(html_content)
            extractor.finalize()

            # 尝试从 HTML 标题中提取章名
            title_m = re.search(r'<title>第\d+章\s*([^<]+)</title>', html_content)
            h1_m = re.search(r'<h1[^>]*>第\d+章\s*([^<]+)</h1>', html_content)
            if h1_m:
                chapter_full = f'第{chapter_key.split("ch")[-1]}章 {h1_m.group(1).strip()}'
            elif title_m:
                chapter_full = f'第{chapter_key.split("ch")[-1]}章 {title_m.group(1).strip()}'
            else:
                chapter_full = chapter_name_short if chapter_name_short else chapter_key

            # 为每个 section 下的 checklist item 生成知识点
            for section_title, section_name, items in extractor.sections:
                # 提取节号
                section_full = section_title.strip()
                if not section_full:
                    section_full = section_name

                for item in items:
                    # 确定分类
                    category = '重点'  # 默认
                    for cls in item['tag_classes']:
                        if cls in TAG_CATEGORY_MAP:
                            category = TAG_CATEGORY_MAP[cls]
                            break

                    # 第一遍：生成临时关键词（不过滤高频词）
                    key_terms_temp = _generate_key_terms(item['label_text'], item['strong_terms'])

                    point = {
                        'chapter_key': chapter_key,
                        'book': book_name,
                        'chapter': chapter_full,
                        'section': section_full,
                        'section_name': section_name,
                        'label_text': item['label_text'],
                        'category': category,
                        'strong_terms': item['strong_terms'],
                        'key_terms_temp': key_terms_temp,
                        'data_id': item.get('data_id'),
                        'file_path': str(html_file.relative_to(KNOWLEDGE_DIR.parent)),
                    }
                    all_points.append(point)

    # 第二遍：计算高频词并过滤
    high_freq = _compute_high_frequency_terms(all_points, threshold_pct=25.0)
    print(f"[KnowledgeParser] 过滤 {len(high_freq)} 个高频通用词: "
          f"{sorted(high_freq, key=lambda x: len(x), reverse=True)[:15]}...")

    for p in all_points:
        key_terms = [t for t in p['key_terms_temp'] if t not in high_freq]
        p['key_terms'] = key_terms
        # 清理临时字段
        del p['key_terms_temp']
        if 'strong_terms' in p:
            del p['strong_terms']

    return all_points


if __name__ == '__main__':
    points = parse_all_knowledge_files()
    print(f"[KnowledgeParser] 共解析 {len(points)} 条知识点")

    # 统计
    from collections import Counter
    cats = Counter(p['category'] for p in points)
    books = Counter(p['book'] for p in points)
    print(f"  分类: {dict(cats)}")
    print(f"  教材: {dict(books)}")

    if points:
        print(f"\n  样例 (前3条):")
        for p in points[:3]:
            print(f"    [{p['category']}] {p['book']} / {p['chapter']}")
            print(f"      {p['label_text'][:80]}...")
            print(f"      key_terms: {p['key_terms'][:8]}...")
