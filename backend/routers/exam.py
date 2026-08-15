from fastapi import APIRouter, File, UploadFile, Form, Query
from service.exam import get_exam_list, get_exam_file, upload_exam_file, import_from_external, delete_exam_file, get_exam_questions, parse_exam_to_db, parse_all_pending_exams, import_and_parse
from fastapi.responses import FileResponse
import os
import urllib.parse

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

router = APIRouter()

@router.get("/exams")
def list_exams(year: str = Query(None), region: str = Query(None), scope: str = Query(None)):
    return get_exam_list(year=year, region=region, scope=scope)

@router.get("/exams/{exam_id}/questions")
def get_questions(exam_id: int):
    return get_exam_questions(exam_id)

@router.get("/exams/image")
def get_exam_image(path: str):
    """获取试卷中的图片文件"""
    try:
        # URL解码路径
        decoded_path = urllib.parse.unquote(path)
        
        # 如果是Web路径（以/uploads/开头），转换为本地路径
        if decoded_path.startswith('/uploads/'):
            local_path = os.path.join(BASE_DIR, decoded_path.lstrip('/'))
        elif decoded_path.startswith('uploads/'):
            local_path = os.path.join(BASE_DIR, decoded_path)
        else:
            local_path = decoded_path
        
        if os.path.exists(local_path) and os.path.isfile(local_path):
            return FileResponse(local_path)
        return {"success": False, "msg": f"图片不存在: {local_path}"}
    except Exception as e:
        return {"success": False, "msg": f"获取图片失败: {str(e)}"}

@router.get("/exams/download")
def download_exam(file_path: str):
    if not os.path.exists(file_path):
        return {"success": False, "msg": "文件不存在"}
    
    return FileResponse(file_path, filename=os.path.basename(file_path))

@router.post("/exams/upload")
def upload_exam(category: str = Form(...), file: UploadFile = File(...)):
    contents = file.file.read()
    return upload_exam_file(category, file.filename, contents)

@router.post("/exams/import")
def import_exams():
    return import_from_external()

@router.post("/exams/parse")
def parse_exam(exam_name: str = Form(...)):
    """解析指定试卷文件夹"""
    return parse_exam_to_db(exam_name)

@router.post("/exams/parse-all")
def parse_all_exams():
    """解析所有尚未解析的试卷"""
    return parse_all_pending_exams()

@router.post("/exams/import-and-parse")
def import_and_parse_exams():
    """从D盘导入并解析所有试卷"""
    return import_and_parse()

@router.delete("/exams/file")
def delete_exam(file_path: str):
    return delete_exam_file(file_path)