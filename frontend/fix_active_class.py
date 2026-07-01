import re
import os

# 定义每个页面的 active 类应该在哪个链接上
active_mapping = {
    'PPT/main.html': 'PPT快搭',
    'practice/main.html': '每日训练',
    '3D model/main.html': '可视学习',
    'forum/main.html': '论坛'
}

# 要处理的目录
frontend_dir = r'c:\Users\MECHREVO\OneDrive\Desktop\mmmmm\biovision\frontend'

def fix_active_in_file(file_path, active_text):
    """在文件中修复 active 类的位置"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 第一步：移除所有 nav-link 上的 active 类
        content = re.sub(r'class="nav-link active"', 'class="nav-link"', content)
        content = re.sub(r'class="nav-link active "', 'class="nav-link"', content)
        
        # 第二步：给包含 active_text 的 nav-link 添加 active 类
        def add_active(match):
            tag = match.group(0)
            if 'class=' in tag:
                # 替换 class 属性，添加 active
                tag = re.sub(r'class="([^"]*)"', r'class="\1 active"', tag)
            else:
                # 没有 class 属性，添加一个
                tag = tag.replace('>', ' class="nav-link active">')
            return tag
        
        # 匹配包含 active_text 的 a 标签
        pattern = rf'<a[^>]*class="[^"]*nav-link[^"]*"[^>]*>{re.escape(active_text)}</a>'
        content = re.sub(pattern, add_active, content)
        
        # 如果上面的没匹配到，尝试更宽松的模式
        if content == original_content:
            pattern = rf'<a[^>]*>{re.escape(active_text)}</a>'
            content = re.sub(pattern, add_active, content)
        
        # 写入文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Fixed active class in: {file_path}')
        else:
            print(f'No changes needed: {file_path}')
            
    except Exception as e:
        print(f'Error processing {file_path}: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # 修复 PPT/main.html
    ppt_path = os.path.join(frontend_dir, 'PPT', 'main.html')
    fix_active_in_file(ppt_path, 'PPT快搭')
