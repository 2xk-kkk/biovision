import os
import shutil
import re
import sqlite3
import json
import sys
from utils.response import ApiResponse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXAM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "exams")
EXTERNAL_DIR = r"D:\paper"
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "forum.db")
# uploads 根目录（用于构建相对 Web 路径）
UPLOADS_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))
# 试卷图片静态目录（与 extract_questions 中的输出保持一致）
IMAGE_OUTPUT_DIR = os.path.join(UPLOADS_ROOT, "exam_images")


def local_path_to_web(local_path):
    """将项目 uploads 下的本地绝对路径转换为 Web 可访问的相对路径（/uploads/...）。非 uploads 内的路径原样返回。"""
    try:
        norm = os.path.normpath(os.path.abspath(local_path))
        if norm.startswith(os.path.normpath(UPLOADS_ROOT)):
            rel = os.path.relpath(norm, UPLOADS_ROOT).replace("\\", "/")
            return "/uploads/" + rel
    except Exception:
        pass
    return local_path


def web_path_to_local(web_path):
    """将 /uploads/... 相对路径转换为本地绝对路径；非 uploads 路径原样返回。"""
    if isinstance(web_path, str):
        if web_path.startswith("/uploads/"):
            rel = web_path[len("/uploads/"):]
            return os.path.normpath(os.path.join(UPLOADS_ROOT, *rel.split("/")))
        if web_path.startswith("uploads/") or web_path.startswith("uploads\\"):
            rel = web_path[len("uploads/") if web_path.startswith("uploads/") else len("uploads\\"):]
            return os.path.normpath(os.path.join(UPLOADS_ROOT, *rel.replace("\\", "/").split("/")))
    return web_path


def _sanitize_folder_name(name):
    """清洗试卷文件夹名，避免 Windows 非法字符与穿越。"""
    bad_chars = '<>:"/\\|?*'
    cleaned = "".join("_" if c in bad_chars else c for c in name).strip().strip(".")
    return cleaned or "exam_folder"

REGIONS = ['全国', '北京', '上海', '江苏', '浙江', '广东', '山东', '湖北', '湖南', '河北', '四川', '重庆', '陕西', '山西', '青海', '宁夏', '云南', '黑龙江', '吉林', '辽宁', '内蒙古', '河南', '安徽', '福建', '江西', '天津', '新疆', '海南', '甘肃', '贵州', '广西', '黑吉辽蒙', '黑吉辽', '陕晋青宁']

# 城市→省份映射（用于识别非知名高中的地区）
CITY_TO_PROVINCE = {
    '哈尔滨': '黑龙江', '大庆': '黑龙江', '虎林': '黑龙江', '双鸭山': '黑龙江', '东辽': '吉林',
    '长春': '吉林', '吉林市': '吉林', '四平': '吉林',
    '沈阳': '辽宁', '大连': '辽宁', '鞍山': '辽宁',
    '呼和浩特': '内蒙古', '包头': '内蒙古',
    '石家庄': '河北', '唐山': '河北', '保定': '河北',
    '郑州': '河南', '洛阳': '河南', '开封': '河南',
    '济南': '山东', '青岛': '山东', '烟台': '山东',
    '南京': '江苏', '苏州': '江苏', '无锡': '江苏',
    '杭州': '浙江', '宁波': '浙江', '温州': '浙江',
    '合肥': '安徽', '芜湖': '安徽',
    '福州': '福建', '厦门': '福建', '泉州': '福建',
    '南昌': '江西', '赣州': '江西',
    '武汉': '湖北', '宜昌': '湖北', '襄阳': '湖北',
    '长沙': '湖南', '株洲': '湖南',
    '广州': '广东', '深圳': '广东', '钦州': '广西', '南宁': '广西',
    '成都': '四川', '绵阳': '四川', '德阳': '四川',
    '重庆': '重庆',
    '西安': '陕西', '咸阳': '陕西',
    '兰州': '甘肃', '天水': '甘肃',
    '昆明': '云南', '大理': '云南',
    '贵阳': '贵州', '遵义': '贵州',
    '银川': '宁夏', '西宁': '青海',
    '乌鲁木齐': '新疆', '拉萨': '西藏',
    '海口': '海南', '三亚': '海南',
    '天津': '天津', '上海': '上海', '北京': '北京',
}

