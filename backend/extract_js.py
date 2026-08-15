import re

# Read the HTML file
with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract the JavaScript
start = html.find('<script>')
end = html.rfind('</script>')
script_start = html.find('\n', start) + 1
js = html[script_start:end]

# Write the JavaScript to a separate file
with open('d:/15821/biovision/frontend/practice/exam-practice.js', 'w', encoding='utf-8') as f:
    f.write(js)

# Replace the inline script with an external script reference
new_html = html[:start] + '<script src="exam-practice.js"></script>' + html[end + len('</script>'):]

# Write the modified HTML
with open('d:/15821/biovision/frontend/practice/exam-practice.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"Extracted JavaScript to exam-practice.js ({len(js)} chars)")
print(f"Modified exam-practice.html to use external script")
print(f"New HTML size: {len(new_html)} chars")