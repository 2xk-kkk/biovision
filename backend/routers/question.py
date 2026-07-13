<<<<<<< HEAD
from fastapi import APIRouter, Header, Query
from service.question import import_questions, get_exam_list, get_exam_questions, submit_answer, get_exam_progress, get_user_exam_answers, get_random_quiz_questions
=======
from fastapi import APIRouter, Header
from service.question import import_questions, get_exam_list, get_exam_questions, submit_answer, get_exam_progress, get_user_exam_answers
>>>>>>> 3dda3ed5df70478afd4f8e6ec969e6318ce519a0
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

<<<<<<< HEAD
@router.get("/quiz/random")
def random_quiz_questions(count: int = Query(10, ge=1, le=50)):
    return get_random_quiz_questions(count)

=======
>>>>>>> 3dda3ed5df70478afd4f8e6ec969e6318ce519a0
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