# 试卷练习页的知名高中列表（与前端 exam-practice.html 保持一致）
SCHOOLS = [
    '人大附中', '北京四中', '上海中学', '华师大二附中', '南京外国语', '杭二中',
    '华师一附中', '成都七中', '深圳中学', '衡水中学',
    # 新增：东北/华北/华东/中南/西南等名校
    '东北育才', '东北育才学校', '哈师大附中', '哈师大附属中学',
    '大庆中学', '大庆实验中学', '牡丹江一中', '双鸭山一中', '东辽一中',
    '吉林省实验中学', '吉大附中', '东北师大附中', '长春十一高',
    '沈阳市第', '大连育明', '大连二十四中', '大连二十中',
    '石家庄市二中', '唐山一中', '保定一中', '衡水二中',
    '郑州外国语', '郑州一中', '河南省实验中学', '洛阳一高', '洛阳市',
    '济南外国语', '山东省实验', '青岛二中', '青岛五十八中', '山东师大附中',
    '南京师大附中', '金陵中学', '苏州中学', '苏大附中', '姜堰二中', '江阴一中',
    '杭州学军', '杭州二中', '镇海中学', '宁波中学',
    '合肥一中', '合肥一六八', '芜湖一中',
    '福州一中', '厦门一中', '厦门双十', '泉州五中',
    '南昌十中', '南昌外国语', '九江一中',
    '武汉外国语', '武汉二中', '武汉六中', '华师大一附中',
    '长沙市一中', '雅礼中学', '长郡中学', '湖南师大附中',
    '广州执信', '广州二中', '广东实验中学', '肇庆中学',
    '绵阳中学', '绵阳南山', '德阳中学', '四川五校', '树德中学',
    '重庆一中', '重庆南开', '重庆巴蜀', '重庆八中',
    '西安交大附中', '西北工大附中', '陕师大附中', '西安中学',
    '钦州港区', '钦州一中', '南宁三中', '南宁二中',
    '昆明一中', '昆明三中', '云南师大附中', '贵阳一中',
    '兰州一中', '西北师大附中', '银川一中',
    '乌鲁木齐一中', '乌市一中', '海南中学',
    '青岛五十八中', '青岛二中', '山东省实验', '济南外国语',
    '大同一中', '太原五中', '山西大学附中',
    '呼和浩特二中', '包头市一中', '赤峰二中',
    '通辽一中', '鄂尔多斯一中',
    '成都九校联考', '成都七中', '南阳中学', '蓉城名校联盟',
    '吉林省实验', '吉林油田实验中学', '大港油田实验中学',
    '鸡西市第一中学', '鸡西一中', '佳木斯一中',
    '四川省树德中学', '江苏油田', '江阴', '姜堰',
    '大连', '青岛', '烟台二中', '威海二中'
]

# 试卷练习页的考试类型（与前端保持一致）
EXAM_TYPES = ['模拟考', '月考', '期中', '期末', '联考', '模拟题', '三模', '二模', '一模']

# 年级关键词映射
GRADE_KEYWORDS = {
    '高一': '高一',
    '高二': '高二',
    '高三': '高三',
}

def extract_grade(name):
    """从试卷名称中提取年级信息"""
    for keyword, grade in GRADE_KEYWORDS.items():
        if keyword in name:
            return grade
    return ''

