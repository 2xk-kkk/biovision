# BioVision 数据库设计文档

> 最后更新：2026-08-06
> 数据库类型：SQLite3
> 数据库文件：`backend/forum.db`

---

## 一、概述

BioVision 使用 SQLite3 作为数据库，单文件存储，通过 WAL 模式提升并发性能。数据库初始化脚本位于 `backend/database/db.py` 的 `init_db()` 函数。

### 连接信息

| 项 | 值 |
|---|---|
| 文件路径 | `backend/forum.db` |
| 连接方式 | `database.db.get_db_connection()` |
| 外键 | PRAGMA foreign_keys = ON |
| 日志模式 | WAL |
| ORM | 无，直接 SQL |

### 模块结构

```
backend/
├── database/db.py          # 数据库连接 & 建表
├── model/                  # 数据访问层（SQL封装）
│   ├── question.py         # 题目/答题/题库结构
│   ├── user.py             # 用户/关注/统计
│   ├── post.py             # 帖子/评论
│   ├── online.py           # 在线状态
│   └── request.py          # Pydantic 请求模型
├── service/                # 业务逻辑层
│   ├── question.py         # 答题/题库/进度
│   ├── user.py             # 注册/登录/个人中心
│   ├── post.py             # 帖子CRUD
│   ├── chart.py            # 首页统计
│   ├── exam.py             # 真题试卷管理
│   └── ppt/                # PPT生成（独立模块）
└── routers/                # API路由层
    ├── question.py
    ├── user.py
    ├── post.py
    ├── exam.py
    ├── chart.py
    └── ppt.py
```

---

## 二、表结构设计

### 2.1 users — 用户表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | INTEGER | PK | 用户ID |
| username | TEXT | NOT NULL, UNIQUE | 用户名 |
| password | TEXT | NOT NULL | SHA256哈希密码 |
| telephone | TEXT | | 手机号 |
| avatar | TEXT | | 头像Base64 |
| introduction | TEXT | | 个人简介 |
| school | TEXT | | 学校 |
| grade | TEXT | | 年级 |
| role | TEXT | DEFAULT '学生' | 角色 |
| like_count | INTEGER | DEFAULT 0 | 获赞数 |
| follower_count | INTEGER | DEFAULT 0 | 粉丝数 |
| following_count | INTEGER | DEFAULT 0 | 关注数 |
| view_count | INTEGER | DEFAULT 0 | 主页浏览量 |
| ip_address | TEXT | | IP属地 |
| study_hours | REAL | DEFAULT 0 | 学习时长 |
| question_count | INTEGER | DEFAULT 0 | 做题数（⚠️ 未启用） |
| wrong_count | INTEGER | DEFAULT 0 | 错题数（⚠️ 未启用） |
| create_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 注册时间 |

> ⚠️ `question_count` 和 `wrong_count` 字段存在但**后端未自动更新**，做题统计请直接查 `user_answers` 表。

---

### 2.2 questions — 题目表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | INTEGER | PK | 题目ID |
| exam_id | INTEGER | NOT NULL, FK→exams | 所属试卷 |
| number | INTEGER | NOT NULL | 题号 |
| stem | TEXT | NOT NULL | 题干 |
| option_a | TEXT | | 选项A |
| option_b | TEXT | | 选项B |
| option_c | TEXT | | 选项C |
| option_d | TEXT | | 选项D |
| answer | TEXT | | 正确答案 |
| images | TEXT | | 图片JSON数组 |
| textbook | TEXT | DEFAULT '' | 教材（如"必修一：分子与细胞"） |
| chapter | TEXT | | 章节 |
| section | TEXT | | 小节 |
| type | TEXT | | 题型（choice/fill/essay） |
| analysis | TEXT | | 解析 |
| create_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 录入时间 |

- **唯一约束**：(exam_id, number)
- **题型枚举**：`choice`(选择题)、`fill`(填空题)、`essay`(大题)
- **教材名称**：存在"必修一"和"选择性必修一"两种命名，通过 `normalize_textbook_name()` 函数统一映射

**教材名称映射表：**

