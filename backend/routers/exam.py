from fastapi import APIRouter, File, UploadFile, Form, Query
from service.exam import get_exam_list, get_exam_file, upload_exam_file, import_from_external, delete_exam_file, get_exam_questions, parse_exam_to_db, parse_all_pending_exams, import_and_parse, web_path_to_local, local_path_to_web
from fastapi.responses import FileResponse
from utils.response import ApiResponse
import os
import urllib.parse

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')


def _resolve_local_path(raw_path: str):
    """将前端传入的 raw_path（可能是 /uploads/... Web 路径，也可能是 Windows 本地绝对路径）解析为本地绝对路径。"""
    if not raw_path:
        return None
    decoded = urllib.parse.unquote(raw_path)
    # 1) 若是 /uploads/... 或 uploads/... 先走 web→local 转换
    if decoded.startswith('/uploads/') or decoded.startswith('uploads/') or decoded.startswith('uploads\\'):
        return web_path_to_local(decoded)
    # 2) 若是 /api/exams/image 形式的 URL 片段，提取其 path 参数
    if '?path=' in decoded:
        idx = decoded.find('?path=') + len('?path=')
        return _resolve_local_path(decoded[idx:])
    # 3) 本地绝对路径直接返回，但仅限位于 UPLOAD_DIR 或 EXTERNAL_DIR 下的文件
    return decoded

router = APIRouter()

@router.get("/exams")
def list_exams(year: str = Query(None), region: str = Query(None), scope: str = Query(None)):
    return get_exam_list(year=year, region=region, scope=scope)

@router.get("/exams/{exam_id}/questions")
def get_questions(exam_id: int):
    return get_exam_questions(exam_id)

@router.get("/exams/image")
def get_exam_image(path: str):
    """获取试卷中的图片文件（/uploads/... Web 路径或本地磁盘路径均兼容）"""
    try:
        local_path = _resolve_local_path(path)
        if local_path and os.path.exists(local_path) and os.path.isfile(local_path):
            return FileResponse(local_path)
        return ApiResponse.error(msg=f"图片不存在: {path}")
    except Exception as e:
        return ApiResponse.error(msg=f"获取图片失败: {str(e)}")


@router.get("/exams/download")
def download_exam(file_path: str):
    """下载试卷文件：接受 /uploads/exams/xxx 的 Web 路径或本地绝对路径。"""
    local_path = _resolve_local_path(file_path)
    if not local_path or not os.path.exists(local_path) or not os.path.isfile(local_path):
        return ApiResponse.error(msg=f"文件不存在: {file_path}")

    return FileResponse(local_path, filename=os.path.basename(local_path))

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
    """删除试卷文件：接受 /uploads/... 或本地绝对路径。仅允许删除位于项目 uploads/exams 下的文件。"""
    resolved = _resolve_local_path(file_path)
    if not resolved:
        return ApiResponse.error(msg="无效的文件路径")
    return delete_exam_file(resolved)