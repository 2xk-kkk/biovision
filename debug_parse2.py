import sys
sys.path.insert(0, 'd:/15821/biovision/backend')

from service.document_parser import extract_text_from_docx

pages = extract_text_from_docx(r'd:/15821/biovision/backend/uploads/exams/2026_黑吉辽蒙卷_生物/2026年高考黑吉辽蒙卷生物高考真题试题(含答案).docx')
lines = pages[0].split('\n')
for i, line in enumerate(lines):
    print(f'{i}: {line[:100]}')
