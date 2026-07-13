import sys
sys.path.insert(0, 'service')
from extract_questions import read_docx_content, build_image_mapping

docx_path = 'uploads/exams/25云南/2025年高考生物试卷（云南卷）.docx'

print("=== 测试 read_docx_content ===")
paragraphs = read_docx_content(docx_path)
for i, para in enumerate(paragraphs):
    if para['images']:
        print(f"段落 {i}: 图片={para['images']}, 文本='{para['text'][:30]}'")

print("\n=== 测试 build_image_mapping ===")
image_mapping = build_image_mapping(docx_path, '25云南')
for rid, path in image_mapping.items():
    print(f"  {rid} -> {path}")

print("\n=== 检查图片是否匹配 ===")
for i, para in enumerate(paragraphs):
    if para['images']:
        for img_id in para['images']:
            if img_id in image_mapping:
                print(f"段落 {i}: {img_id} -> {image_mapping[img_id]}")
            else:
                print(f"段落 {i}: {img_id} 未找到映射")