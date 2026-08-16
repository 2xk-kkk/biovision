        // 自动识别 API 基础路径：
        // - 页面通过 FastAPI 访问（http://host:port/...）→ 使用相对路径 '/api'
        // - 直接 file:// 双击打开 → 回退到 'http://localhost:8000/api'
        (function () {
            var proto = (typeof location !== 'undefined' && location.protocol) || '';
            window.__API_BASE__ = (proto === 'file:') ? 'http://localhost:8000/api' : '/api';
            window.__STATIC_PREFIX__ = (proto === 'file:') ? 'http://localhost:8000' : '';
        })();

        function apiUrl(path) {
            var base = window.__API_BASE__ || '/api';
            if (!path) return base;
            if (path.charAt(0) !== '/') path = '/' + path;
            return base + path;
        }

        /** 将 /uploads/... 或 /api/... 相对路径转换为当前访问方式下可直接请求/下载/展示的完整 URL。 */
        function toAccessibleUrl(raw) {
            if (!raw || typeof raw !== 'string') return '';
            if (/^https?:/i.test(raw)) return raw;
            if (raw.charAt(0) === '/') {
                return (window.__STATIC_PREFIX__ || '') + raw;
            }
            return raw;
        }

        // 全国知名高中列表
        const FAMOUS_UNIVERSITIES = [
            '人大附中', '北京四中', '上海中学', '华师大二附中',
            '南京外国语', '杭二中', '华师一附中', '成都七中',
            '深圳中学', '衡水中学'
        ];

        const HOT_UNIVERSITIES = ['人大附中', '上海中学', '衡水中学', '成都七中', '华师一附中'];

        let selectedFile = null;
        let currentYear = '全部';
        let currentUniversity = '全部';
        let currentType = '全部';
        let years = [];

        function escapeAttr(str) {
            if (str === null || str === undefined) return '';
            return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
        }

        function buildExamCard(exam, index) {
            var gradeLabel = exam.grade || exam.year || '';
            var gradeColor = '#f59e0b';
            if (exam.grade === '高一') gradeColor = '#10b981';
            else if (exam.grade === '高二') gradeColor = '#3b82f6';
            else if (exam.grade === '高三') gradeColor = '#f59e0b';

            var gradeBadge = '';
            if (gradeLabel) {
                gradeBadge = '<span class="grade-badge" style="background:' + gradeColor + '">' + gradeLabel + '</span>';
            }

            var region = exam.region || '';
            var examType = exam.exam_type || '模拟题';
            var fileCount = exam.file_count || 0;
            var hasAnswers = exam.has_answers;
            var questionCount = exam.question_count || 0;

            // 标签
            var tags = '';
            if (index < 3) {
                tags += '<span class="exam-tag tag-new">新增</span>';
            }
            if (HOT_UNIVERSITIES.indexOf(exam.region) !== -1) {
                tags += '<span class="exam-tag tag-hot">热门高中</span>';
            }

            // 操作按钮
            var examId = exam.id || 'null';
            var examNameEscaped = escapeAttr(exam.name || '');
            var examNameStr = exam.name || '';

            var actionButtons = '';
            actionButtons += '<button class="btn-preview" onclick="previewExam(' + examId + ', \'' + examNameEscaped + '\')">预览</button>';

            if (hasAnswers) {
                actionButtons += '<button class="btn-quiz" onclick="startQuiz(' + examId + ')">开始练习</button>';
            } else {
                actionButtons += '<button class="btn-quiz" onclick="parseExam(\'' + examNameEscaped + '\')">📝 解析</button>';
            }

            var filesStr = JSON.stringify(exam.files || []);
            actionButtons += '<button class="btn-start" onclick="downloadFiles(\'' + encodeURIComponent(filesStr) + '\')">下载</button>';

            var html = '';
            html += '<div class="exam-card">';
            html += '  <div class="exam-card-header">';
            html += '    <div class="exam-icon">📘</div>';
            html += '    <div class="exam-title">';
            html += '      <div class="exam-name">';
            html += gradeBadge + ' ' + region + ' ' + examType;
            html += '      </div>';
            html += '    </div>';
            html += '  </div>';
            html += '  <div class="exam-meta">';
            html += '    <div class="meta-item">';
            html += '      <span class="meta-icon">🏫</span>';
            html += '      <span class="meta-value">' + (exam.region || '未知高校') + '</span>';
            html += '    </div>';
            html += '    <div class="meta-item">';
            html += '      <span class="meta-icon">📄</span>';
            html += '      <span class="meta-value">' + fileCount + '份文件</span>';
            html += '    </div>';
            html += '    <div class="meta-item">';
            html += '      <span class="meta-icon">📝</span>';
            if (hasAnswers) {
                html += '      <span class="meta-value">' + questionCount + '题</span>';
            } else {
                html += '      <span class="meta-value">未解析</span>';
            }
            html += '    </div>';
            html += '  </div>';
            html += '  <div class="exam-tags">' + tags + '</div>';
            html += '  <div class="exam-footer">';
            html += '    <div class="star-rating">';
            html += '      <span class="star">★</span>';
            html += '      <span class="star">★</span>';
            html += '      <span class="star">★</span>';
            html += '      <span class="star">★</span>';
            html += '      <span class="star">☆</span>';
            html += '    </div>';
            html += '    <div class="exam-actions">' + actionButtons + '</div>';
            html += '  </div>';
            html += '</div>';

            return html;
        }

        async function loadExams(year, university, type) {
            if (year === undefined) year = null;
            if (university === undefined) university = null;
            if (type === undefined) type = null;

            var container = document.getElementById('examContainer');
            try {
                var url = apiUrl('/exams');
                var params = ['scope=模拟'];
                if (year && year !== '全部') params.push('year=' + year);
                if (university && university !== '全部') params.push('region=' + encodeURIComponent(university));
                if (type && type !== '全部') params.push('type=' + encodeURIComponent(type));
                if (params.length > 0) url += '?' + params.join('&');

                var response = await fetch(url);
                var result = await response.json();

                if (!result.success) {
                    container.innerHTML = '<div class="empty-state">' +
                        '<div class="empty-icon">📭</div>' +
                        '<div class="empty-title">暂无试卷</div>' +
                        '<div class="empty-desc">' + (result.msg || '试卷目录为空') + '</div>' +
                        '</div>';
                    return;
                }

                var data = result.data;
                var exams = data.exams;
                var stats = data.stats || {};
                years = data.years || [];

                updateStats(stats);
                updateYearSelect(years);
                updateUniversityTags();

                if (exams.length === 0) {
                    container.innerHTML = '<div class="empty-state">' +
                        '<div class="empty-icon">📭</div>' +
                        '<div class="empty-title">暂无试卷</div>' +
                        '<div class="empty-desc">请点击上方"上传试卷"添加高中模拟题</div>' +
                        '</div>';
                    return;
                }

                var htmlParts = [];
                for (var i = 0; i < exams.length; i++) {
                    htmlParts.push(buildExamCard(exams[i], i));
                }
                container.innerHTML = htmlParts.join('');
            } catch (error) {
                console.error('加载试卷失败:', error);
                container.innerHTML = '<div class="empty-state">' +
                    '<div class="empty-icon">❌</div>' +
                    '<div class="empty-title">加载失败</div>' +
                    '<div class="empty-desc">请确保后端服务已启动</div>' +
                    '</div>';
                console.error('加载试卷失败:', error);
            }
        }

        function updateStats(stats) {
            document.getElementById('statTotalExams').textContent = stats.total_exams || 0;
            document.getElementById('statTotalRegions').textContent = stats.total_regions || 0;
            document.getElementById('statYearRange').textContent = stats.year_range || '--';
            document.getElementById('statTotalQuestions').textContent = stats.total_questions > 0 ? stats.total_questions + '+' : '0';
        }

        function updateYearSelect(yearList) {
            var select = document.getElementById('yearSelect');
            var currentValue = select.value;
            select.innerHTML = '<option value="全部">全部年份</option>';
            yearList.forEach(function(year) {
                var option = document.createElement('option');
                option.value = year;
                option.textContent = year + '年';
                select.appendChild(option);
            });
            select.value = currentYear;
        }

        function updateUniversityTags() {
            var container = document.getElementById('uniTags');
            container.innerHTML = '';

            // "全部高校" 标签
            var allTag = document.createElement('span');
            allTag.className = 'region-tag' + (currentUniversity === '全部' ? ' active' : '');
            allTag.textContent = '全部高中';
            allTag.onclick = function() { selectUniversity('全部'); };
            container.appendChild(allTag);

            // 知名高校标签
            FAMOUS_UNIVERSITIES.forEach(function(uni) {
                var tag = document.createElement('span');
                tag.className = 'region-tag' + (currentUniversity === uni ? ' active' : '');
                tag.textContent = uni;
                tag.onclick = function() { selectUniversity(uni); };
                container.appendChild(tag);
            });
        }

        function selectUniversity(university) {
            currentUniversity = university;
            loadExams(
                currentYear === '全部' ? null : currentYear,
                currentUniversity === '全部' ? null : currentUniversity,
                currentType === '全部' ? null : currentType
            );
        }

        function handleFilterChange() {
            currentYear = document.getElementById('yearSelect').value;
            currentType = document.getElementById('typeSelect').value;
            loadExams(
                currentYear === '全部' ? null : currentYear,
                currentUniversity === '全部' ? null : currentUniversity,
                currentType === '全部' ? null : currentType
            );
        }

        function downloadFiles(encodedFiles) {
            var files = JSON.parse(decodeURIComponent(encodedFiles));
            if (files.length === 1) {
                var p = (typeof files[0].path === 'string' && files[0].path.charAt(0) === '/')
                    ? files[0].path
                    : apiUrl('/exams/download?file_path=' + encodeURIComponent(files[0].path || ''));
                // 如果后端返回的是 /uploads/... Web 路径，直接作为静态资源下载；否则走 /api/exams/download 代理
                var downloadUrl = (typeof files[0].path === 'string' && /^\/uploads\//i.test(files[0].path))
                    ? toAccessibleUrl(files[0].path)
                    : toAccessibleUrl(apiUrl('/exams/download?file_path=' + encodeURIComponent(files[0].path || '')));
                window.open(downloadUrl, '_blank');
            } else {
                files.forEach(function(file) {
                    setTimeout(function() {
                        var dUrl = (typeof file.path === 'string' && /^\/uploads\//i.test(file.path))
                            ? toAccessibleUrl(file.path)
                            : toAccessibleUrl(apiUrl('/exams/download?file_path=' + encodeURIComponent(file.path || '')));
                        window.open(dUrl, '_blank');
                    }, 300);
                });
            }
        }

        function openUploadModal() {
            document.getElementById('uploadModal').classList.add('show');
            document.getElementById('categoryInput').value = '';
            clearFile();
        }

        function closePreviewModal() {
            document.getElementById('previewModal').classList.remove('show');
        }

        function startQuiz(examId) {
            window.location.href = 'exam-quiz.html?exam_id=' + examId;
        }

        // 构建图片HTML
        function buildImagesHtml(images) {
            if (!images || images.length === 0) return '';
            var html = '<div class="preview-q-images">';
            for (var i = 0; i < images.length; i++) {
                html += '<img src="' + images[i] + '" alt="题目图片" onerror="this.style.display=\'none\'">';
            }
            html += '</div>';
            return html;
        }

        // 构建选择题HTML
        function buildChoiceQuestionsHtml(choiceQuestions) {
            var html = '<div class="preview-section-title">一、选择题（共' + choiceQuestions.length + '题，每题只有一个选项符合题意）</div>';
            for (var i = 0; i < choiceQuestions.length; i++) {
                var q = choiceQuestions[i];
                var stem = q.stem || q.content || q.question || '';
                var images = parseImages(q.images);
                var imagesHtml = buildImagesHtml(images);

                var optionsHtml = '';
                var opts = q._options || [];
                for (var j = 0; j < opts.length; j++) {
                    optionsHtml += '<div class="preview-option">' +
                        '<span class="preview-option-letter">' + opts[j].key + '.</span>' +
                        '<span class="preview-option-text">' + (opts[j].text || '') + '</span>' +
                        '</div>';
                }

                var answerHtml = '';
                if (q.answer) {
                    answerHtml = '<div class="preview-answer"><strong>参考答案：</strong>' + q.answer + '</div>';
                }

                html += '<div class="preview-question">' +
                    '<div class="preview-question-stem" data-num="' + q._index + '">' + stem + '</div>' +
                    imagesHtml +
                    '<div class="preview-options">' + optionsHtml + '</div>' +
                    answerHtml +
                    '</div>';
            }
            return html;
        }

        // 构建非选择题HTML
        function buildFillQuestionsHtml(fillQuestions, hasChoice) {
            var sectionTitle = (hasChoice ? '二、' : '一、') + '非选择题（共' + fillQuestions.length + '题）';
            var html = '<div class="preview-section-title">' + sectionTitle + '</div>';
            for (var i = 0; i < fillQuestions.length; i++) {
                var q = fillQuestions[i];
                var stem = q.stem || q.content || q.question || '';
                var images = parseImages(q.images);
                var imagesHtml = buildImagesHtml(images);

                var answerHtml = '';
                if (q.answer) {
                    answerHtml = '<div class="preview-answer"><strong>参考答案：</strong>' + q.answer + '</div>';
                }

                html += '<div class="preview-question">' +
                    '<div class="preview-question-stem" data-num="' + q._index + '">' + stem + '</div>' +
                    imagesHtml +
                    '<div class="preview-no-options">（本题无选项，请直接作答）</div>' +
                    answerHtml +
                    '</div>';
            }
            return html;
        }

        async function previewExam(examId, examName) {
            if (!examId) {
                if (confirm('试卷"' + examName + '"尚未解析，是否先进行解析？')) {
                    await parseExam(examName);
                    showToast('success', '解析成功，请再次点击预览按钮');
                }
                return;
            }

            document.getElementById('previewModal').classList.add('show');
            var content = document.getElementById('previewContent');
            content.innerHTML = '<div class="preview-no-questions">' +
                '<div style="font-size: 48px; margin-bottom: 16px;">📝</div>' +
                '<div>加载中...</div>' +
                '</div>';

            try {
                var response = await fetch(apiUrl('/exams/' + examId + '/questions'));
                var result = await response.json();

                var questions = [];
                var examInfo = {};
                if (result.code === 200 && result.data) {
                    if (Array.isArray(result.data)) {
                        questions = result.data;
                    } else if (result.data.questions && Array.isArray(result.data.questions)) {
                        questions = result.data.questions;
                        examInfo = result.data.exam_info || {};
                    }
                }

                if (questions.length > 0) {
                    // 按题型分组
                    var choiceQuestions = [];
                    var fillQuestions = [];

                    questions.forEach(function(q, index) {
                        var options = parseOptions(q.options);
                        var isChoice = options.length > 0;
                        if (isChoice) {
                            choiceQuestions.push({
                                ...q,
                                _index: index + 1,
                                _options: options
                            });
                        } else {
                            fillQuestions.push({ ...q, _index: index + 1 });
                        }
                    });

                    var examTitle = examInfo.name || examName || '生物试卷';
                    var grade = examInfo.grade || '';
                    var region = examInfo.region || '';
                    var examType = examInfo.exam_type || '';

                    // 构建选择题部分
                    var choiceHtml = '';
                    if (choiceQuestions.length > 0) {
                        choiceHtml = buildChoiceQuestionsHtml(choiceQuestions);
                    }

                    // 构建填空题部分
                    var fillHtml = '';
                    if (fillQuestions.length > 0) {
                        fillHtml = buildFillQuestionsHtml(fillQuestions, choiceQuestions.length > 0);
                    }

                    var headerInfo = '';
                    if (grade) headerInfo += '<span>年级：' + grade + '</span>';
                    if (region) headerInfo += '<span>学校：' + region + '</span>';
                    if (examType) headerInfo += '<span>类型：' + examType + '</span>';
                    headerInfo += '<span>共 ' + questions.length + ' 题</span>';

                    content.innerHTML = '<div class="preview-paper">' +
                        '<div class="preview-paper-header">' +
                        '<div class="preview-paper-title">' + examTitle + '</div>' +
                        '<div class="preview-paper-info">' + headerInfo + '</div>' +
                        '</div>' +
                        choiceHtml +
                        fillHtml +
                        '<div class="preview-paper-footer">—— 试卷预览结束 ——</div>' +
                        '</div>';
                } else {
                    content.innerHTML = '<div class="preview-no-questions">' +
                        '<div style="font-size: 48px; margin-bottom: 16px;">📋</div>' +
                        '<div>该试卷暂无题目</div>' +
                        '<div style="font-size: 13px; color: #9ca3af; margin-top: 8px;">请先解析试卷提取题目</div>' +
                        '</div>';
                }
            } catch (error) {
                content.innerHTML = '<div class="preview-no-questions">' +
                    '<div style="font-size: 48px; margin-bottom: 16px;">❌</div>' +
                    '<div>加载失败</div>' +
                    '<div style="font-size: 13px; color: #9ca3af; margin-top: 8px;">请确保后端服务已启动</div>' +
                    '</div>';
                console.error('预览失败:', error);
            }
        }

        function parseOptions(optionsData) {
            if (!optionsData) return [];
            var result = [];
            if (typeof optionsData === 'string') {
                try {
                    var parsed = JSON.parse(optionsData);
                    result = parseOptions(parsed);
                } catch (e) {
                    // Try to parse inline options like "A. xxx B. xxx C. xxx D. xxx"
                    result = parseOptionsFromString(optionsData);
                }
            } else if (Array.isArray(optionsData)) {
                result = optionsData;
            } else if (typeof optionsData === 'object' && optionsData !== null) {
                result = Object.keys(optionsData)
                    .filter(function(key) { return optionsData[key] && String(optionsData[key]).trim(); })
                    .map(function(key) {
                        return { key: key, text: String(optionsData[key]).trim() };
                    });
            }
            // Filter out empty text
            return result.filter(function(o) { return o && o.text && o.text.trim(); });
        }

        function parseOptionsFromString(text) {
            if (!text) return [];
            var options = [];
            // Match patterns like: A. content B. content or A、content B、content
            var pattern = /([A-D])[\s]*[.．、)）:：][\s]*(.*?)(?=[\s]*[A-D][\s]*[.．、)）:：]|$)/g;
            var match;
            while ((match = pattern.exec(text)) !== null) {
                var content = (match[2] || '').trim();
                if (content) {
                    options.push({ key: match[1], text: content });
                }
            }
            return options;
        }

        function parseImages(imagesData) {
            if (!imagesData) return [];
            var images = [];
            if (typeof imagesData === 'string') {
                try {
                    images = JSON.parse(imagesData);
                } catch (e) {
                    if (imagesData.startsWith('/') || imagesData.startsWith('http')) {
                        if (imagesData.indexOf(',') !== -1) {
                            images = imagesData.split(',').map(function(img) { return img.trim(); }).filter(function(img) { return img; });
                        } else {
                            images = [imagesData];
                        }
                    } else {
                        return [];
                    }
                }
            } else {
                images = imagesData;
            }
            // Return as-is (URLs or paths), don't filter by extension since URLs may not have extensions visible
            return images.filter(function(img) { return img && typeof img === 'string' && img.length > 0; });
        }

        function closeUploadModal() {
            document.getElementById('uploadModal').classList.remove('show');
        }

        function handleFileSelect(event) {
            var file = event.target.files[0];
            if (file) {
                selectedFile = file;
                document.getElementById('fileName').textContent = file.name;
                document.getElementById('selectedFile').style.display = 'block';
            }
        }

        function handleDrop(event) {
            var file = event.dataTransfer.files[0];
            if (file) {
                selectedFile = file;
                document.getElementById('fileName').textContent = file.name;
                document.getElementById('selectedFile').style.display = 'block';
            }
        }

        function clearFile() {
            selectedFile = null;
            document.getElementById('fileInput').value = '';
            document.getElementById('selectedFile').style.display = 'none';
        }

        async function importAndParse() {
            try {
                showToast('success', '正在从D盘导入并解析试卷...');
                var response = await fetch(apiUrl('/exams/import-and-parse'), {
                    method: 'POST'
                });
                var result = await response.json();

                if (result.success) {
                    var data = result.data || {};
                    var parseData = data.parse_result || {};
                    var msg = result.msg || '导入完成';
                    if (parseData.success !== undefined) {
                        msg += '（成功解析 ' + parseData.success + ' 个，失败 ' + parseData.failed + ' 个）';
                    }
                    showToast('success', msg);
                    loadExams();
                } else {
                    showToast('error', result.msg);
                }
            } catch (error) {
                showToast('error', '导入失败，请确保后端服务已启动');
                console.error('导入失败:', error);
            }
        }

        async function parseExam(examName) {
            try {
                showToast('success', '正在解析 ' + examName + '...');
                var formData = new FormData();
                formData.append('exam_name', examName);

                var response = await fetch(apiUrl('/exams/parse'), {
                    method: 'POST',
                    body: formData
                });
                var result = await response.json();

                if (result.success) {
                    showToast('success', result.msg);
                    loadExams();
                } else {
                    showToast('error', result.msg);
                }
            } catch (error) {
                showToast('error', '解析失败，请确保后端服务已启动');
                console.error('解析失败:', error);
            }
        }

        async function parseAllPending() {
            if (!confirm('确定要解析所有尚未解析的试卷吗？')) return;

            try {
                showToast('success', '正在批量解析试卷...');
                var response = await fetch(apiUrl('/exams/parse-all'), {
                    method: 'POST'
                });
                var result = await response.json();

                if (result.success) {
                    var data = result.data || {};
                    showToast('success', result.msg);
                    loadExams();
                } else {
                    showToast('error', result.msg);
                }
            } catch (error) {
                showToast('error', '批量解析失败，请确保后端服务已启动');
                console.error('批量解析失败:', error);
            }
        }

        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            var category = document.getElementById('categoryInput').value.trim();
            if (!category) {
                showToast('error', '请输入试卷分类');
                return;
            }

            if (!selectedFile) {
                showToast('error', '请选择要上传的文件');
                return;
            }

            var formData = new FormData();
            formData.append('category', category);
            formData.append('file', selectedFile);

            try {
                var response = await fetch(apiUrl('/exams/upload'), {
                    method: 'POST',
                    body: formData
                });
                var result = await response.json();

                if (result.success) {
                    showToast('success', '上传成功');
                    closeUploadModal();
                    loadExams();
                } else {
                    showToast('error', result.msg);
                }
            } catch (error) {
                showToast('error', '上传失败，请确保后端服务已启动');
                console.error('上传失败:', error);
            }
        });

        function showToast(type, message) {
            var toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.textContent = message;
            document.body.appendChild(toast);

            setTimeout(function() {
                toast.remove();
            }, 3000);
        }

        document.querySelector('.search-form').addEventListener('submit', function(e) {
            e.preventDefault();
        });

        document.getElementById('uploadModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeUploadModal();
            }
        });

        // 下拉菜单交互
        document.querySelectorAll('.dropdown-toggle').forEach(function(toggle) {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                var dropdown = toggle.parentElement;
                dropdown.classList.toggle('show');
            });
        });

        // 点击页面其他地方关闭下拉菜单
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.dropdown')) {
                document.querySelectorAll('.dropdown').forEach(function(dropdown) {
                    dropdown.classList.remove('show');
                });
            }
            var navDropdown = document.getElementById('navDropdownMenu');
            if (navDropdown && !e.target.closest('#navAvatarBtn')) {
                navDropdown.classList.remove('show');
            }
        });

        // 导航栏头像下拉菜单
        var navAvatarBtn = document.getElementById('navAvatarBtn');
        var navDropdown = document.getElementById('navDropdownMenu');
        if (navAvatarBtn && navDropdown) {
            navAvatarBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                navDropdown.classList.toggle('show');
            });
        }

        // 解析JWT token
        function parseJwt(token) {
            try {
                var base64Url = token.split('.')[1];
                var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                var binaryString = atob(base64);
                var bytes = new Uint8Array(binaryString.length);
                for (var i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                var jsonPayload = decodeURIComponent(escape(String.fromCharCode.apply(null, bytes)));
                return JSON.parse(jsonPayload);
            } catch (e) {
                return null;
            }
        }

        // 获取默认头像
        function getDefaultAvatar(username) {
            var colors = [
                '#4338ca',
                '#be185d',
                '#0369a1',
                '#15803d',
                '#c2410c',
                '#7c3aed',
                '#dc2626',
                '#b45309'
            ];
            var char = (username || '用').trim()[0].toUpperCase();
            var colorIndex = char.charCodeAt(0) % colors.length;
            return {
                color: colors[colorIndex],
                char: char
            };
        }

        // 加载用户信息
        async function loadUserInfo() {
            var token = localStorage.getItem('token');
            var navAvatarEl = document.getElementById('navAvatar');
            if (!navAvatarEl) return;

            if (!token) {
                navAvatarEl.innerHTML = '👤';
                return;
            }

            try {
                var payload = parseJwt(token);
                if (!payload || !payload.user_id) {
                    navAvatarEl.innerHTML = '👤';
                    return;
                }

                var resp = await fetch(apiUrl('/user/' + payload.user_id + '/info'));
                var data = await resp.json();

                if (data.success && data.data) {
                    var username = data.data.username || '用户';
                    if (data.data.avatar) {
                        navAvatarEl.innerHTML = '<img src="' + data.data.avatar + '" alt="头像" style="width:100%;height:100%;object-fit:cover;">';
                    } else {
                        var defaultAvatar = getDefaultAvatar(username);
                        navAvatarEl.style.background = defaultAvatar.color;
                        navAvatarEl.textContent = defaultAvatar.char;
                    }
                } else {
                    navAvatarEl.innerHTML = '👤';
                }
            } catch (e) {
                navAvatarEl.innerHTML = '👤';
            }
        }

        loadUserInfo();
        loadExams();