def parse_exam_info(name):
    year = ''
    region = ''
    exam_type = '高考真题'
    question_count = 0
    grade = extract_grade(name)

    # 先提取考试类型（月考/期中/期末/模拟考/联考 等），从 name 中识别
    for t in EXAM_TYPES:
        if t in name:
            exam_type = t
            break

    # 先识别知名高中（比省份更具体，如"上海中学"应识别为学校而非"上海"）
    for s in SCHOOLS:
        if s in name:
            region = s
            break

    # 若未识别到学校，用城市→省份映射来识别地区
    if not region:
        for city, province in CITY_TO_PROVINCE.items():
            if city in name:
                region = province
                break

    patterns = [
        r'^(20\d{2})_([^_]+)_([^_]+)$',
        r'^(20\d{2})_([^_]+)$',
        r'^(20\d{2})年(.+?)高考',
        r'^(20\d{2})年(.+?)卷',
        r'^(2\d)(.+)$'
    ]

    matched = False
    for pattern in patterns:
        match = re.match(pattern, name)
        if match:
            if len(match.group(1)) == 2:
                year = '20' + match.group(1)
            else:
                year = match.group(1)

            if len(match.groups()) > 1:
                remaining = match.group(2)

                # 学校/城市优先；若未识别到，再退回省份匹配
                if not region:
                    for r in REGIONS:
                        if r in remaining:
                            region = r
                            break

                if not region:
                    region = '全国'

            matched = True
            break

    if not matched:
        year_match = re.search(r'(20\d{2})', name)
        if year_match:
            year = year_match.group(1)

        if not region:
            # 再次用城市映射兜底
            for city, province in CITY_TO_PROVINCE.items():
                if city in name:
                    region = province
                    break
            if not region:
                for r in REGIONS:
                    if r in name:
                        region = r
                        break
                if not region:
                    region = '其他'

    name_clean = name.replace(f'{year}_', '').replace(f'{year}年', '')
    if '卷' in name_clean:
        match = re.search(r'(.+?)卷', name_clean)
        if match:
            region_candidate = match.group(1).replace('_', '').replace('理综', '').replace('生物', '')
            if region_candidate and region_candidate != region:
                if region_candidate in REGIONS:
                    region = region_candidate

    if '新课标' in name:
        region = '新课标'

    region = region.replace('卷', '').strip()
    if region == '':
        region = '全国'

    return year, region, exam_type, question_count, grade

def get_exam_list(year=None, region=None, scope=None):
    exams = []
    stats = {
        'total_exams': 0,
        'total_regions': 0,
        'year_range': '',
        'total_questions': 0
    }
    
    if not os.path.exists(EXAM_DIR):
        return ApiResponse.error(msg="试卷目录不存在")
    
    try:
        db = sqlite3.connect(DB_PATH)
        db_cursor = db.cursor()
        
        all_regions = set()
        all_years = []
        
        for item in os.listdir(EXAM_DIR):
            item_path = os.path.join(EXAM_DIR, item)
            if os.path.isdir(item_path):
                files = []
                file_count = 0
                
                for root, dirs, filenames in os.walk(item_path):
                    for file_name in filenames:
                        if file_name.startswith('.') or file_name.endswith('.url'):
                            continue
                        file_path = os.path.join(root, file_name)
                        if os.path.isfile(file_path):
                            file_ext = os.path.splitext(file_name)[1].lower()
                            # 兼容：将本地 D:\\ 或项目内路径统一输出为 /uploads/exams/... Web 路径
                            web_path = local_path_to_web(file_path)
                            try:
                                size = os.path.getsize(file_path)
                            except OSError:
                                size = 0
                            files.append({
                                "name": file_name,
                                "path": web_path,          # 前端直接可用于 <a href>
                                "local_path": file_path,   # 后端读取用（解析/下载回退）
                                "extension": file_ext,
                                "size": size
                            })
                            file_count += 1
                
                if file_count == 0:
                    continue
                
                exam_year, exam_region, exam_type, question_count, exam_grade = parse_exam_info(item)

                # 试卷来源筛选：真题大观(非学校高考真题) vs 试卷练习(名校模拟卷)
                # scope='真题' 只返回高考真题（region 不是知名高中）；scope='模拟' 只返回名校模拟卷（region 是知名高中）
                if scope == '真题' and exam_region in SCHOOLS:
                    continue
                if scope == '模拟' and exam_region not in SCHOOLS:
                    continue

                if year and exam_year != year:
                    continue
                if region and region != '全部' and exam_region != region:
                    continue
                
                db_cursor.execute('SELECT id, question_count FROM exams WHERE name = ?', (item,))
                db_result = db_cursor.fetchone()
                db_id = db_result[0] if db_result else None
                db_question_count = db_result[1] if db_result else 0
                
                db_cursor.execute('SELECT COUNT(*) FROM questions WHERE exam_id = ?', (db_id,))
                question_count = db_cursor.fetchone()[0] if db_id else 0
                has_answers = question_count > 0
                
                all_regions.add(exam_region)
                if exam_year:
                    all_years.append(exam_year)
                
                exams.append({
                    "id": db_id,
                    "name": item,
                    "year": exam_year,
                    "grade": exam_grade,
                    "region": exam_region,
                    "exam_type": exam_type,
                    "question_count": db_question_count,
                    "file_count": file_count,
                    "has_answers": has_answers,
                    "files": files
                })
        
        db.close()
        
        exams.sort(key=lambda x: (x['year'] or '0', x['region']), reverse=True)
        
        stats['total_exams'] = len(exams)
        stats['total_regions'] = len(all_regions)
        if all_years:
            stats['year_range'] = f"{min(all_years)}-{max(all_years)}"
        stats['total_questions'] = sum(e['question_count'] for e in exams)
        
        years = sorted(set(e['year'] for e in exams if e['year']), reverse=True)
        regions = sorted(list(all_regions))
        
        return ApiResponse.success(data={
            'exams': exams,
            'stats': stats,
            'years': years,
            'regions': regions
        })
    except Exception as e:
        return ApiResponse.error(msg=f"读取试卷列表失败: {str(e)}")

