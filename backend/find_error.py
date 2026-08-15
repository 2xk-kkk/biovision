# Find the exact error in Q2
with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

start = html.find('<script>')
end = html.rfind('</script>')
script_start = html.find('\n', start) + 1
js = html[script_start:end]

lines = js.split('\n')
first_half = lines[:342]

mock_setup = """var document = { 
    getElementById: function(id) { return { 
        innerHTML: '', textContent: '', value: '',
        style: {}, classList: { add: function(){}, remove: function(){} },
        appendChild: function(){}, addEventListener: function(){},
        querySelectorAll: function(){ return []; },
        onclick: null, textContent: ''
    }; },
    createElement: function(tag) { return { 
        className: '', textContent: '', innerHTML: '',
        style: {}, setAttribute: function(){},
        appendChild: function(){}, onclick: null
    }; },
    querySelectorAll: function(sel) { return []; },
    querySelector: function(sel) { return null; }
};
var window = { location: { href: '' }, open: function(){} };
var alert = function(){};
var fetch = function() { return Promise.resolve(); };
var atob = function(s) { return s; };
"""

# Add lines one by one to find the error
for test_lines_count in range(86, 171, 5):
    test_lines = first_half[:test_lines_count]
    test_js = '\n'.join(test_lines)
    
    test_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Test Lines 1-{test_lines_count}</title>
</head>
<body>
    <h1>Test Lines 1-{test_lines_count}</h1>
    <div id="output">Testing...</div>
    <script>
{mock_setup}
try {{
{test_js}
    document.getElementById('output').innerHTML = 'SUCCESS';
}} catch(e) {{
    document.getElementById('output').innerHTML = 'ERROR: ' + e.message;
}}
    </script>
</body>
</html>'''
    
    filename = f'd:/15821/biovision/frontend/practice/test-lines-{test_lines_count}.html'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(test_html)

print(f"Created test files for line counts: 86, 91, 96, ..., 170")
print(f"Total files: {len(range(86, 171, 5))}")

# Also show what's at each 5-line boundary
for test_lines_count in range(86, 171, 5):
    line_content = first_half[test_lines_count-1] if test_lines_count <= len(first_half) else '(end)'
    print(f"\nLine {test_lines_count}: {line_content.strip()[:100]}")