from fastapi import APIRouter, Header, Query
from service.question import import_questions, get_exam_list, get_exam_questions, submit_answer, get_exam_progress, get_user_exam_answers, get_wrong_answer_list, get_wrong_answer_stats_service, submit_retry_answer, toggle_mastered_service, set_wrong_answer_reason_service, get_questions_by_textbook_service, get_user_daily_answers, get_question_bank_structure_service, get_textbook_progress_service, get_textbook_chapter_progress_service, add_to_wrong_book_service, get_related_questions_service, get_single_question_service, run_knowledge_tagging_service
from model.knowledge_point import get_knowledge_points_by_chapter_key, get_all_knowledge_points
from database.db import get_db_connection
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

class ReasonRequest(BaseModel):
    error_reason: str

@router.put("/wrong-answers/{question_id}/reason")
def set_wrong_answer_reason(question_id: int, request: ReasonRequest, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")

    user_id = int(payload["msg"]["user_id"])
    return set_wrong_answer_reason_service(user_id, question_id, request.error_reason)

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


@router.get("/question-bank/structure")
def question_bank_structure():
    """获取题库的层级结构：教材→章→节，含各节点题目数量"""
    return get_question_bank_structure_service()


@router.get("/user/{user_id}/textbook-progress")
def textbook_progress(user_id: int):
    """获取用户每本教材的做题进度"""
    return get_textbook_progress_service(user_id)


@router.get("/textbook/chapters")
def textbook_chapters(textbook: str = Query(...), user_id: int = Query(...)):
    """获取某本教材各章节的做题进度（含用户数据）"""
    return get_textbook_chapter_progress_service(textbook, user_id)


@router.post("/wrong-answers/{question_id}")
def add_wrong_answer(question_id: int, answer: str = None, error_reason: str = None, token: str = Header(...)):
    """将题目加入错题本（可同时设置错误原因）"""
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")

    user_id = int(payload["msg"]["user_id"])
    return add_to_wrong_book_service(user_id, question_id, answer, error_reason)


@router.get("/questions/related/{question_id}")
def get_related_answers(question_id: int, limit: int = Query(5), token: str = Header(...)):
    """获取根据知识点推荐的相关题目"""
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    user_id = int(payload["msg"]["user_id"])
    return get_related_questions_service(user_id, question_id, limit)


@router.get("/questions/{question_id}")
def get_single_question(question_id: int):
    """获取单个题目"""
    return get_single_question_service(question_id)


@router.post("/knowledge/tag-all")
def tag_all_questions():
    """管理员触发：重新为所有题目自动打标"""
    return run_knowledge_tagging_service()


@router.get("/knowledge/points")
def get_knowledge_points(chapter_key: str = Query(None)):
    """获取知识点列表，可按章节 key 筛选（如 book1-ch1）"""
    db = get_db_connection()
    try:
        if chapter_key:
            points = get_knowledge_points_by_chapter_key(db, chapter_key)
        else:
            points = get_all_knowledge_points(db)
        return ApiResponse.success(data=points)
    except Exception as e:
        return ApiResponse.error(msg=f"获取知识点失败: {str(e)}")
    finally:
        db.close()