def get_exam_file(file_path):
    if not os.path.exists(file_path):
        return ApiResponse.error(msg="文件不存在")
    
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        return content
    except Exception as e:
        return ApiResponse.error(msg=f"读取文件失败: {str(e)}")

def upload_exam_file(category: str, file_name: str, file_content: bytes):
    try:
        if not os.path.exists(EXAM_DIR):
            os.makedirs(EXAM_DIR)

        category_safe = _sanitize_folder_name(category)
        category_path = os.path.join(EXAM_DIR, category_safe)
        if not os.path.exists(category_path):
            os.makedirs(category_path, exist_ok=True)

        # 避免非法文件名 & 覆盖冲突
        file_name_safe = _sanitize_folder_name(file_name) or "exam_file"
        if not os.path.splitext(file_name_safe)[1]:
            # 保留原始扩展名
            orig_ext = os.path.splitext(file_name)[1] or ""
            file_name_safe = file_name_safe + orig_ext

        file_path = os.path.join(category_path, file_name_safe)
        base, ext = os.path.splitext(file_path)
        counter = 1
        while os.path.exists(file_path):
            file_path = f"{base}_{counter}{ext}"
            counter += 1

        with open(file_path, 'wb') as f:
            f.write(file_content)

        # 返回前端可直接访问的 Web 路径（/uploads/exams/...）
        web_path = local_path_to_web(file_path)
        return ApiResponse.success(data={"file_path": file_path, "web_path": web_path})
    except Exception as e:
        return ApiResponse.error(msg=f"上传文件失败: {str(e)}")


def import_from_external():
    if not os.path.exists(EXTERNAL_DIR):
        return ApiResponse.error(msg="外部试卷目录不存在")

    try:
        imported_exam_count = 0
        imported_file_count = 0
        skipped_dirs = []

        if not os.path.exists(EXAM_DIR):
            os.makedirs(EXAM_DIR, exist_ok=True)

        for item in os.listdir(EXTERNAL_DIR):
            src = os.path.join(EXTERNAL_DIR, item)
            if not os.path.isdir(src):
                continue
            # 1) 遍历 D 盘文件夹读取试卷
            folder_safe = _sanitize_folder_name(item)
            target_path = os.path.join(EXAM_DIR, folder_safe)
            if os.path.exists(target_path):
                skipped_dirs.append(item)
                continue

            # 2) 将 pdf/docx 等文件复制到项目 uploads/exams 目录
            try:
                shutil.copytree(src, target_path)
            except Exception as inner:
                skipped_dirs.append(f"{item}: {str(inner)}")
                continue

            # 清理 .url / 隐藏文件（非真实试卷文件，避免出现在列表中）
            for root, dirs, filenames in os.walk(target_path):
                for filename in filenames:
                    if filename.startswith('.') or filename.lower().endswith('.url'):
                        try:
                            os.remove(os.path.join(root, filename))
                        except Exception:
                            pass

            file_count = 0
            for root, dirs, filenames in os.walk(target_path):
                for filename in filenames:
                    if not filename.startswith('.') and not filename.lower().endswith('.url'):
                        file_count += 1
            imported_exam_count += 1
            imported_file_count += file_count

        msg = f"成功导入 {imported_exam_count} 个试卷文件夹，共 {imported_file_count} 个文件（已复制到后端 uploads/exams）"
        if skipped_dirs:
            msg += f"；跳过 {len(skipped_dirs)} 个（已存在/无法复制）"
        # 3) 数据库存 /uploads/exams/<试卷文件夹名>/<文件名> 的 Web 路径：
        #    试卷列表 get_exam_list 在 files 字段中通过 local_path_to_web 转换输出。
        #    此处只保证文件已进入项目 uploads 目录，后续解析/下载全部走静态路径。
        return ApiResponse.success(
            data={
                "imported_count": imported_file_count,
                "imported_exam_count": imported_exam_count,
                "skipped_count": len(skipped_dirs),
            },
            msg=msg
        )
    except Exception as e:
        return ApiResponse.error(msg=f"导入文件失败: {str(e)}")

