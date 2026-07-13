import zipfile
import xml.etree.ElementTree as ET
import os
import re

NSMAP = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'v': 'urn:schemas-microsoft-com:vml'
}

docx_path = 'uploads/exams/25云南/2025年高考生物试卷（云南卷）.docx'

print("=== 检查 document.xml 结构 ===")
with zipfile.ZipFile(docx_path, 'r') as z:
    with z.open('word/document.xml') as f:
        tree = ET.parse(f)
        root = tree.getroot()
        
        for i, para in enumerate(root.iter('{' + NSMAP['w'] + '}p')):
            text_content = ''
            images = []
            
            for run in para.iter('{' + NSMAP['w'] + '}r'):
                for t in run.iter('{' + NSMAP['w'] + '}t'):
                    if t.text:
                        text_content += t.text
            
            for pict in para.iter('{' + NSMAP['w'] + '}pict'):
                print(f"  段落{i} 找到 pict 标签")
                for imagedata in pict.iter('{' + NSMAP['v'] + '}imagedata'):
                    rid = imagedata.get('{' + NSMAP['r'] + '}id')
                    if rid:
                        images.append(f"pict:{rid}")
            
            for drawing in para.iter('{' + NSMAP['w'] + '}drawing'):
                print(f"  段落{i} 找到 drawing 标签")
                for blip in drawing.iter('{' + NSMAP['w'] + '}blip'):
                    embed = blip.get('{' + NSMAP['r'] + '}embed')
                    if embed:
                        images.append(f"drawing:{embed}")
            
            if images or '选择题' in text_content or re.match(r'^\d+[\.．、]', text_content.strip()):
                text_display = text_content[:50] if len(text_content) > 50 else text_content
                print(f"段落 {i}: img={len(images)} [{images}] - '{text_display}'")

print("\n=== 检查命名空间 ===")
with zipfile.ZipFile(docx_path, 'r') as z:
    with z.open('word/document.xml') as f:
        content = f.read().decode('utf-8')[:2000]
        print(content)