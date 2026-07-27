from database.db import get_db_connection
from model.question import add_exam, add_question, get_questions_by_exam, get_exams, save_user_answer, get_user_answers, get_exam_stats, get_exam_id, get_wrong_answers, get_wrong_answer_stats, mark_mastered, retry_wrong_answer, get_questions_by_textbook, get_questions_by_type
from utils.response import ApiResponse
import json
import os
import random

def import_questions():
    questions_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'questions.json')
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
        is_correct = 1 if answer.strip().upper() == correct_answer.strip().upper() else 0
        
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

def get_wrong_answer_list(user_id, textbook=None, status=None, page=1, page_size=20):
    db = get_db_connection()
    try:
        result = get_wrong_answers(db, user_id, textbook, status, page, page_size)
        return ApiResponse.success(data=result)
    except Exception as e:
        return ApiResponse.error(msg=f"获取错题列表失败: {str(e)}")
    finally:
        db.close()

def get_wrong_answer_stats_service(user_id):
    db = get_db_connection()
    try:
        stats = get_wrong_answer_stats(db, user_id)
        return ApiResponse.success(data=stats)
    except Exception as e:
        return ApiResponse.error(msg=f"获取错题统计失败: {str(e)}")
    finally:
        db.close()

def submit_retry_answer(user_id, question_id, answer):
    db = get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute('SELECT answer FROM questions WHERE id = ?', (question_id,))
        result = cursor.fetchone()
        if not result:
            return ApiResponse.error(msg="题目不存在")

        correct_answer = result[0]
        is_correct = 1 if answer.strip().upper() == correct_answer.strip().upper() else 0

        retry_wrong_answer(db, user_id, question_id, answer, is_correct)

        cursor.execute(
            'SELECT wrong_count, mastered FROM user_answers WHERE user_id = ? AND question_id = ?',
            (user_id, question_id)
        )
        row = cursor.fetchone()
        wrong_count = row[0] if row else 0
        mastered = row[1] if row else 0

        return ApiResponse.success(data={
            'question_id': question_id,
            'your_answer': answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'wrong_count': wrong_count,
            'mastered': mastered
        }, msg="回答正确！已自动标记为已攻克" if is_correct else "回答错误，请继续努力")
    except Exception as e:
        return ApiResponse.error(msg=f"提交失败: {str(e)}")
    finally:
        db.close()

def toggle_mastered_service(user_id, question_id, mastered=1):
    db = get_db_connection()
    try:
        success = mark_mastered(db, user_id, question_id, mastered)
        if success:
            return ApiResponse.success(msg="操作成功")
        else:
            return ApiResponse.error(msg="操作失败")
    except Exception as e:
        return ApiResponse.error(msg=f"操作失败: {str(e)}")
    finally:
        db.close()

def get_questions_by_textbook_service(textbook=None, chapter=None, section=None, question_type=None):
    db = get_db_connection()
    try:
        if question_type == 'comprehensive':
            choice_questions = get_questions_by_type(db, textbook, chapter, section, 'choice')
            fill_questions = get_questions_by_type(db, textbook, chapter, section, 'fill')
            essay_questions = get_questions_by_type(db, textbook, chapter, section, 'essay')
            
            if len(fill_questions) < 2:
                fill_questions = get_questions_by_type(db, textbook, chapter, None, 'fill')
            
            if len(essay_questions) < 1:
                essay_questions = get_questions_by_type(db, textbook, chapter, None, 'essay')
            
            if len(choice_questions) < 2:
                choice_questions = get_questions_by_type(db, textbook, chapter, None, 'choice')
            
            selected_choice = random.sample(choice_questions, min(2, len(choice_questions))) if choice_questions else []
            selected_fill = random.sample(fill_questions, min(2, len(fill_questions))) if fill_questions else []
            selected_essay = random.sample(essay_questions, min(1, len(essay_questions))) if essay_questions else []
            
            questions = selected_choice + selected_fill + selected_essay
            random.shuffle(questions)
        else:
            questions = get_questions_by_textbook(db, textbook, chapter, '专项训练', question_type)
            
            if len(questions) == 0:
                questions = get_questions_by_textbook(db, textbook, chapter, section, question_type)
            
            if len(questions) == 0:
                questions = get_questions_by_textbook(db, textbook, chapter, None, question_type)
        
        return ApiResponse.success(data=questions)
    except Exception as e:
        return ApiResponse.error(msg=f"获取题目失败: {str(e)}")
    finally:
        db.close()