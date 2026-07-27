import sys
sys.path.insert(0, '.')
from service.question import get_questions_by_textbook_service

result = get_questions_by_textbook_service(
    textbook='必修一：分子与细胞', 
    chapter='第1章 走近细胞', 
    section='专项训练', 
    question_type='fill'
)

if result['success'] and result['data']:
    for q in result['data']:
        if '细胞学说' in q['stem']:
            print(f"找到题目:")
            print(f"ID:{q['id']}")
            print(f"题干:{q['stem']}")
            print(f"答案:{q['answer']}")
            print(f"题型:{q['type']}")
