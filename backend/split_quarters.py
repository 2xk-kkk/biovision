# Split first half into quarters
with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

start = html.find('<script>')
end = html.rfind('</script>')
script_start = html.find('\n', start) + 1
js = html[script_start:end]

lines = js.split('\n')
first_half = lines[:342]
total = len(first_half)
quarter = total // 4

# Create mock DOM wrapper
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
try {
"""

mock_end = """
    document.getElementById('output').innerHTML = 'SUCCESS';
} catch(e) {
    document.getElementById('output').innerHTML = 'ERROR: ' + e.message;
}
"""

# Test each quarter
for q in range(4):
    start_line = q * quarter
    end_line = (q + 1) * quarter if q < 3 else total
    quarter_lines = first_half[start_line:end_line]
    quarter_js = '\n'.join(quarter_lines)
    
    test_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Test Quarter {q+1}</title>
</head>
<body>
    <h1>Test Quarter {q+1}</h1>
    <div id="output">Testing...</div>
    <script>
{mock_setup}
{quarter_js}
{mock_end}
    </script>
</body>
</html>'''
    
    with open(f'd:/15821/biovision/frontend/practice/test-q{q+1}.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print(f"Created test-q{q+1}.html (first half lines {start_line+1}-{end_line})")

print("Done!")