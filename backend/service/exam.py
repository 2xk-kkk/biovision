import os
import shutil
import re
import sqlite3
import json
from utils.response import ApiResponse

EXAM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "exams")
EXTERNAL_DIR = r"D:\biology_exams"
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "forum.db")

REGIONS = ['全国', '北京', '上海', '江苏', '浙江', '广东', '山东', '湖北', '湖南', '河北', '四川', '重庆', '陕西', '山西', '青海', '宁夏', '云南', '黑龙江', '吉林', '辽宁', '内蒙古', '河南', '安徽', '福建', '江西', '天津', '新疆', '海南', '甘肃', '贵州', '广西', '黑吉辽蒙', '黑吉辽', '陕晋青宁']

def parse_exam_info(name):
    year = ''
    region = ''
    exam_type = '高考真题'
    question_count = 0
    
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
    
    return year, region, exam_type, question_count

def get_exam_list(year=None, region=None):
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
                            files.append({
                                "name": file_name,
                                "path": file_path,
                                "extension": file_ext,
                                "size": os.path.getsize(file_path)
                            })
                            file_count += 1
                
                if file_count == 0:
                    continue
                
                exam_year, exam_region, exam_type, question_count = parse_exam_info(item)
                
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
        
        category_path = os.path.join(EXAM_DIR, category)
        if not os.path.exists(category_path):
            os.makedirs(category_path)
        
        file_path = os.path.join(category_path, file_name)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return ApiResponse.success(data={"file_path": file_path})
    except Exception as e:
        return ApiResponse.error(msg=f"上传文件失败: {str(e)}")

def import_from_external():
    if not os.path.exists(EXTERNAL_DIR):
        return ApiResponse.error(msg="外部试卷目录不存在")
    
    try:
        imported_count = 0
        for item in os.listdir(EXTERNAL_DIR):
            item_path = os.path.join(EXTERNAL_DIR, item)
            if os.path.isdir(item_path):
                target_path = os.path.join(EXAM_DIR, item)
                if os.path.exists(target_path):
                    continue
                
                shutil.copytree(item_path, target_path)
                file_count = 0
                for root, dirs, filenames in os.walk(target_path):
                    for filename in filenames:
                        if not filename.startswith('.'):
                            file_count += 1
                imported_count += file_count
        
        return ApiResponse.success(data={"imported_count": imported_count}, msg=f"成功导入 {imported_count} 个文件")
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
        
        cursor.execute('''
            SELECT id, number, stem, option_a, option_b, option_c, option_d, answer, images 
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
                'images': images if images else []
            })
        
        conn.close()
        
        return ApiResponse.success(data={
            'exam_id': exam_id_val,
            'exam_name': exam_name,
            'questions': questions,
            'question_count': len(questions)
        })
    except Exception as e:
        return ApiResponse.error(msg=f"获取题目失败: {str(e)}")