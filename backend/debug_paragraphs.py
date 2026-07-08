import zipfile
import xml.etree.ElementTree as ET

NSMAP = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'v': 'urn:schemas-microsoft-com:vml'
}

docx_path = 'uploads/exams/25云南/2025年高考生物试卷（云南卷）.docx'

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
                for imagedata in pict.iter('{' + NSMAP['v'] + '}imagedata'):
                    rid = imagedata.get('{' + NSMAP['r'] + '}id')
                    if rid:
                        images.append(rid)
            
            if text_content.strip() or images:
                text_display = text_content[:50] if len(text_content) > 50 else text_content
                print(f'段落{i}: 文本="{text_display}", 图片={images}')