def delete_exam_file(file_path: str):
    if not os.path.exists(file_path):
        return ApiResponse.error(msg="文件不存在")
    
    if not file_path.startswith(EXAM_DIR):
        return ApiResponse.error(msg="无权删除此文件")
    
    try:
        os.remove(file_path)
        return ApiResponse.success(msg="删除成功")
    except Exception as e:
        return ApiResponse.error(msg=f"删除文件失败: {str(e)}")

def get_exam_questions(exam_id: int):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name FROM exams WHERE id = ?', (exam_id,))
        exam_row = cursor.fetchone()
        
        if not exam_row:
            conn.close()
            return ApiResponse.error(msg="试卷不存在")
        
        exam_id_val, exam_name = exam_row
        
        # 获取试卷信息
        exam_year, exam_region, exam_type, _, exam_grade = parse_exam_info(exam_name)
        
        cursor.execute('''
            SELECT id, number, stem, option_a, option_b, option_c, option_d, answer, images, type, analysis 
            FROM questions 
            WHERE exam_id = ? 
            ORDER BY number ASC
        ''', (exam_id_val,))
        
        questions = []
        for row in cursor.fetchall():
            images_str = row[8] if row[8] else ''
            images = []
            if images_str:
                try:
                    images = json.loads(images_str)
                except:
                    images = []
            
            # 构建图片URL（如果图片是本地路径，转换为HTTP URL）
            image_urls = []
            for img in images:
                if img and isinstance(img, str):
                    if img.startswith('http'):
                        image_urls.append(img)
                    elif img.startswith('/uploads/') or img.startswith('uploads/'):
                        # 已经是web路径，直接使用
                        image_urls.append(img)
                    else:
                        # 本地图片路径，转换为可访问的URL
                        image_urls.append(f'/api/exams/image?path={img}')
            
            questions.append({
                'id': row[0],
                'number': row[1],
                'stem': row[2],
                'options': {
                    'A': row[3] if row[3] else '',
                    'B': row[4] if row[4] else '',
                    'C': row[5] if row[5] else '',
                    'D': row[6] if row[6] else ''
                },
                'answer': row[7] if row[7] else '',
                'images': image_urls,
                'type': row[9] if row[9] else '',
                'analysis': row[10] if row[10] else ''
            })
        
        conn.close()
        
        return ApiResponse.success(data={
            'exam_id': exam_id_val,
            'exam_name': exam_name,
            'exam_info': {
                'name': exam_name,
                'grade': exam_grade,
                'region': exam_region,
                'exam_type': exam_type,
                'year': exam_year
            },
            'questions': questions,
            'question_count': len(questions)
        })
    except Exception as e:
        return ApiResponse.error(msg=f"获取题目失败: {str(e)}")


