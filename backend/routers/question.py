from fastapi import APIRouter, Header, Query
from service.question import import_questions, get_exam_list, get_exam_questions, submit_answer, get_exam_progress, get_user_exam_answers, get_random_quiz_questions
from service.question import get_wrong_answer_list, get_wrong_answer_stats_service, submit_retry_answer, toggle_mastered_service, categorize_all_questions
from utils.jwt_utils import verify_jwt
from utils.response import ApiResponse
from pydantic import BaseModel

router = APIRouter()

class MasterRequest(BaseModel):
    mastered: int = 1  # 1=已攻克, 0=待复习

@router.post("/questions/import")
def import_all_questions():
    return import_questions()

@router.get("/exams/list")
def list_all_exams():
    return get_exam_list()

@router.get("/exams/{exam_id}/questions")
def exam_questions(exam_id: int):
    return get_exam_questions(exam_id)

@router.get("/quiz/random")
def random_quiz_questions(count: int = Query(10, ge=1, le=50)):
    return get_random_quiz_questions(count)

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


# ========== 错题集 API ==========

@router.get("/wrong-answers")
def list_wrong_answers(
    token: str = Header(...),
    textbook: str = Query(default=None, description="教材筛选"),
    status: str = Query(default=None, description="状态筛选: all, mastered, unmastered"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
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
def retry_answer(question_id: int, answer: str = Query(...), token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")

    user_id = int(payload["msg"]["user_id"])
    return submit_retry_answer(user_id, question_id, answer)


@router.put("/wrong-answers/{question_id}/master")
def toggle_master(question_id: int, body: MasterRequest, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")

    user_id = int(payload["msg"]["user_id"])
    return toggle_mastered_service(user_id, question_id, body.mastered)


@router.post("/admin/categorize-questions")
def admin_categorize_questions():
    """管理接口：批量给题目打教材标签"""
    return categorize_all_questions()