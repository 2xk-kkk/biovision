import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_NAME = os.path.join(BASE_DIR, "forum.db")


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # 启用 WAL 模式，提升并发性能
    return conn


def add_column_if_not_exists(conn, table_name, column_name, column_def):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    if column_name not in columns:
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
            conn.commit()
        except Exception as e:
            print(f"添加列 {column_name} 失败: {e}")

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            telephone TEXT,
            avatar TEXT,
            introduction TEXT,
            like_count INTEGER DEFAULT 0,
            follower_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 迁移：添加缺失的用户表字段
    add_column_if_not_exists(conn, 'users', 'introduction', 'TEXT')
    add_column_if_not_exists(conn, 'users', 'like_count', 'INTEGER DEFAULT 0')
    add_column_if_not_exists(conn, 'users', 'follower_count', 'INTEGER DEFAULT 0')
    add_column_if_not_exists(conn, 'users', 'following_count', 'INTEGER DEFAULT 0')
    add_column_if_not_exists(conn, 'users', 'view_count', 'INTEGER DEFAULT 0')
    add_column_if_not_exists(conn, 'users', 'ip_address', 'TEXT')
    add_column_if_not_exists(conn, 'users', 'school', 'TEXT')
    add_column_if_not_exists(conn, 'users', 'grade', 'TEXT')
    add_column_if_not_exists(conn, 'users', 'role', 'TEXT DEFAULT "学生"')
    add_column_if_not_exists(conn, 'users', 'study_hours', 'REAL DEFAULT 0')
    add_column_if_not_exists(conn, 'users', 'question_count', 'INTEGER DEFAULT 0')
    add_column_if_not_exists(conn, 'users', 'wrong_count', 'INTEGER DEFAULT 0')

    # 迁移：为帖子表添加标签字段
    add_column_if_not_exists(conn, 'posts', 'tags', 'TEXT')

    # 迁移：为题目表添加知识点标签字段
    add_column_if_not_exists(conn, 'questions', 'knowledge_tags', 'TEXT DEFAULT "[]"')

    # 用户在线状态表（新增！用于登录时记录 last_active）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_online (
            user_id INTEGER PRIMARY KEY,
            last_active INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 关注关系表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_follow (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            follower_id INTEGER NOT NULL,
            following_id INTEGER NOT NULL,
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(follower_id, following_id),
            FOREIGN KEY(follower_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(following_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 帖子表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tag TEXT DEFAULT 'Question_discussion',
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            collect_count INTEGER DEFAULT 0,
            share_count INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 帖子图片表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS post_image (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            image_url TEXT NOT NULL,
            sort_order INTEGER NOT NULL,
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    ''')

    # 评论表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            like_count INTEGER DEFAULT 0,
            parent_id INTEGER DEFAULT NULL,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(parent_id) REFERENCES comments(id) ON DELETE CASCADE
        )
    ''')

    # 用户互动表（点赞/收藏）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_interact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            type TEXT NOT NULL,  -- 'like' 或 'collect'
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, post_id, type),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    ''')

    # 评论点赞表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comment_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            comment_id INTEGER NOT NULL,
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, comment_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(comment_id) REFERENCES comments(id) ON DELETE CASCADE
        )
    ''')

    # 试卷表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            file_name TEXT,
            question_count INTEGER DEFAULT 0,
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name)
        )
    ''')

    # 题目表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            number INTEGER NOT NULL,
            stem TEXT NOT NULL,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            answer TEXT,
            images TEXT,
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(exam_id) REFERENCES exams(id) ON DELETE CASCADE,
            UNIQUE(exam_id, number)
        )
    ''')

    # 知识点表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_key TEXT NOT NULL,
            book TEXT NOT NULL,
            chapter TEXT NOT NULL,
            section TEXT,
            section_name TEXT,
            label_text TEXT NOT NULL,
            category TEXT NOT NULL,
            key_terms TEXT NOT NULL,
            data_id INTEGER,
            file_path TEXT
        )
    ''')

    # 创建索引：按章节键查询知识点
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_kp_chapter_key
        ON knowledge_points(chapter_key)
    ''')

    # 用户答题记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT,
            is_correct INTEGER DEFAULT 0,
            wrong_count INTEGER DEFAULT 0,
            mastered INTEGER DEFAULT 0,
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE,
            UNIQUE(user_id, question_id)
        )
    ''')

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("✅ 数据库初始化成功：所有表已创建或确认存在。")