def parse_exam_to_db(exam_name: str):
    """
    解析指定试卷文件夹，提取题目并保存到数据库。
    exam_name: 试卷文件夹名称（在 EXAM_DIR 下）
    """
    try:
        from service.doc_parser import process_exam_folder
        
        folder_path = os.path.join(EXAM_DIR, exam_name)
        if not os.path.exists(folder_path):
            return ApiResponse.error(msg=f"试卷文件夹不存在: {exam_name}")
        
        # 检查数据库中是否已有此试卷的记录
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, question_count FROM exams WHERE name = ?', (exam_name,))
        existing = cursor.fetchone()
        
        if existing and existing[1] > 0:
            conn.close()
            return ApiResponse.success(msg=f"试卷 {exam_name} 已解析过，无需重复解析")
        
        # 如果已有试卷记录但没有题目，先删除旧记录
        if existing:
            cursor.execute('DELETE FROM questions WHERE exam_id = ?', (existing[0],))
            cursor.execute('DELETE FROM exams WHERE id = ?', (existing[0],))
            conn.commit()
        
        # 解析文件夹
        result = process_exam_folder(folder_path)
        
        if not result or not result.get('success'):
            conn.close()
            msg = result.get('msg', '解析失败') if result else '解析失败'
            return ApiResponse.error(msg=f"解析 {exam_name} 失败: {msg}")
        
        questions = result.get('questions', [])
        if not questions:
            conn.close()
            return ApiResponse.error(msg=f"解析 {exam_name} 成功但未提取到题目")
        
        # 获取试卷信息
        exam_year, exam_region, exam_type, _, exam_grade = parse_exam_info(exam_name)
        
        # 插入试卷记录
        cursor.execute('''
            INSERT INTO exams (name, file_name, question_count)
            VALUES (?, ?, ?)
        ''', (exam_name, exam_name, len(questions)))
        exam_id = cursor.lastrowid
        
        # 插入题目
        inserted_count = 0
        for q in questions:
            q_num = q.get('number', 0)
            q_stem = q.get('stem', '')
            q_options = q.get('options', {})
            q_answer = q.get('answer', '')
            q_type = q.get('type', 'choice')
            q_analysis = q.get('analysis', '')
            
            if not q_stem or len(q_stem) < 3:
                continue
            
            # 确保选项字段不为空
            opt_a = q_options.get('A', '') if q_options else ''
            opt_b = q_options.get('B', '') if q_options else ''
            opt_c = q_options.get('C', '') if q_options else ''
            opt_d = q_options.get('D', '') if q_options else ''
            
            cursor.execute('''
                INSERT OR IGNORE INTO questions 
                (exam_id, number, stem, option_a, option_b, option_c, option_d, answer, type, analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (exam_id, q_num, q_stem, opt_a, opt_b, opt_c, opt_d, q_answer, q_type, q_analysis))
            inserted_count += 1
        
        # 更新试卷的题目数量
        cursor.execute('UPDATE exams SET question_count = ? WHERE id = ?', (inserted_count, exam_id))
        conn.commit()
        conn.close()
        
        return ApiResponse.success(data={
            'exam_name': exam_name,
            'exam_id': exam_id,
            'questions_found': len(questions),
            'questions_inserted': inserted_count
        }, msg=f"成功解析 {exam_name}，共提取 {len(questions)} 道题目，入库 {inserted_count} 道")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse.error(msg=f"解析试卷失败: {str(e)}")


def parse_all_pending_exams():
    """
    解析所有尚未解析的试卷（有文件但数据库中无题目的试卷）。
    """
    if not os.path.exists(EXAM_DIR):
        return ApiResponse.error(msg="试卷目录不存在")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        for item in os.listdir(EXAM_DIR):
            item_path = os.path.join(EXAM_DIR, item)
            if not os.path.isdir(item_path):
                continue
            
            # 检查是否有 .doc/.docx 文件
            has_doc = False
            for root, dirs, files in os.walk(item_path):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in ('.doc', '.docx'):
                        has_doc = True
                        break
                if has_doc:
                    break
            
            if not has_doc:
                results['skipped'] += 1
                continue
            
            # 检查数据库中是否已有此题目的记录
            cursor.execute('SELECT id, question_count FROM exams WHERE name = ?', (item,))
            existing = cursor.fetchone()
            
            if existing and existing[1] > 0:
                results['skipped'] += 1
                continue
            
            results['total'] += 1
            
            # 调用解析
            parse_result = parse_exam_to_db(item)
            
            if parse_result.get('success'):
                results['success'] += 1
                results['details'].append({
                    'name': item,
                    'status': 'success',
                    'msg': parse_result.get('msg', '')
                })
            else:
                results['failed'] += 1
                results['details'].append({
                    'name': item,
                    'status': 'failed',
                    'msg': parse_result.get('msg', '')
                })
        
        conn.close()
        
        return ApiResponse.success(data=results, msg=f"解析完成：成功 {results['success']} 个，失败 {results['failed']} 个，跳过 {results['skipped']} 个")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ApiResponse.error(msg=f"批量解析失败: {str(e)}")


def import_and_parse():
    """
    从D盘导入试卷并自动解析所有新试卷。
    """
    # 先导入
    import_result = import_from_external()
    
    if not import_result.get('success'):
        return import_result
    
    imported_count = import_result.get('data', {}).get('imported_count', 0)
    
    # 再批量解析
    parse_result = parse_all_pending_exams()
    
    result_data = {
        'imported_count': imported_count,
        'parse_result': parse_result.get('data') if parse_result.get('success') else None
    }
    
    msg = f"导入 {imported_count} 个文件"
    if parse_result.get('success') and parse_result.get('data'):
        msg += f"，解析成功 {parse_result['data']['success']} 个"
    
    return ApiResponse.success(data=result_data, msg=msg)