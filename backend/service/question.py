from database.db import get_db_connection
from model.question import add_exam, add_question, get_questions_by_exam, get_exams, save_user_answer, get_user_answers, get_exam_stats, get_exam_id, get_random_choice_questions
from utils.response import ApiResponse
import json
import os

def import_questions():
    questions_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'questions.json')
    if not os.path.exists(questions_file):
        return ApiResponse.error(msg="问题文件不存在")
    
    db = get_db_connection()
    try:
        with open(questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_count = 0
        for exam_name, exam_data in data.items():
            exam_id = add_exam(db, exam_name, exam_data.get('file', ''), exam_data.get('question_count', 0))
            
            for q in exam_data['questions']:
                add_question(
                    db,
                    exam_id,
                    q['number'],
                    q['stem'],
                    q['options']['A'],
                    q['options']['B'],
                    q['options']['C'],
                    q['options']['D'],
                    q['answer'],
                    q.get('images')
                )
                imported_count += 1
        
        return ApiResponse.success(data={"imported_count": imported_count}, msg=f"成功导入 {imported_count} 道题")
    except Exception as e:
        return ApiResponse.error(msg=f"导入失败: {str(e)}")
    finally:
        db.close()

def get_exam_list():
    db = get_db_connection()
    try:
        exams = get_exams(db)
        return ApiResponse.success(data=exams)
    except Exception as e:
        return ApiResponse.error(msg=f"获取试卷列表失败: {str(e)}")
    finally:
        db.close()

def get_exam_questions(exam_id):
    db = get_db_connection()
    try:
        questions = get_questions_by_exam(db, exam_id)
        return ApiResponse.success(data=questions)
    except Exception as e:
        return ApiResponse.error(msg=f"获取题目失败: {str(e)}")
    finally:
        db.close()

def submit_answer(user_id, question_id, answer):
    db = get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute('SELECT answer FROM questions WHERE id = ?', (question_id,))
        result = cursor.fetchone()
        if not result:
            return ApiResponse.error(msg="题目不存在")
        
        correct_answer = result[0]
        is_correct = 1 if answer == correct_answer else 0
        
        save_user_answer(db, user_id, question_id, answer, is_correct)
        
        return ApiResponse.success(data={
            'question_id': question_id,
            'your_answer': answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct
        }, msg="提交成功")
    except Exception as e:
        return ApiResponse.error(msg=f"提交失败: {str(e)}")
    finally:
        db.close()

def get_exam_progress(user_id, exam_id):
    db = get_db_connection()
    try:
        stats = get_exam_stats(db, exam_id, user_id)
        return ApiResponse.success(data=stats)
    except Exception as e:
        return ApiResponse.error(msg=f"获取进度失败: {str(e)}")
    finally:
        db.close()

def get_user_exam_answers(user_id, exam_id):
    db = get_db_connection()
    try:
        answers = get_user_answers(db, user_id, exam_id)
        return ApiResponse.success(data=answers)
    except Exception as e:
        return ApiResponse.error(msg=f"获取答题记录失败: {str(e)}")
    finally:
        db.close()

def get_random_quiz_questions(count=10):
    db = get_db_connection()
    try:
        questions = get_random_choice_questions(db, count)
        return ApiResponse.success(data={'questions': questions})
    except Exception as e:
        return ApiResponse.error(msg=f"获取随机题目失败: {str(e)}")
    finally:
        db.close()