| 前端显示 | 数据库中的名称 | 题目数 |
|---|---|---|
| 必修一：分子与细胞 | 必修一：分子与细胞 | ~1059 |
| 必修二：遗传与进化 | 必修二：遗传与进化 | ~726 |
| 选修一：稳态与调节 | 选修一 + 选择性必修一 | ~604 |
| 选修二：生物与环境 | 选修二 + 选择性必修二 | ~475 |
| 选修三：生物技术与工程 | 选修三 + 选择性必修三 | ~386 |

---

### 2.3 exams — 试卷表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | INTEGER | PK | 试卷ID |
| name | TEXT | NOT NULL, UNIQUE | 试卷名称 |
| file_name | TEXT | | 源文件名 |
| question_count | INTEGER | DEFAULT 0 | 题目数量 |
| create_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 导入时间 |

---

### 2.4 user_answers — 答题记录表

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | INTEGER | PK | 记录ID |
| user_id | INTEGER | NOT NULL, FK→users | 用户ID |
| question_id | INTEGER | NOT NULL, FK→questions | 题目ID |
| answer | TEXT | | 用户答案 |
| is_correct | INTEGER | DEFAULT 0 | 是否正确（0/1） |
| wrong_count | INTEGER | DEFAULT 0 | 累计错误次数 |
| mastered | INTEGER | DEFAULT 0 | 是否已攻克（0/1） |
| create_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 最后答题时间 |

- **唯一约束**：(user_id, question_id) — 每道题每人只保留最新一条记录
- 提交答案时采用 INSERT OR REPLACE 策略，`create_at` 更新为最近答题时间
- `mastered`：做对一次自动设为1，用于错题本"已攻克"筛选

---

### 2.5 posts — 帖子表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 帖子ID |
| user_id | INTEGER FK | 作者ID |
| content | TEXT NOT NULL | 内容 |
| tag | TEXT DEFAULT 'Question_discussion' | 分类标签 |
| tags | TEXT | 自定义标签 |
| view_count | INTEGER DEFAULT 0 | 浏览数 |
| like_count | INTEGER DEFAULT 0 | 点赞数 |
| collect_count | INTEGER DEFAULT 0 | 收藏数 |
| share_count | INTEGER DEFAULT 0 | 分享数 |
| create_at | TIMESTAMP | 发布时间 |

---

### 2.6 comments — 评论表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 评论ID |
| post_id | INTEGER FK | 帖子ID |
| user_id | INTEGER FK | 用户ID |
| content | TEXT NOT NULL | 内容 |
| like_count | INTEGER DEFAULT 0 | 点赞数 |
| parent_id | INTEGER | 父评论ID（支持嵌套回复） |
| create_at | TIMESTAMP | 发布时间 |

---

### 2.7 社交相关表

**user_follow — 关注关系**
| 字段 | 类型 | 说明 |
|---|---|---|
| follower_id | INTEGER FK | 关注者 |
| following_id | INTEGER FK | 被关注者 |
| 唯一约束 | (follower_id, following_id) | |

**user_interact — 用户互动（点赞/收藏）**
| 字段 | 类型 | 说明 |
|---|---|---|
| user_id | INTEGER FK | 用户 |
| post_id | INTEGER FK | 帖子 |
| type | TEXT | 'like' 或 'collect' |
| 唯一约束 | (user_id, post_id, type) | |

**comment_likes — 评论点赞**
| 字段 | 类型 | 说明 |
|---|---|---|
| user_id | INTEGER FK | 用户 |
| comment_id | INTEGER FK | 评论 |
| 唯一约束 | (user_id, comment_id) | |

**post_image — 帖子图片**
| 字段 | 类型 | 说明 |
|---|---|---|
| post_id | INTEGER FK | 帖子 |
| image_url | TEXT | 图片URL |
| sort_order | INTEGER | 排序 |

---

### 2.8 user_online — 在线状态

| 字段 | 类型 | 说明 |
|---|---|---|
| user_id | INTEGER PK, FK | 用户ID |
| last_active | INTEGER NOT NULL | Unix时间戳 |

---

### 2.9 post_stats — 帖子统计

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT PK | |
| total | INT NOT NULL | 帖子总数 |

