"""
Pure Python .doc (OLE compound document) parser for biology exam papers.
Extracts text from Word binary .doc files and parses exam questions.
No external dependencies required.
"""
import struct
import re
import os


def read_doc_text(file_path):
    """Extract text from a .doc file using OLE compound document parsing."""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        return _parse_ole_text(data)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ''


def _parse_ole_text(data):
    """Parse OLE2 compound document and extract text."""
    if data[:8] != b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
        return _fallback_extract_from_data(data)

    # Parse header
    sector_size_power = struct.unpack_from('<H', data, 30)[0]
    sector_size = 1 << sector_size_power
    first_dir_sector = struct.unpack_from('<I', data, 48)[0]
    mini_stream_cutoff = struct.unpack_from('<I', data, 56)[0]

    # Read FAT sectors from header
    fat_sectors = []
    for i in range(109):
        val = struct.unpack_from('<I', data, 76 + i * 4)[0]
        if val >= 0xFFFFFFFE:
            break
        fat_sectors.append(val)

    # Build FAT chain
    fat_data = bytearray()
    for sec in fat_sectors:
        offset = 512 + sec * sector_size
        if offset + sector_size <= len(data):
            fat_data.extend(data[offset:offset + sector_size])

    fat_entries = []
    for i in range(0, len(fat_data), 4):
        fat_entries.append(struct.unpack_from('<I', fat_data, i)[0])

    # Read directory from first_dir_sector
    dir_data = bytearray()
    cur_sector = first_dir_sector
    visited = set()
    while cur_sector < 0xFFFFFFFE and cur_sector not in visited:
        visited.add(cur_sector)
        offset = 512 + cur_sector * sector_size
        if offset + sector_size <= len(data):
            dir_data.extend(data[offset:offset + sector_size])
        cur_sector = fat_entries[cur_sector] if cur_sector < len(fat_entries) else 0xFFFFFFFE

    # Parse directory entries (128 bytes each)
    entries = []
    for i in range(0, len(dir_data), 128):
        entry = dir_data[i:i + 128]
        if len(entry) < 128:
            break
        name_bytes = entry[:64]
        name_len = struct.unpack_from('<H', entry, 64)[0]
        name = ''
        if name_len > 0 and name_len <= 64:
            name = name_bytes[:name_len - 2].decode('utf-16-le', errors='ignore')
        entry_type = entry[66]
        start_sector = struct.unpack_from('<I', entry, 116)[0]
        size = struct.unpack_from('<I', entry, 120)[0] | (struct.unpack_from('<I', entry, 124)[0] << 32)
        entries.append({'name': name, 'type': entry_type, 'start': start_sector, 'size': size})

    # Find WordDocument stream
    word_doc = None
    for e in entries:
        if e['name'] == 'WordDocument' and e['type'] == 2:
            word_doc = e
            break

    if not word_doc:
        return _fallback_extract_from_data(data)

    # Read WordDocument stream
    word_stream = _read_chain(word_doc['start'], word_doc['size'], data, fat_entries, sector_size)

    # Parse text from WordDocument
    return _extract_text_from_word_stream(word_stream)


def _read_chain(start_sector, size, data, fat_entries, sector_size):
    """Read data from a sector chain."""
    result = bytearray()
    cur = start_sector
    visited = set()
    sectors_read = 0
    max_sectors = (size + sector_size - 1) // sector_size + 5

    while cur < 0xFFFFFFFE and cur not in visited and sectors_read < max_sectors:
        visited.add(cur)
        offset = 512 + cur * sector_size
        if offset + sector_size <= len(data):
            result.extend(data[offset:offset + sector_size])
        if cur < len(fat_entries):
            cur = fat_entries[cur]
        else:
            break
        sectors_read += 1

    return bytes(result[:size])


