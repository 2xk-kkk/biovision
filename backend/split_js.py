# Split JS into chunks and create test files
with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

start = html.find('<script>')
end = html.rfind('</script>')
script_start = html.find('\n', start) + 1
js = html[script_start:end]

lines = js.split('\n')
total_lines = len(lines)
print(f"Total lines: {total_lines}")

# Split into chunks of 50 lines
chunk_size = 50
chunks = []
for i in range(0, total_lines, chunk_size):
    chunk = lines[i:i+chunk_size]
    chunks.append((i+1, min(i+chunk_size, total_lines), '\n'.join(chunk)))

# Create test files for each chunk
for idx, (start_line, end_line, chunk_js) in enumerate(chunks):
    test_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Test Chunk {idx+1} (lines {start_line}-{end_line})</title>
</head>
<body>
    <h1>Test Chunk {idx+1} (lines {start_line}-{end_line})</h1>
    <div id="output">Testing...</div>
    <script>
    try {{
{chunk_js}
        document.getElementById('output').innerHTML = 'SUCCESS';
    }} catch(e) {{
        document.getElementById('output').innerHTML = 'ERROR: ' + e.message;
    }}
    </script>
</body>
</html>'''
    
    with open(f'd:/15821/biovision/frontend/practice/test-chunk{idx+1}.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print(f"Created test-chunk{idx+1}.html (lines {start_line}-{end_line}, {len(chunk_js)} chars)")

print("Done creating test files.")