---

### 2.10 model_favorites — 3D 模型收藏

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 记录ID |
| user_id | INTEGER FK→users | 收藏用户 |
| model_id | TEXT | 模型标识（见 `backend/model/model_favorite.py` 的 `MODEL_CATALOG`，30个模型） |
| create_at | TIMESTAMP | 收藏时间 |
| 唯一约束 | (user_id, model_id) | 同一用户同一模型只收藏一次 |

> 模型元数据（名称/描述/章节/页面文件/图标）由后端 `MODEL_CATALOG` 常量统一维护，作为收藏详情接口的返回来源。

---

## 三、API 接口文档

Base URL: `http://localhost:8000/api`

### 3.1 用户相关

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| POST | `/register` | 否 | 用户注册 |
| POST | `/login` | 否 | 用户登录 |
| GET | `/user/{id}/info` | 否 | 获取用户信息 |
| PUT | `/user/{id}/info` | JWT | 更新用户信息 |
| PUT | `/user/{id}/username` | JWT | 修改用户名 |
| PUT | `/user/{id}/avatar` | JWT | 更新头像 |
| PUT | `/user/{id}/introduction` | JWT | 更新简介 |
| PUT | `/user/{id}/ip_address` | JWT | 更新IP属地 |
| GET | `/user/{id}/stats` | 否 | 用户统计数据 |
| GET | `/user/{id}/posts` | 否 | 用户帖子列表 |
| GET | `/user/{id}/followers` | 否 | 粉丝列表 |
| GET | `/user/{id}/following` | 否 | 关注列表 |
| GET | `/user/{id}/likers` | 否 | 点赞用户列表 |
| GET | `/user/{id}/likes` | 否 | 用户点赞的帖子 |
| GET | `/user/{id}/collects` | 否 | 用户收藏的帖子 |
| POST | `/model/{model_id}/favorite` | JWT | 收藏/取消收藏 3D 模型 |
| GET | `/model/favorites/ids` | JWT | 当前用户已收藏的模型 id 列表 |
| GET | `/user/{id}/model-favorites` | 否 | 用户收藏的 3D 模型详情列表 |
| POST | `/user/{id}/follow` | JWT | 关注用户 |
| POST | `/user/{id}/unfollow` | JWT | 取消关注 |
| GET | `/user/{id}/follow/status` | JWT | 检查关注状态 |
| POST | `/user/{id}/view` | 否 | 增加主页浏览量 |

### 3.2 题目/练习相关

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| POST | `/questions/import` | 否 | 批量导入题目 |
| POST | `/questions/answer` | JWT | 提交答案 |
| GET | `/questions/textbook` | 否 | 按教材/章节/题型筛选题目 |
| GET | `/questions/related/{question_id}` | JWT | 相关知识点推荐 |
| GET | `/questions/{question_id}` | 否 | 获取单个题目详情 |
| GET | `/exams/list` | 否 | 试卷列表（数据库） |
| GET | `/exams/{id}/questions` | 否 | 试卷题目 |
| GET | `/exams/{id}/progress` | JWT | 用户考试进度 |
| GET | `/exams/{id}/my_answers` | JWT | 用户考试答案 |
| GET | `/wrong-answers` | JWT | 错题列表（分页） |
| GET | `/wrong-answers/stats` | JWT | 错题统计 |
| POST | `/wrong-answers/{qid}/retry` | JWT | 重做错题 |
| PUT | `/wrong-answers/{qid}/master` | JWT | 标记/取消攻克 |
| GET | `/question-bank/structure` | 否 | 题库层级结构 |
| GET | `/user/{id}/daily-answers` | 否 | 近N天每日做题数 |
| GET | `/user/{id}/textbook-progress` | 否 | 五本教材做题进度 |
| GET | `/textbook/chapters` | 否 | 某教材章节进度 |

### 3.3 PPT生成

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| POST | `/ppt/generate` | 否 | AI生成PPT课件 |
| GET | `/ppt/decks` | 否 | 已生成课件列表 |
| GET | `/ppt/decks/{id}/html` | 否 | 查看课件 |
| GET | `/ppt/decks/{id}/download` | 否 | 下载课件 |
| GET | `/ppt/knowledge/chapters` | 否 | 知识点章节列表 |
| GET | `/ppt/knowledge/{key}` | 否 | 章节知识点内容 |