def _extract_text_from_word_stream(word_stream):
    """Extract text from WordDocument stream."""
    if len(word_stream) < 32:
        return ''

    w_ident = struct.unpack_from('<H', word_stream, 0)[0]
    if w_ident != 0xA5EC:
        return _fallback_text_scan(word_stream)

    flags = struct.unpack_from('<H', word_stream, 10)[0]
    f_complex = flags & 0x04  # bit 2

    if f_complex:
        # Complex document - would need Piece Table from 1Table/0Table
        # For now, scan for text
        return _fallback_text_scan(word_stream)
    else:
        # Simple document
        # Text is stored as UTF-16LE starting at a calculated offset
        # The actual text often starts after the FIB area
        # Try scanning for Chinese text patterns
        return _scan_for_text(word_stream)


def _scan_for_text(word_stream):
    """Scan WordDocument stream for Chinese/English text."""
    # Strategy: look for UTF-16LE encoded text regions
    # Skip the FIB area and find the first line of coherent text

    # First, try to find text by looking for known document patterns
    # Common patterns in Chinese exam papers
    text_start = None

    # Look for coherent Chinese text: multiple consecutive Chinese characters
    for offset in range(1536, min(len(word_stream), 10000), 64):
        sample_size = min(256, len(word_stream) - offset)
        sample = word_stream[offset:offset + sample_size]
        try:
            decoded = sample.decode('utf-16-le', errors='ignore')
            # Count consecutive Chinese characters
            max_consecutive = 0
            current_consecutive = 0
            for c in decoded:
                if '\u4e00' <= c <= '\u9fff':
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0

            if max_consecutive >= 5:  # 5+ consecutive Chinese chars = likely real text
                text_start = offset
                break
        except:
            pass

    if text_start is None:
        # Fallback: lower threshold
        for offset in range(1536, min(len(word_stream), 10000), 128):
            sample = word_stream[offset:offset + 512]
            try:
                decoded = sample.decode('utf-16-le', errors='ignore')
                chinese_count = sum(1 for c in decoded if '\u4e00' <= c <= '\u9fff')
                if chinese_count >= 30:
                    text_start = offset
                    break
            except:
                pass

    if text_start is None:
        return _fallback_text_scan(word_stream)

    # Extract from text_start onwards
    text_bytes = word_stream[text_start:]

    # Find end of meaningful text (long null sequence)
    end_idx = len(text_bytes)
    for i in range(0, len(text_bytes) - 4, 2):
        chunk = text_bytes[i:i + 200]
        if all(b == 0 for b in chunk):
            end_idx = i
            break

    text = text_bytes[:end_idx].decode('utf-16-le', errors='ignore')

    # Clean up
    text = _clean_extracted_text(text)
    return text


def _clean_extracted_text(text):
    """Clean extracted text - remove control chars, normalize whitespace."""
    # Replace common Word control chars
    control_chars = {
        '\x00': ' ',     # null
        '\x01': ' ',     # cell/row mark
        '\x02': '',      # reserved
        '\x03': '',      # end of cell
        '\x04': '',      # end of row
        '\x05': '',      # separator
        '\x07': '',      # cell mark
        '\x08': '',      # backspace
        '\x0b': '\n',    # vertical tab (section break)
        '\x0c': '\n',    # form feed (page break)
        '\x0d': '\n',    # carriage return
        '\x1f': ' ',     # hyphen
        '\x20': ' ',     # space
        '\r': '\n',
    }

    result = []
    for char in text:
        code = ord(char)
        if char in control_chars:
            result.append(control_chars[char])
        elif code < 0x20:
            result.append(' ')
        else:
            result.append(char)

    text = ''.join(result)

    # Normalize whitespace
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # Remove page headers/footers
        if re.match(r'^生物试题\s*第\d+页', line):
            continue
        if re.match(r'^共\d+页', line):
            continue
        # Remove INCLUDEPICTURE fields
        if 'INCLUDEPICTURE' in line or 'MERGEFORMAT' in line:
            continue
        if line:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def _fallback_text_scan(data):
    """Fallback text extraction for non-standard files."""
    if isinstance(data, (bytes, bytearray)):
        raw = data
    else:
        raw = data

    result = bytearray()
    i = 0
    while i < len(raw) - 1:
        char = struct.unpack_from('<H', raw, i)[0]
        if (0x4E00 <= char <= 0x9FFF or  # CJK Unified Ideographs
            0x3000 <= char <= 0x303F or  # CJK Symbols
            0xFF00 <= char <= 0xFFEF or  # Fullwidth Forms
            0x20 <= char <= 0x7E or      # ASCII printable
            char in (0x0D, 0x0A, 0x09) or  # CR, LF, Tab
            char >= 0x2000):             # General punctuation
            result.extend(raw[i:i+2])
            i += 2
        else:
            i += 1

    try:
        text = result.decode('utf-16-le', errors='ignore')
        return _clean_extracted_text(text)
    except:
        return ''


