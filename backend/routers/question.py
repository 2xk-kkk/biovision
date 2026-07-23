from fastapi import APIRouter, Header
from service.question import import_questions, get_exam_list, get_exam_questions, submit_answer, get_exam_progress, get_user_exam_answers
from utils.jwt_utils import verify_jwt
from utils.response import ApiResponse

router = APIRouter()

@router.post("/questions/import")
def import_all_questions():
    return import_questions()

@router.get("/exams/list")
def list_all_exams():
    return get_exam_list()

@router.get("/exams/{exam_id}/questions")
def exam_questions(exam_id: int):
    return get_exam_questions(exam_id)

@router.post("/questions/answer")
def answer_question(question_id: int, answer: str, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    user_id = int(payload["msg"]["user_id"])
    return submit_answer(user_id, question_id, answer)

@router.get("/exams/{exam_id}/progress")
def exam_progress(exam_id: int, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    user_id = int(payload["msg"]["user_id"])
    return get_exam_progress(user_id, exam_id)

@router.get("/exams/{exam_id}/my_answers")
def my_exam_answers(exam_id: int, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    user_id = int(payload["msg"]["user_id"])
    return get_user_exam_answers(user_id, exam_id)