# -*- coding: utf-8 -*-
"""
更智能的匹配：用题干中的多个关键词组合搜索
"""
import sqlite3
import re
import os
from docx import Document

WORD_FILE = r'D:\biology\遗传因子的发现 全章节专项练习题（2小节·每题15道·含详细解析）.docx'
DB_FILE = 'forum.db'

def parse_word_questions(filepath):
    doc = Document(filepath)
    questions = []
    current_question = None
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        
        q_match = re.match(r'^(\d+)[\.、]\s*(.+)$', text)
        if q_match and not text.startswith('【') and not text.startswith('答案') and not text.startswith('解析'):
            q_num = int(q_match.group(1))
            q_content = q_match.group(2)
            
            skip_keywords = ['本大题', '每题只有', '适用教材', '适用范围', '题型说明', '题型配置']
            if any(kw in q_content for kw in skip_keywords):
                continue
            
            if current_question and current_question['stem']:
                questions.append(current_question)
            
            current_question = {
                'number': q_num,
                'stem': q_content,
                'options': {},
                'answer': '',
                'analysis': ''
            }
            continue
        
        if current_question:
            opt_matches = re.findall(r'([ABCD])[\.、]\s*([^ABCD【\n]+?)(?=\s+[ABCD][\.、]|$)', text)
            if opt_matches and len(opt_matches) >= 1 and not text.startswith('【'):
                for key, value in opt_matches:
                    value = value.strip()
                    if value and key not in current_question['options']:
                        current_question['options'][key] = value
                continue
            
            opt_match = re.match(r'^([ABCD])[\.、]\s*(.+)$', text)
            if opt_match and not text.startswith('【'):
                current_question['options'][opt_match.group(1)] = opt_match.group(2).strip()
                continue
            
            ans_match = re.match(r'^【答案】\s*(.+)$', text)
            if ans_match:
                current_question['answer'] = ans_match.group(1).strip()
                continue
            
            an_match = re.match(r'^【解析】\s*(.+)$', text)
            if an_match:
                current_question['analysis'] = an_match.group(1).strip()
                continue
            
            an_match2 = re.match(r'^解析[：:]\s*(.+)$', text)
            if an_match2:
                current_question['analysis'] = an_match2.group(1).strip()
                continue
    
    if current_question and current_question['stem']:
        questions.append(current_question)
    
    return questions

def find_best_match(cursor, stem):
    """用多个关键词逐步搜索，找到最匹配的题目"""
    # 清理题干中的特殊符号
    stem_clean = stem.replace('（', '(').replace('）', ')').replace('₁', '1').replace('₂', '2')
    
    # 方法1: 用题干前15字符精确匹配
    keyword1 = stem_clean[:15].strip()
    cursor.execute("""
        SELECT id, stem, answer, analysis, chapter, section
        FROM questions 
        WHERE stem LIKE ? 
        AND (analysis IS NULL OR analysis = '' OR analysis = 'None')
        LIMIT 5
    """, (f'%{keyword1}%',))
    results = cursor.fetchall()
    if results:
        return results[0]
    
    # 方法2: 用题干前10字符
    keyword2 = stem_clean[:10].strip()
    cursor.execute("""
        SELECT id, stem, answer, analysis, chapter, section
        FROM questions 
        WHERE stem LIKE ? 
        AND (analysis IS NULL OR analysis = '' OR analysis = 'None')
        LIMIT 5
    """, (f'%{keyword2}%',))
    results = cursor.fetchall()
    if results:
        return results[0]
    
    # 方法3: 提取核心关键词（去掉括号内容，用主要词语）
    # 提取3-5个汉字的关键短语
    words = re.findall(r'[\u4e00-\u9fff]{3,5}', stem_clean)
    for word in words:
        cursor.execute("""
            SELECT id, stem, answer, analysis, chapter, section
            FROM questions 
            WHERE stem LIKE ? 
            AND (analysis IS NULL OR analysis = '' OR analysis = 'None')
            LIMIT 3
        """, (f'%{word}%',))
        results = cursor.fetchall()
        if results:
            return results[0]
    
    return None

def main():
    print(f"读取: {WORD_FILE}")
    questions = parse_word_questions(WORD_FILE)
    with_analysis = [q for q in questions if q.get('analysis')]
    print(f"解析出 {len(questions)} 道题, 有解析 {len(with_analysis)} 道")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    updated = 0
    not_found = 0
    
    for q in with_analysis:
        stem = q['stem'].strip()
        match = find_best_match(cursor, stem)
        
        if match:
            cursor.execute("""
                UPDATE questions SET analysis = ? WHERE id = ?
            """, (q['analysis'], match[0]))
            print(f"✅ 更新ID={match[0]} [{match[5]}]: {stem[:40]}...")
            updated += 1
        else:
            not_found += 1
            print(f"❌ 未匹配: {stem[:50]}...")
    
    conn.commit()
    conn.close()
    
    print(f"\n完成! 更新 {updated} 道, 未匹配 {not_found} 道")

if __name__ == '__main__':
    main()
