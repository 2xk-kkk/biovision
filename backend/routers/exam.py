from fastapi import APIRouter, File, UploadFile, Form, Query
from service.exam import get_exam_list, get_exam_file, upload_exam_file, import_from_external, delete_exam_file, get_exam_questions
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.get("/exams")
def list_exams(year: str = Query(None), region: str = Query(None), scope: str = Query(None)):
    return get_exam_list(year=year, region=region, scope=scope)

@router.get("/exams/{exam_id}/questions")
def get_questions(exam_id: int):
    return get_exam_questions(exam_id)

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

@router.delete("/exams/file")
def delete_exam(file_path: str):
    return delete_exam_file(file_path)