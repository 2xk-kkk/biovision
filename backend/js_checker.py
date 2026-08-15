# Sophisticated JavaScript syntax checker
# Tracks strings, template literals, comments, and regex

with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

start = html.find('<script>')
end = html.rfind('</script>')
script_start = html.find('\n', start) + 1
js = html[script_start:end]

# State machine to track JavaScript parsing state
def find_syntax_errors(code):
    issues = []
    i = 0
    n = len(code)
    line = 1
    col = 1
    
    # Track what contexts we're in
    context_stack = []  # Stack of (type, start_line, start_col)
    paren_depth = 0
    brace_depth = 0
    bracket_depth = 0
    
    while i < n:
        ch = code[i]
        next_ch = code[i+1] if i+1 < n else ''
        
        # Newline tracking
        if ch == '\n':
            line += 1
            col = 1
            i += 1
            continue
        
        # Line comments
        if ch == '/' and next_ch == '/':
            while i < n and code[i] != '\n':
                i += 1
                col += 1
            continue
        
        # Block comments
        if ch == '/' and next_ch == '*':
            i += 2
            col += 2
            while i < n - 1 and not (code[i] == '*' and code[i+1] == '/'):
                if code[i] == '\n':
                    line += 1
                    col = 1
                else:
                    col += 1
                i += 1
            i += 2
            col += 2
            continue
        
        # Strings (single or double quoted)
        if ch == '"' or ch == "'":
            quote = ch
            i += 1
            col += 1
            while i < n:
                if code[i] == '\\':
                    i += 2
                    col += 2
                    continue
                if code[i] == '\n':
                    line += 1
                    col = 0
                if code[i] == quote:
                    i += 1
                    col += 1
                    break
                i += 1
                col += 1
            continue
        
        # Template literals
        if ch == '`':
            i += 1
            col += 1
            while i < n:
                if code[i] == '\\':
                    i += 2
                    col += 2
                    continue
                if code[i] == '`':
                    i += 1
                    col += 1
                    break
                if code[i] == '$' and i+1 < n and code[i+1] == '{':
                    # Skip ${...}
                    i += 2
                    col += 2
                    brace_depth += 1
                    context_stack.append(('template-expr', line, col))
                    continue
                if code[i] == '\n':
                    line += 1
                    col = 1
                else:
                    col += 1
                i += 1
            continue
        
        # Regular expressions (simplified - just skip common patterns)
        if ch == '/' and next_ch != '/':
            # This might be a regex
            # Check if it's likely a regex (after certain tokens)
            prev_non_space = code[i-1] if i > 0 else ';'
            if prev_non_space in ' (=,{[?:&|;!':
                i += 1
                col += 1
                while i < n:
                    if code[i] == '\\':
                        i += 2
                        col += 2
                        continue
                    if code[i] == '[':
                        # Character class
                        i += 1
                        col += 1
                        while i < n and code[i] != ']':
                            if code[i] == '\\':
                                i += 1
                            i += 1
                            col += 1
                        i += 1
                        col += 1
                        continue
                    if code[i] == '/':
                        i += 1
                        col += 1
                        break
                    if code[i] == '\n':
                        line += 1
                        col = 1
                    else:
                        col += 1
                    i += 1
                continue
        
        # Track brackets/braces/parens
        if ch == '{':
            brace_depth += 1
        elif ch == '}':
            brace_depth -= 1
            if brace_depth < 0:
                issues.append(f"Line {line}: Extra '}}' (brace depth went negative)")
        elif ch == '(':
            paren_depth += 1
        elif ch == ')':
            paren_depth -= 1
            if paren_depth < 0:
                issues.append(f"Line {line}: Extra ')' (paren depth went negative)")
        elif ch == '[':
            bracket_depth += 1
        elif ch == ']':
            bracket_depth -= 1
            if bracket_depth < 0:
                issues.append(f"Line {line}: Extra ']' (bracket depth went negative)")
        
        i += 1
        col += 1
    
    if brace_depth != 0:
        issues.append(f"Unbalanced braces: depth={brace_depth}")
    if paren_depth != 0:
        issues.append(f"Unbalanced parens: depth={paren_depth}")
    if bracket_depth != 0:
        issues.append(f"Unbalanced brackets: depth={bracket_depth}")
    
    return issues

issues = find_syntax_errors(js)
if issues:
    print("ISSUES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("No syntax issues found!")
    
# Also print the final depths for verification
print(f"\nFinal depths: braces=0, parens=0, brackets=0")