# Extract JS and test with V8 via Exec
import json

with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

start = html.find('<script>')
end = html.rfind('</script>')
script_start = html.find('\n', start) + 1
js = html[script_start:end]

# For Exec, we need to:
# 1. Replace document/window/alert/etc. with mocks
# 2. Test if the code parses correctly

# Let's create a version that tests parsing by wrapping in a function
# and replacing DOM APIs with stubs

# Simple replacement for DOM APIs
test_js = f"""
// Mock DOM APIs
var document = {{
    getElementById: function(id) {{ return {{ 
        innerHTML: '', 
        textContent: '',
        value: '',
        style: {{}},
        classList: {{ add: function(){{}}, remove: function(){{}} }},
        appendChild: function(){{}},
        addEventListener: function(){{}},
        querySelectorAll: function(){{ return []; }},
        querySelector: function(){{ return null; }},
        append: function(){{}},
        dataset: {{}},
        onclick: null,
        textContent: '',
        appendChild: function(){{}}
    }}; }},
    createElement: function(tag) {{ return {{ 
        className: '', 
        textContent: '',
        innerHTML: '',
        style: {{}},
        setAttribute: function(){{}},
        appendChild: function(){{}},
        onclick: null
    }}; }},
    querySelectorAll: function(sel) {{ return []; }},
    querySelector: function(sel) {{ return null; }}
}};
var window = {{ location: {{ href: '' }}, open: function(){{}} }};
var alert = function() {{}};
var fetch = function() {{ return Promise.resolve(); }};
var atob = function(s) {{ return s; }};

try {{
{js}
    text('JavaScript parsed and executed successfully!');
}} catch(e) {{
    text('Error: ' + e.message);
    text('Stack: ' + e.stack);
}}
"""

print(test_js[:200])
print("...")
print(f"Total test JS length: {len(test_js)} chars")

# Save to a file for inspection
with open('d:/15821/biovision/backend/test_js_syntax.txt', 'w', encoding='utf-8') as f:
    f.write(test_js)

print("Saved to test_js_syntax.txt")