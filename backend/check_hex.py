# Check for invisible/special characters in the JavaScript
with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'rb') as f:
    content = f.read()

# Find the script section
start_marker = b'<script>\n'
end_marker = b'\n    </script>'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find script markers")
    # Try alternative
    start_idx = content.find(b'<script>')
    end_idx = content.find(b'</script>')
    print(f"Alt: start={start_idx}, end={end_idx}")
    if start_idx != -1 and end_idx != -1:
        # Find the newline after <script>
        nl_idx = content.find(b'\n', start_idx)
        print(f"Newline after script: {nl_idx}")
        script_bytes = content[nl_idx+1:end_idx]
    else:
        print("Cannot find script block!")
        exit()
else:
    script_bytes = content[start_idx + len(start_marker):end_idx]

# Decode and analyze
js = script_bytes.decode('utf-8')

# Check for unusual bytes
print(f"Script size: {len(script_bytes)} bytes, {len(js)} chars")

# Look for non-standard whitespace or control characters
for i, b in enumerate(script_bytes):
    if b < 0x20 and b not in (0x09, 0x0A, 0x0D):  # tab, newline, carriage return
        line_num = js[:i].count('\n') + 1
        print(f"  Control byte 0x{b:02X} at position {i}, line {line_num}")
        context = script_bytes[max(0,i-10):i+10]
        print(f"    Context: {context}")

print("\nDone checking for control bytes.")

# Also check the first few bytes after <script>
print(f"\nFirst 50 bytes after <script>:")
print(script_bytes[:50])
print(f"\nLast 50 bytes before </script>:")
print(script_bytes[-50:])