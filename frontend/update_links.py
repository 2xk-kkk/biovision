import re
import os

# 定义要修改的链接映射
link_mapping = {
    'PPT/main.html': 'ppt',
    'practice/main.html': 'practice',
    '3D model/main.html': '3d',
    'forum/main.html': 'forum',
    'index.html': '_self'
}

# 要处理的目录
frontend_dir = r'c:\Users\MECHREVO\OneDrive\Desktop\mmmmm\biovision\frontend'

# 要处理的HTML文件列表
html_files = [
    os.path.join(frontend_dir, 'index.html'),
    os.path.join(frontend_dir, 'forum', 'main.html'),
    os.path.join(frontend_dir, 'PPT', 'main.html'),
    os.path.join(frontend_dir, 'practice', 'main.html'),
    os.path.join(frontend_dir, '3D model', 'main.html')
]

def update_links_in_file(file_path):
    """在文件中更新链接"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 保存原始内容以便对比
        original_content = content
        
        for href_path, target_name in link_mapping.items():
            # 使用更精确的正则表达式处理
            def process_tag(match):
                tag = match.group(0)
                href = match.group(1)
                
                # 移除现有的 target 属性
                tag = re.sub(r'\s+target="[^"]*"', '', tag)
                
                # 检查是否有其他属性（通过检查是否有多个 = 符号）
                if tag.count('=') > 1:
                    # 有其他属性，在 href 之后添加 target
                    new_tag = tag.replace(f'href="{href}"', f'href="{href}" target="{target_name}"')
                else:
                    # 只有 href 属性
                    new_tag = tag.replace('>', f' target="{target_name}">')
                
                return new_tag
            
            # 匹配包含该 href 的 a 标签
            pattern = rf'<a[^>]*href="([^"]*{re.escape(href_path)})"[^>]*>'
            content = re.sub(pattern, process_tag, content)
        
        # 只在内容发生变化时才写入文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Updated: {file_path}')
        else:
            print(f'No changes needed: {file_path}')
            
    except Exception as e:
        print(f'Error processing {file_path}: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    for html_file in html_files:
        if os.path.exists(html_file):
            update_links_in_file(html_file)
        else:
            print(f'File not found: {html_file}')
