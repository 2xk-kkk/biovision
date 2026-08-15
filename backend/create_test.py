# Extract JS and create test files
with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

start = html.find('<script>')
end = html.rfind('</script>')
script_start = html.find('\n', start) + 1
js = html[script_start:end]

# Write full JS to a test file
test_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Full JS Test</title>
</head>
<body>
    <h1>Full JS Test</h1>
    <div id="output"></div>
    <script>
    try {
''' + js + '''
        document.getElementById('output').innerHTML = 'SUCCESS';
    } catch(e) {
        document.getElementById('output').innerHTML = 'ERROR: ' + e.message;
        console.error('Error:', e.message);
    }
    </script>
</body>
</html>'''

with open('d:/15821/biovision/frontend/practice/test-full.html', 'w', encoding='utf-8') as f:
    f.write(test_html)

print("Test file created.")
print(f"JS length: {len(js)} chars")