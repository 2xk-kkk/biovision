import os
import shutil
import re
import zipfile
from utils.response import ApiResponse
from database.db import get_db_connection

EXAM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "exams")
EXTERNAL_DIR = r"D:\biology_exams"

REGIONS = ['全国', '北京', '上海', '江苏', '浙江', '广东', '山东', '湖北', '湖南', '河北', '四川', '重庆', '陕西', '山西', '青海', '宁夏', '云南', '黑龙江', '吉林', '辽宁', '内蒙古', '河南', '安徽', '福建', '江西', '天津', '新疆', '海南', '甘肃', '贵州', '广西']

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
                
                all_regions.add(exam_region)
                if exam_year:
                    all_years.append(exam_year)
                
                exams.append({
                    "name": item,
                    "year": exam_year,
                    "region": exam_region,
                    "exam_type": exam_type,
                    "question_count": question_count,
                    "file_count": file_count,
                    "files": files
                })
        
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
        
        total_questions = 0
        parse_errors = []
        
        ext = os.path.splitext(file_name)[1].lower()
        
        if ext in ['.pdf', '.docx']:
            from service.document_parser import parse_and_save
            parse_result = parse_and_save(file_path, custom_title=category)
            if parse_result['success']:
                total_questions = parse_result['question_count']
            else:
                parse_errors.append(parse_result.get('msg', '解析失败'))
        
        elif ext == '.zip':
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(category_path)
            
            extracted_files = []
            for root, dirs, filenames in os.walk(category_path):
                for extracted_file in filenames:
                    extracted_files.append(os.path.join(root, extracted_file))
            
            for extracted_path in extracted_files:
                if os.path.isfile(extracted_path):
                    file_ext = os.path.splitext(extracted_path)[1].lower()
                    if file_ext in ['.pdf', '.docx']:
                        from service.document_parser import parse_and_save
                        parse_result = parse_and_save(extracted_path, custom_title=category)
                        if parse_result['success']:
                            total_questions += parse_result['question_count']
                        else:
                            parse_errors.append(parse_result.get('msg', '解析失败'))
        
        if total_questions > 0:
            msg = f"上传成功，解析出 {total_questions} 道题"
            if parse_errors:
                msg += f"（部分文件解析失败：{'; '.join(parse_errors[:3])}）"
            return ApiResponse.success(data={
                "file_path": file_path,
                "question_count": total_questions
            }, msg=msg)
        
        if parse_errors:
            return ApiResponse.error(msg=f"上传成功但未解析出题目，错误：{'; '.join(parse_errors)}")
        
        return ApiResponse.error(msg="上传成功但未解析出题目，请检查文件格式是否正确")
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

def get_exam_questions(exam_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, name FROM exams WHERE id = ?', (exam_id,))
        exam_row = cursor.fetchone()
        
        if not exam_row:
            return ApiResponse.error(msg="试卷不存在")
        
        exam_id, exam_name = exam_row
        
        cursor.execute('''
            SELECT id, number, stem, option_a, option_b, option_c, option_d, answer 
            FROM questions 
            WHERE exam_id = ? 
            ORDER BY number ASC
        ''', (exam_id,))
        
        questions = []
        for row in cursor.fetchall():
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
                'answer': row[7] if row[7] else ''
            })
        
        conn.close()
        
        return ApiResponse.success(data={
            'exam_id': exam_id,
            'exam_name': exam_name,
            'questions': questions,
            'question_count': len(questions)
        })
    except Exception as e:
        conn.close()
        return ApiResponse.error(msg=f"获取题目失败: {str(e)}")

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