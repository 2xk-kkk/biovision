import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from service.document_parser import parse_and_save

EXAM_DIR = os.path.join(os.path.dirname(__file__), 'backend', 'uploads', 'exams')

def reparse_all():
    if not os.path.exists(EXAM_DIR):
        print(f"试卷目录不存在: {EXAM_DIR}")
        return
    
    total_parsed = 0
    total_questions = 0
    failed = []
    
    for item in os.listdir(EXAM_DIR):
        item_path = os.path.join(EXAM_DIR, item)
        if not os.path.isdir(item_path):
            continue
        
        has_pdf_or_docx = False
        pdf_files = []
        
        for root, dirs, filenames in os.walk(item_path):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.pdf', '.docx']:
                    has_pdf_or_docx = True
                    pdf_files.append(os.path.join(root, filename))
        
        if not has_pdf_or_docx:
            print(f"跳过 {item} (无PDF/docx文件)")
            continue
        
        print(f"\n解析试卷: {item}")
        
        for pdf_file in pdf_files:
            print(f"  处理文件: {os.path.basename(pdf_file)}")
            result = parse_and_save(pdf_file, custom_title=item)
            if result['success']:
                print(f"  ✓ 成功解析 {result['question_count']} 道题")
                total_parsed += 1
                total_questions += result['question_count']
            else:
                print(f"  ✗ 解析失败: {result['msg']}")
                failed.append(item)
    
    print(f"\n{'='*50}")
    print(f"解析完成！")
    print(f"成功解析: {total_parsed} 个试卷")
    print(f"总计题目: {total_questions} 道")
    if failed:
        print(f"解析失败: {len(failed)} 个试卷")
        for f in failed:
            print(f"  - {f}")

if __name__ == '__main__':
    reparse_all()
