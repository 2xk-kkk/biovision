# Binary search for the error
# Create test files with different line ranges and test them

import subprocess
import time

with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

start = html.find('<script>')
end = html.rfind('</script>')
script_start = html.find('\n', start) + 1
js = html[script_start:end]

lines = js.split('\n')
total = len(lines)

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

mock_end = """
try {
    var result = 'NO_ERROR';
    // Force a syntax error check by wrapping in eval
    // Actually, we just need to check if the script above parses correctly
    document.getElementById('output').innerHTML = 'SUCCESS';
} catch(e) {
    document.getElementById('output').innerHTML = 'RUNTIME_ERROR: ' + e.message;
}
"""

# Test with different end points
# The issue is that SyntaxError prevents parsing entirely
# So we need to test chunks that are self-contained

# Let's try a different approach: just run the code and see if we get SYNTAX error
# We'll test by creating HTML files that run the JS and report errors

test_cases = []

# Test specific function ranges
functions_to_test = [
    (1, 85, "Basic variables"),
    (86, 170, "loadExams template literal part 1"),
    (171, 255, "loadExams template literal part 2 + updateStats"),
    (256, 342, "previewExam part 1"),
    (343, 425, "previewExam part 2"),
    (426, 510, "previewExam part 3 + parseImages"),
    (511, 595, "parseOptions + uploadFile"),
    (596, 685, "uploadFile + loadUserInfo"),
]

for start_line, end_line, description in functions_to_test:
    test_lines = lines[start_line-1:end_line]
    test_js = '\n'.join(test_lines)
    
    # We need to make this a complete script
    # The issue is that these chunks may have unbalanced braces
    
    test_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Test {start_line}-{end_line}: {description}</title>
</head>
<body>
    <h1>Test {start_line}-{end_line}: {description}</h1>
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
    
    filename = f'd:/15821/biovision/frontend/practice/test-func-{start_line}-{end_line}.html'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print(f"Created {filename}: {description}")

print("\nDone creating test files!")
print("\nImportant: The issue is that SyntaxError prevents parsing of the entire script block.")
print("We need to find which specific lines cause the error.")
print("\nLet me also test the FULL script with just try-catch (for runtime errors):")

# Full script test
full_test_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Full Script Test</title>
</head>
<body>
    <h1>Full Script Test</h1>
    <div id="output">Testing...</div>
    <script>
{mock_setup}
// Run the full script - we know it has SyntaxError, so this won't work
// But let's try to load it dynamically
try {{
    // Just test parsing by using Function constructor
    var fn = new Function("{js.replace(chr(34), chr(92)+chr(34)).replace(chr(10), chr(92)+'n')}");
    document.getElementById('output').innerHTML = 'PARSE_SUCCESS';
}} catch(e) {{
    document.getElementById('output').innerHTML = 'PARSE_ERROR: ' + e.message;
}}
    </script>
</body>
</html>'''

with open('d:/15821/biovision/frontend/practice/test-full-parse.html', 'w', encoding='utf-8') as f:
    f.write(full_test_html)

print("Created test-full-parse.html")