### 3.4 论坛

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/posts` | 否 | 帖子列表 |
| POST | `/create_post` | JWT | 发帖 |
| GET | `/post/{id}` | 否 | 帖子详情 |
| PUT | `/post/{id}` | JWT | 编辑帖子 |
| DELETE | `/post/{id}` | JWT | 删除帖子 |
| POST | `/post/{id}/like` | JWT | 点赞帖子 |
| POST | `/post/{id}/collect` | JWT | 收藏帖子 |
| POST | `/post/{id}/share` | JWT | 分享帖子 |
| POST | `/post/{id}/comment` | JWT | 评论帖子 |
| GET | `/post/{id}/comments` | 否 | 帖子评论列表 |
| POST | `/comment/{id}/like` | JWT | 点赞评论 |
| POST | `/upload_image` | JWT | 上传图片 |
| POST | `/upload_file` | JWT | 上传文件 |

### 3.5 试卷管理 & 统计

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/exams` | 否 | 真题文件列表 |
| GET | `/exams/download` | 否 | 下载真题文件 |
| POST | `/exams/upload` | 否 | 上传真题文件 |
| POST | `/exams/import` | 否 | 批量导入真题 |
| DELETE | `/exams/file` | 否 | 删除真题文件 |
| GET | `/stats` | 否 | 平台统计 |

### 3.6 旧版PPT接口（保留兼容）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/decks` | 课件列表 |
| GET | `/decks/{id}/html` | 查看课件 |
| GET | `/decks/{id}/download` | 下载课件 |
| POST | `/generate` | 生成课件 |
| GET | `/knowledge/chapters` | 知识点列表 |

---

## 四、数据流关键路径

### 4.1 做题流程

```
用户点击"开始练习"
  → GET /api/questions/textbook?textbook=&chapter=&section=&type=
  → 返回题目列表 → 前端随机抽5道
  → 用户答题 → 提交答案
  → POST /api/questions/answer (JWT)
  → 后端比对答案 → INSERT/UPDATE user_answers
  → 返回正确/错误 + 解析
```

### 4.2 进度统计

```
main.html 加载
  → GET /api/question-bank/structure    (题库总量)
  → GET /api/user/{id}/daily-answers   (近90天做题日历)
  → GET /api/user/{id}/textbook-progress (五本教材进度)
  → 前端渲染热力图 + 进度环
```

### 4.3 PPT生成

```
用户选择知识点 + 题库章节
  → POST /api/ppt/generate
  → 后端读取知识HTML文件 → 提取纯文本
  → 查询题库章节样题 → 合并到prompt
  → 调用AI生成幻灯片JSON → 渲染HTML → 返回下载链接
```

---

## 五、已知问题 & 注意事项

| 问题 | 影响 | 计划 |
|---|---|---|
| questions表教材名不统一 | 查询需LIKE双匹配 | 待统一数据 |
| users.question_count未自动更新 | 该字段数据不准 | 直接查user_answers |
| SQLite无时区，日期用localtime修正 | 每日统计偏差 | 已修复 |
| 无知识标签字段 | 无法按知识点推荐 | 计划新增 |
| user_answers只保留最新记录 | 无法追溯历史 | 可新增log表 |

---

## 六、迁移记录

| 日期 | 变更 | 说明 |
|---|---|---|
| 初始 | 创建基础表 | users/posts/comments/exams/questions |
| 迁移1 | users增加字段 | introduction/like_count/follower_count/following_count/view_count |
| 迁移2 | users增加字段 | ip_address/school/grade/role |
| 迁移3 | users增加字段 | study_hours/question_count/wrong_count |
| 迁移4 | posts增加字段 | tags |
| 迁移5 | questions增加字段 | textbook/chapter/section/type/analysis |
| 2026-07 | 新增user_answers | 答题记录表 |
| 2026-08 | 修正时区问题 | get_daily_answer_counts使用localtime |
