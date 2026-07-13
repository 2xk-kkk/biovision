import zipfile
import xml.etree.ElementTree as ET

NSMAP = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
}

docx_path = 'uploads/exams/25四川/2025年高考生物试卷（四川卷）.docx'

print("=== 检查文档结构 ===")
with zipfile.ZipFile(docx_path, 'r') as z:
    with z.open('word/document.xml') as f:
        tree = ET.parse(f)
        root = tree.getroot()
        
        print(f"根标签: {root.tag}")
        print(f"根属性: {root.attrib}")
        print(f"\n直接子节点:")
        for i, child in enumerate(root):
            print(f"  [{i}] {child.tag}")
        
        body = None
        for child in root:
            if child.tag == '{' + NSMAP['w'] + '}body':
                body = child
                break
        
        if body:
            print(f"\nbody直接子节点:")
            for i, child in enumerate(body):
                print(f"  [{i}] {child.tag}")
                
                if child.tag == '{' + NSMAP['w'] + '}p':
                    text = ''
                    for t in child.iter('{' + NSMAP['w'] + '}t'):
                        if t.text:
                            text += t.text
                    print(f"    文本: {text[:50]}")
        else:
            print("未找到body")