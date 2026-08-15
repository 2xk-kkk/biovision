# Split JS into two halves and test
with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

start = html.find('<script>')
end = html.rfind('</script>')
script_start = html.find('\n', start) + 1
js = html[script_start:end]

lines = js.split('\n')
mid = len(lines) // 2

# First half
first_half = '\n'.join(lines[:mid])
second_half = '\n'.join(lines[mid:])

print(f"Total lines: {len(lines)}")
print(f"First half: lines 1-{mid} ({len(first_half)} chars)")
print(f"Second half: lines {mid+1}-{len(lines)} ({len(second_half)} chars)")

# Create test files that wrap each half in a try-catch
for idx, (name, half) in enumerate([(1, first_half), (2, second_half)], 1):
    test_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Test Half {idx}</title>
</head>
<body>
    <h1>Test Half {idx}</h1>
    <div id="output">Testing...</div>
    <script>
    var document = {{ 
        getElementById: function(id) {{ return {{ 
            innerHTML: '', textContent: '', value: '',
            style: {{}}, classList: {{ add: function(){{}}, remove: function(){{}} }},
            appendChild: function(){{}}, addEventListener: function(){{}},
            querySelectorAll: function(){{ return []; }},
            onclick: null, textContent: ''
        }}; }},
        createElement: function(tag) {{ return {{ 
            className: '', textContent: '', innerHTML: '',
            style: {{}}, setAttribute: function(){{}},
            appendChild: function(){{}}, onclick: null
        }}; }},
        querySelectorAll: function(sel) {{ return []; }},
        querySelector: function(sel) {{ return null; }}
    }};
    var window = {{ location: {{ href: '' }}, open: function(){{}} }};
    var alert = function() {{}};
    var fetch = function() {{ return Promise.resolve(); }};
    var atob = function(s) {{ return s; }};
    
    try {{
{half}
        document.getElementById('output').innerHTML = 'SUCCESS';
    }} catch(e) {{
        document.getElementById('output').innerHTML = 'ERROR: ' + e.message;
    }}
    </script>
</body>
</html>'''
    
    with open(f'd:/15821/biovision/frontend/practice/test-half{idx}.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print(f"Created test-half{idx}.html")

print("Done!")