import zipfile
import xml.etree.ElementTree as ET
import re

NSMAP = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'v': 'urn:schemas-microsoft-com:vml'
}

docx_path = 'uploads/exams/25云南/2025年高考生物试卷（云南卷）.docx'

print("=== 检查 relationships 文件 ===")
with zipfile.ZipFile(docx_path, 'r') as z:
    if 'word/_rels/document.xml.rels' in z.namelist():
        print("relationships 文件存在")
        with z.open('word/_rels/document.xml.rels') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            ns = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
            
            for rel in root.iter('{' + ns['r'] + '}Relationship'):
                rid = rel.get('Id')
                target = rel.get('Target')
                if target and target.startswith('media/'):
                    print(f"  ID={rid}, Target={target}")
    else:
        print("relationships 文件不存在")

print("\n=== 检查段落中的图片 ===")
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
                        images.append(f"pict:{rid}")
            
            for drawing in para.iter('{' + NSMAP['w'] + '}drawing'):
                for blip in drawing.iter('{' + NSMAP['w'] + '}blip'):
                    embed = blip.get('{' + NSMAP['r'] + '}embed')
                    if embed:
                        images.append(f"drawing:{embed}")
            
            if images:
                text_display = text_content[:40] if len(text_content) > 40 else text_content
                print(f"段落 {i}: 图片={images}, 文本='{text_display}'")

print("\n=== 检查 media 文件 ===")
with zipfile.ZipFile(docx_path, 'r') as z:
    for name in z.namelist():
        if name.startswith('word/media/'):
            print(f"  {name}")