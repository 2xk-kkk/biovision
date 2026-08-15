# Check for lookalike characters
with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

start = html.find('<script>')
end = html.rfind('</script>')
script_start = html.find('\n', start) + 1
js = html[script_start:end]

lines = js.split('\n')
for i, line in enumerate(lines, 1):
    for j, ch in enumerate(line):
        code = ord(ch)
        # Check for lookalike characters that might cause issues
        # Fullwidth parens: U+FF08 (（) and U+FF09 (）)
        # Greek/Fake parens
        if ch in '（）':
            print(f"Line {i}, pos {j}: Fullwidth paren U+{code:04X} {ch!r}")
        # Check for other potential issues
        # Zero-width space: U+200B
        if code == 0x200b:
            print(f"Line {i}, pos {j}: Zero-width space")

# Also check for mismatched quote characters
# Look for lines with both single and double quotes in template literals
for i, line in enumerate(lines, 1):
    # Check for potential issues with template literals containing complex expressions
    if '=>' in line and '`' in line:
        print(f"Line {i}: Arrow function with template literal: {line.strip()[:100]}")

print("\nDone.")