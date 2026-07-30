from fastapi import APIRouter, Header, Query
from service.question import import_questions, get_exam_list, get_exam_questions, submit_answer, get_exam_progress, get_user_exam_answers, get_wrong_answer_list, get_wrong_answer_stats_service, submit_retry_answer, toggle_mastered_service, get_questions_by_textbook_service, get_user_daily_answers
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

@router.get("/wrong-answers")
def wrong_answers(
    token: str = Header(...),
    textbook: str = Query(None),
    status: str = Query(None),
    page: int = Query(1),
    page_size: int = Query(20)
):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    user_id = int(payload["msg"]["user_id"])
    return get_wrong_answer_list(user_id, textbook, status, page, page_size)

@router.get("/wrong-answers/stats")
def wrong_answer_stats(token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    user_id = int(payload["msg"]["user_id"])
    return get_wrong_answer_stats_service(user_id)

@router.post("/wrong-answers/{question_id}/retry")
def retry_wrong_answer(question_id: int, answer: str, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    user_id = int(payload["msg"]["user_id"])
    return submit_retry_answer(user_id, question_id, answer)

from pydantic import BaseModel

class MasterRequest(BaseModel):
    mastered: int = 1

@router.put("/wrong-answers/{question_id}/master")
def master_wrong_answer(question_id: int, request: MasterRequest, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    user_id = int(payload["msg"]["user_id"])
    return toggle_mastered_service(user_id, question_id, request.mastered)

@router.get("/questions/textbook")
def textbook_questions(
    textbook: str = Query(None),
    chapter: str = Query(None),
    section: str = Query(None),
    type: str = Query(None)
):
    return get_questions_by_textbook_service(textbook, chapter, section, type)


@router.get("/user/{user_id}/daily-answers")
def user_daily_answers(user_id: int, days: int = Query(90)):
    """获取用户最近N天每天的做题数量"""
    return get_user_daily_answers(user_id, days)