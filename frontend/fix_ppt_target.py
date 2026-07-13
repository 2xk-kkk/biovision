import re
import os

file_path = r'c:\Users\MECHREVO\OneDrive\Desktop\mmmmm\biovision\frontend\PPT\main.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 修复 PPT 快搭链接的 target 属性
    content = re.sub(r'target="_blank"', 'target="_self"', content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Fixed target attribute for PPT link')
    else:
        print('No changes needed for target attribute')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
