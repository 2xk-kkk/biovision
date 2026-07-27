import sys
sys.path.insert(0, '.')
from service.question import get_questions_by_textbook_service

result = get_questions_by_textbook_service(
    textbook='必修一：分子与细胞', 
    chapter='第1章 走近细胞', 
    section='第1节 细胞是生命活动的基本单位', 
    question_type='choice'
)

print("API返回:")
print(f"成功:{result['success']}")
print(f"数量:{len(result['data'])}")
print()

if result['success'] and result['data']:
    for q in result['data'][:5]:
        print(f"ID:{q['id']}")
        print(f"  题型:{q['type']}")
        print(f"  小节:{q['section']}")
        print(f"  题干:{q['stem'][:60]}...")
        print(f"  答案:{q['answer']}")
        print(f"  解析:{q['analysis'][:80]}..." if q['analysis'] else "  解析:空")
        print()
