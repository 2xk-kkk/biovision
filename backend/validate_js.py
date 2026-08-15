# Try to validate JavaScript syntax
import re

# Read the HTML file
with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find script block
start = html.find('<script>')
end = html.rfind('</script>')
if start != -1 and end != -1:
    # Find the end of the <script> tag
    script_start = html.find('\n', start) + 1
    script_content = html[script_start:end]
    
    # Write to temp JS file
    with open('d:/15821/biovision/backend/temp_check.js', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"Extracted {len(script_content)} chars of JavaScript")
    
    # Check for issues line by line
    lines = script_content.split('\n')
    
    # Track brace/paren/bracket balance
    brace = 0
    paren = 0
    bracket = 0
    
    for i, line in enumerate(lines, 1):
        # Skip strings and template literals for basic counting
        # Simple approach: just count all occurrences
        for ch in line:
            if ch == '{': brace += 1
            elif ch == '}': brace -= 1
            elif ch == '(': paren += 1
            elif ch == ')': paren -= 1
            elif ch == '[': bracket += 1
            elif ch == ']': bracket -= 1
        
        # Print lines where balance goes negative
        if brace < 0 or paren < 0 or bracket < 0:
            print(f"PROBLEM at line {i}: braces={brace}, parens={paren}, brackets={bracket}")
            print(f"  Content: {line[:120]}")
            print()
            break
    
    if brace == 0 and paren == 0 and bracket == 0:
        print("Final state is balanced: braces=0, parens=0, brackets=0")
    else:
        print(f"Final state: braces={brace}, parens={paren}, brackets={bracket}")
    
    # Try Node.js
    import subprocess
    try:
        result = subprocess.run(
            ['node', '--check', 'd:/15821/biovision/backend/temp_check.js'],
            capture_output=True, text=True, timeout=10
        )
        print(f"\nNode syntax check: exit={result.returncode}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        if result.returncode == 0:
            print("JavaScript syntax is VALID!")
    except FileNotFoundError:
        print("Node.js not installed, skipping syntax check")
    except Exception as e:
        print(f"Error running node: {e}")
else:
    print("No script block found")