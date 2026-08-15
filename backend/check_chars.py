# Check for unusual characters in JavaScript
with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

start = html.find('<script>')
end = html.rfind('</script>')
script_start = html.find('\n', start) + 1
js = html[script_start:end]

# Check for non-ASCII characters that might cause issues
lines = js.split('\n')
for i, line in enumerate(lines, 1):
    for j, ch in enumerate(line):
        code = ord(ch)
        if code > 127 and code not in range(0x4e00, 0x9fff+1) and code not in range(0x3000, 0x303f+1) and ch not in '（）《》""''！？：；、·':
            # Check if it's a common CJK character or punctuation
            if not (0x4e00 <= code <= 0x9fff or 0x3000 <= code <= 0x303f or 
                    0xff00 <= code <= 0xffef or 0x2000 <= code <= 0x206f or
                    ch in '，。！？；：""''（）《》【】、…—·'):
                print(f"Line {i}, pos {j}: U+{code:04X} {ch!r} - {line[:80]}")

print("\nDone checking unusual characters.")

# Also check for zero-width characters
for i, line in enumerate(lines, 1):
    for j, ch in enumerate(line):
        code = ord(ch)
        if code in [0x200b, 0x200c, 0x200d, 0xFEFF, 0x2060]:  # Zero-width characters
            print(f"Line {i}, pos {j}: Zero-width character U+{code:04X}")

print("\nDone checking zero-width characters.")