def _fallback_extract_from_data(data):
    """Extract text using alternative methods."""
    return _fallback_text_scan(data)


def parse_exam_questions(text):
    """
    Parse exam questions from extracted text.
    Returns list of question dicts.
    """
    if not text or len(text) < 50:
        return []

    questions = []

    # Normalize the text first
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Find all question boundaries
    # Pattern: number followed by Chinese/ASCII period, then space
    q_pattern = r'(?:^|\n)\s*(\d{1,3})\s*[.．、)）:：]\s*'

    matches = list(re.finditer(q_pattern, text))

    if not matches:
        # Try simpler pattern
        matches = list(re.finditer(r'(?:^|\n)\s*(\d{1,3})\s*[.．、)）]\s*', text))

    for idx, match in enumerate(matches):
        q_num = int(match.group(1))
        start_pos = match.end()

        # End position: start of next question or end of text
        if idx + 1 < len(matches):
            end_pos = matches[idx + 1].start()
        else:
            end_pos = len(text)

        # Extract question block
        q_block = text[start_pos:end_pos].strip()

        if len(q_block) < 5:
            continue

        question = _parse_single_question(q_num, q_block)
        if question:
            questions.append(question)

    return questions


def _parse_single_question(num, block):
    """Parse a single question block with improved multi-strategy parsing."""
    question = {
        'number': num,
        'stem': '',
        'options': {'A': '', 'B': '', 'C': '', 'D': ''},
        'answer': '',
        'type': 'choice',
        'analysis': ''
    }

    lines = [l.strip() for l in block.split('\n') if l.strip()]
    if not lines:
        return None

    # Remove page headers/footers and INCLUDEPICTURE
    cleaned_lines = []
    for line in lines:
        line = re.sub(r'生物试题\s*第\d+页.*', '', line).strip()
        line = re.sub(r'共\d+页.*', '', line).strip()
        line = re.sub(r'INCLUDEPICTURE.*?MERGEFORMAT.*', '', line).strip()
        if line:
            cleaned_lines.append(line)

    if not cleaned_lines:
        return None

    combined = ' '.join(cleaned_lines)
    # Remove leading number and period from combined text
    combined_clean = re.sub(r'^\d{1,3}\s*[.．、)）:：]\s*', '', combined).strip()

    # ========== Strategy 1: Same-line or mixed-line options ==========
    # Patterns:
    #   "A．选项内容 B．选项内容 C．选项内容 D．选项内容" (same line)
    #   "A．选项内容B．选项内容C．选项内容D．选项内容" (no spaces)
    #   Multi-line where each line starts with A./B./C./D.
    #   Mixed: some options on same line, some on separate lines
    
    # First, try to split the combined text into options
    # Pattern: A． or A. or A) or A： followed by content
    # The key is that option markers must be on "boundaries" (start of line or after whitespace/punctuation)
    
    option_marker = r'(?:^|[\s\u3000])([A-D])\s*[.．、)）:：]\s*'
    opt_splits = list(re.finditer(option_marker, combined_clean))
    
    if len(opt_splits) >= 2:
        # Check if these are real options (not just random A/B/C/D occurrences)
        real_options = {}
        for idx_opt, match in enumerate(opt_splits):
            letter = match.group(1)
            start = match.end()
            if idx_opt + 1 < len(opt_splits):
                end = opt_splits[idx_opt + 1].start()
            else:
                end = len(combined_clean)
            content = combined_clean[start:end].strip()
            # Validate: option content should be reasonable length (1-200 chars)
            if content and 1 <= len(content) <= 200:
                real_options[letter] = content
        
        if len(real_options) >= 2:
            # Stem is everything before the first option
            first_opt_start = opt_splits[0].start()
            question['stem'] = combined_clean[:first_opt_start].strip()
            question['stem'] = re.sub(r'\s+', ' ', question['stem']).strip()
            
            for letter in ['A', 'B', 'C', 'D']:
                if letter in real_options:
                    question['options'][letter] = re.sub(r'\s+', ' ', real_options[letter]).strip()
            
            if question['stem'] and len(question['stem']) >= 2:
                # Extract answer
                answer = _extract_answer(combined_clean, combined)
                if answer:
                    question['answer'] = answer
                
                # Determine type: if we have options, it's a choice question
                question['type'] = 'choice' if len(real_options) >= 2 else 'fill'
                return question

    # ========== Strategy 2: Multi-line format (options on their own lines) ==========
    # Look for lines starting with A． B． C． D．
    multi_options = {}
    multi_stem_lines = []
    found_option = False
    last_option_letter = None

    for line in cleaned_lines:
        opt_match = re.match(r'^([A-D])\s*[.．、)）:：]\s*(.*)', line)
        if opt_match:
            found_option = True
            letter = opt_match.group(1)
            content = opt_match.group(2).strip()
            multi_options[letter] = content
            last_option_letter = letter
        elif not found_option:
            multi_stem_lines.append(line)
        else:
            # After an option - might be continuation or answer section
            if last_option_letter and line and not re.match(r'^(?:答案|参考答案|正确答案|解析|分析|【)', line):
                multi_options[last_option_letter] = (multi_options.get(last_option_letter, '') + ' ' + line).strip()

    if len(multi_options) >= 2:
        question['stem'] = re.sub(r'\s+', ' ', ' '.join(multi_stem_lines)).strip()
        question['stem'] = re.sub(r'^\d{1,3}\s*[.．、)）:：]\s*', '', question['stem']).strip()
        for letter in ['A', 'B', 'C', 'D']:
            if letter in multi_options:
                question['options'][letter] = re.sub(r'\s+', ' ', multi_options[letter]).strip()

        if question['stem'] and len(question['stem']) >= 2:
            answer = _extract_answer(combined_clean, combined)
            if answer:
                question['answer'] = answer
            question['type'] = 'choice' if len(multi_options) >= 2 else 'fill'
            return question

    # ========== Strategy 3: Table format (A/B/C/D followed by Chinese text, no separator) ==========
    # Match A/B/C/D directly followed by Chinese characters
    table_opt_pattern = r'([A-D])(?=[\u4e00-\u9fff])'
    opt_positions = [(m.group(1), m.start(), m.end()) for m in re.finditer(table_opt_pattern, combined_clean)]

    if len(opt_positions) >= 2:
        # Deduplicate consecutive same-letter entries
        deduped = []
        prev_letter = None
        for letter, start, end in opt_positions:
            if letter != prev_letter:
                deduped.append((letter, start, end))
                prev_letter = letter
        opt_positions = deduped

        unique_letters = [p[0] for p in opt_positions]

        if len(opt_positions) >= 2 and all(l in 'ABCD' for l in unique_letters):
            for i, (letter, start, end) in enumerate(opt_positions):
                if i + 1 < len(opt_positions):
                    next_start = opt_positions[i + 1][1]
                    opt_content = combined_clean[end:next_start].strip()
                else:
                    opt_content = combined_clean[end:].strip()

                if letter in ['A', 'B', 'C', 'D'] and opt_content and len(opt_content) <= 300:
                    question['options'][letter] = opt_content

            first_opt_start = opt_positions[0][1]
            question['stem'] = combined_clean[:first_opt_start].strip()
            question['stem'] = re.sub(r'\s+', ' ', question['stem']).strip()

            if question['stem'] and len(question['stem']) >= 2:
                answer = _extract_answer(combined_clean, combined)
                if answer:
                    question['answer'] = answer
                question['type'] = 'choice' if len(opt_positions) >= 2 else 'fill'
                return question

    # ========== Strategy 4: Fallback - no options found, treat as fill-in ==========
    question['stem'] = combined_clean.strip()
    question['stem'] = re.sub(r'\s+', ' ', question['stem']).strip()

    answer = _extract_answer(combined_clean, combined)
    if answer:
        question['answer'] = answer

    question['type'] = 'fill'
    return question if len(question['stem']) >= 3 else None


