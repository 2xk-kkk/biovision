"""Debug script for doc parser"""
import struct, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from service.doc_parser import _clean_extracted_text, _scan_for_text, _parse_ole_text, parse_exam_questions, read_doc_text

folder = r'D:\paper\大庆中学高三上学期生物期中试题及答案'
for f in os.listdir(folder):
    if f.endswith('.doc'):
        path = os.path.join(folder, f)
        print(f'Testing: {f}')
        
        # Read raw data
        with open(path, 'rb') as fh:
            data = fh.read()
        
        # Parse OLE
        text = _parse_ole_text(data)
        print(f'Extracted text: {len(text)} chars')
        print('First 500:')
        print(text[:500])
        print('...')
        
        # Try parsing questions
        questions = parse_exam_questions(text)
        print(f'\nQuestions found: {len(questions)}')
        for q in questions[:5]:
            print(f"  Q{q['number']}: {q['stem'][:60]}")
            print(f"    Options: A={q['options']['A'][:30]} B={q['options']['B'][:30]} C={q['options']['C'][:30]} D={q['options']['D'][:30]}")
            print()
        break
