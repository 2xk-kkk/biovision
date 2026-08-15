# Create systematic test variants
import os

base_mock = '''var document = { 
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
'''

# Test 1: Original (reproduces error)
test1 = '''
try {
    const exams = [{id: 1, name: "test", grade: "高一", region: "学校", exam_type: "模拟题", has_answers: true, question_count: 10, file_count: 1, files: []}];
    const HOT_UNIVERSITIES = ['人大附中', '上海中学', '衡水中学'];
    const container = document.getElementById('output');
    
    container.innerHTML = exams.map((exam, index) => {
        const gradeLabel = exam.grade || exam.year || '';
        const gradeColor = exam.grade === '高一' ? '#10b981' : '#f59e0b';
        return `
            <div class="exam-card">
                ${gradeLabel ? `<span class="grade-badge" style="background:${gradeColor}">${gradeLabel}</span>` : ''}
                ${exam.region || ''} ${exam.exam_type || '模拟题'}
                <button class="btn-preview" onclick="previewExam(${exam.id || 'null'}, '${exam.name.replace(/'/g, "\\'")}')">预览</button>
                ${exam.has_answers ? 
                    `<button class="btn-quiz" onclick="startQuiz(${exam.id})">开始练习</button>` : 
                    `<button class="btn-quiz" onclick="parseExam('${exam.name.replace(/'/g, "\\'")}')">解析</button>`
                }
            </div>
        `;
    }).join('');
    
    document.getElementById('output').innerHTML = 'SUCCESS';
} catch(e) {
    document.getElementById('output').innerHTML = 'ERROR: ' + e.message;
}
'''

# Test 2: Without the regex in onclick
test2 = '''
try {
    const exams = [{id: 1, name: "test", grade: "高一", region: "学校", exam_type: "模拟题", has_answers: true, question_count: 10, file_count: 1, files: []}];
    const HOT_UNIVERSITIES = ['人大附中', '上海中学', '衡水中学'];
    const container = document.getElementById('output');
    
    container.innerHTML = exams.map((exam, index) => {
        const gradeLabel = exam.grade || exam.year || '';
        const gradeColor = exam.grade === '高一' ? '#10b981' : '#f59e0b';
        const examName = exam.name.replace(/'/g, "\\\\'");
        return `
            <div class="exam-card">
                ${gradeLabel ? `<span class="grade-badge" style="background:${gradeColor}">${gradeLabel}</span>` : ''}
                ${exam.region || ''} ${exam.exam_type || '模拟题'}
                <button class="btn-preview" onclick="previewExam(${exam.id || 'null'}, '${examName}')">预览</button>
                ${exam.has_answers ? 
                    `<button class="btn-quiz" onclick="startQuiz(${exam.id})">开始练习</button>` : 
                    `<button class="btn-quiz" onclick="parseExam('${examName}')">解析</button>`
                }
            </div>
        `;
    }).join('');
    
    document.getElementById('output').innerHTML = 'SUCCESS';
} catch(e) {
    document.getElementById('output').innerHTML = 'ERROR: ' + e.message;
}
'''

# Test 3: Without nested template literals
test3 = '''
try {
    const exams = [{id: 1, name: "test", grade: "高一", region: "学校", exam_type: "模拟题", has_answers: true, question_count: 10, file_count: 1, files: []}];
    const HOT_UNIVERSITIES = ['人大附中', '上海中学', '衡水中学'];
    const container = document.getElementById('output');
    
    container.innerHTML = exams.map((exam, index) => {
        const gradeLabel = exam.grade || exam.year || '';
        const gradeColor = exam.grade === '高一' ? '#10b981' : '#f59e0b';
        const badgeHtml = gradeLabel ? '<span class="grade-badge" style="background:' + gradeColor + '">' + gradeLabel + '</span>' : '';
        const quizButton = exam.has_answers ? 
            '<button class="btn-quiz" onclick="startQuiz(' + exam.id + ')">开始练习</button>' : 
            '<button class="btn-quiz" onclick="parseExam(\\'' + exam.name + '\\')">解析</button>';
        return '<div class="exam-card">' +
            badgeHtml +
            (exam.region || '') + ' ' + (exam.exam_type || '模拟题') +
            '<button class="btn-preview" onclick="previewExam(' + (exam.id || 'null') + ', \\'' + exam.name + '\\')">预览</button>' +
            quizButton +
            '</div>';
    }).join('');
    
    document.getElementById('output').innerHTML = 'SUCCESS';
} catch(e) {
    document.getElementById('output').innerHTML = 'ERROR: ' + e.message;
}
'''

# Test 4: Just the template literal with nested template
test4 = '''
try {
    const gradeLabel = '高一';
    const gradeColor = '#10b981';
    const result = `<div>${gradeLabel ? `<span style="background:${gradeColor}">${gradeLabel}</span>` : ''}</div>`;
    document.getElementById('output').innerHTML = 'SUCCESS: ' + result;
} catch(e) {
    document.getElementById('output').innerHTML = 'ERROR: ' + e.message;
}
'''

# Test 5: Just the regex part
test5 = '''
try {
    const exam = {id: 1, name: "test's"};
    const result = exam.name.replace(/'/g, "\\'");
    const html = `<button onclick="previewExam(${exam.id}, '${result}')">预览</button>`;
    document.getElementById('output').innerHTML = 'SUCCESS: ' + html;
} catch(e) {
    document.getElementById('output').innerHTML = 'ERROR: ' + e.message;
}
'''

tests = [
    ('test-v1.html', 'Test 1: Original (with regex + nested templates)', test1),
    ('test-v2.html', 'Test 2: Regex outside template literal', test2),
    ('test-v3.html', 'Test 3: No nested templates (string concat)', test3),
    ('test-v4.html', 'Test 4: Just nested templates', test4),
    ('test-v5.html', 'Test 5: Just regex', test5),
]

for filename, description, test_code in tests:
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{description}</title>
</head>
<body>
    <h1>{description}</h1>
    <div id="output">Testing...</div>
    <script>
{base_mock}
{test_code}
    </script>
</body>
</html>'''
    
    filepath = f'd:/15821/biovision/frontend/practice/{filename}'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Created {filename}: {description}")

print("Done!")