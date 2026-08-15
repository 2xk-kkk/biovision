import re
import sys

# Read the HTML file
with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract all script blocks
scripts = re.findall(r'<script>([\s\S]*?)</script>', html)

print(f"Found {len(scripts)} script blocks")

# Check each script for basic issues
for i, script in enumerate(scripts):
    # Skip external script references
    if script.strip().startswith('src='):
        continue
    
    lines = script.split('\n')
    print(f"\nScript block {i}: {len(script)} chars, {len(lines)} lines")
    
    # Check for unbalanced braces/parentheses
    brace_count = 0
    paren_count = 0
    bracket_count = 0
    
    for line_num, line in enumerate(lines, 1):
        in_template = False
        for char in line:
            if char == '`':
                in_template = not in_template
            elif not in_template:
                if char == '{': brace_count += 1
                elif char == '}': brace_count -= 1
                elif char == '(': paren_count += 1
                elif char == ')': paren_count -= 1
                elif char == '[': bracket_count += 1
                elif char == ']': bracket_count -= 1
        
        print(f"  Final state: braces={brace_count}, parens={paren_count}, brackets={bracket_count}")
        
        if brace_count != 0 or paren_count != 0 or bracket_count != 0:
            print(f"  WARNING: Unbalanced delimiters!")
            
            # Try to find where
            brace_count = 0
            paren_count = 0
            bracket_count = 0
            for line_num, line in enumerate(lines, 1):
                for char in line:
                    if char == '{': brace_count += 1
                    elif char == '}': brace_count -= 1
                    elif char == '(': paren_count += 1
                    elif char == ')': paren_count -= 1
                    elif char == '[': bracket_count += 1
                    elif char == ']': bracket_count -= 1
                if brace_count < 0 or paren_count < 0 or bracket_count < 0:
                    print(f"  First negative at line {line_num}: braces={brace_count}, parens={paren_count}, brackets={bracket_count}")
                    print(f"    Content: {line[:80]}")
                    break