def _extract_answer(combined_clean, original_text):
    """Extract answer from question text using multiple patterns."""
    # Pattern 1: 【答案】A or 【答案】: A
    m = re.search(r'【答案】\s*[:：]?\s*([A-D]+)', combined_clean)
    if m:
        return m.group(1).upper()
    
    # Pattern 2: 答案：A or 答案:A
    m = re.search(r'(?:答案|参考答案|正确答案)\s*[:：]\s*([A-D]+)', combined_clean)
    if m:
        return m.group(1).upper()
    
    # Pattern 3: Answer at end of block like "答案 A" or "A."
    m = re.search(r'(?:答案|参考答案)\s*([A-D]{1,4})\b', combined_clean)
    if m:
        return m.group(1).upper()
    
    # Pattern 4: In original text, search for answer markers
    m = re.search(r'(?:答案|参考答案|正确答案|【答案】)\s*[:：]?\s*([A-D]+)', original_text)
    if m:
        return m.group(1).upper()
    
    return ''


def process_exam_folder(folder_path):
    """
    Process an exam folder: find .doc files, extract text, parse questions.
    Returns dict with exam info and questions.
    """
    folder_name = os.path.basename(folder_path)

    # Find .doc/.docx files
    doc_files = []
    for f in os.listdir(folder_path):
        ext = os.path.splitext(f)[1].lower()
        if ext in ('.doc', '.docx'):
            doc_files.append(os.path.join(folder_path, f))

    if not doc_files:
        return None

    all_questions = []
    raw_text = ''
    for doc_file in doc_files:
        # Extract text
        if doc_file.endswith('.docx'):
            text = _extract_docx_text(doc_file)
        else:
            text = read_doc_text(doc_file)

        if text and len(text) >= 20:
            raw_text = text
            break  # Use first valid document

    if not raw_text or len(raw_text) < 20:
        return {
            'folder_name': folder_name,
            'questions': [],
            'success': False,
            'msg': f'未能从 {folder_name} 中提取有效文本'
        }

    # Parse questions
    questions = parse_exam_questions(raw_text)

    if not questions:
        return {
            'folder_name': folder_name,
            'questions': [],
            'raw_text': raw_text[:2000],
            'success': False,
            'msg': f'未能解析出题目（共提取 {len(raw_text)} 字）'
        }

    return {
        'folder_name': folder_name,
        'questions': questions,
        'raw_text': raw_text,
        'success': True,
        'total_questions': len(questions)
    }


def _extract_docx_text(file_path):
    """Extract text from .docx file using python-docx."""
    try:
        from docx import Document
        doc = Document(file_path)
        text_parts = []
        for para in doc.paragraphs:
            text_parts.append(para.text)
        return '\n'.join(text_parts)
    except ImportError:
        return ''
    except Exception:
        return ''


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = r'D:\paper\大庆中学高三上学期生物期中试题及答案'

    result = process_exam_folder(folder)
    if result:
        print(f"Folder: {result['folder_name']}")
        print(f"Success: {result['success']}")
        print(f"Questions found: {len(result.get('questions', []))}")
        for q in result.get('questions', [])[:5]:
            print(f"\n  Q{q['number']}: {q['stem'][:80]}...")
            print(f"    Options: {q['options']}")
            print(f"    Answer: {q['answer']}")
    else:
        print("No .doc files found")
