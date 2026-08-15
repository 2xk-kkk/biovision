# Extract and analyze the JavaScript for syntax issues
import re

with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find script block
start = html.find('<script>')
end = html.rfind('</script>')
script_start = html.find('\n', start) + 1
js = html[script_start:end]

# Look for potential issues
lines = js.split('\n')
print(f"Total script lines: {len(lines)}")

# Check template literals
for i, line in enumerate(lines, 1):
    # Count backticks
    bt = line.count('`')
    if bt % 2 != 0:
        print(f"Line {i}: Odd backticks ({bt}): {line.strip()[:120]}")

# Check for arrow functions with potential issues
for i, line in enumerate(lines, 1):
    if '=>' in line:
        # Check for problematic arrow function patterns
        stripped = line.strip()
        # Pattern: (params) => { ... } should be fine
        # But param => { ... } without parens should also be fine
        # Check for missing closing paren
        if '(' in stripped and ')' not in stripped and '{' in stripped:
            print(f"Line {i}: Possible missing closing paren: {stripped[:120]}")

print("\nDone checking.")