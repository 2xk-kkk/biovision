import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_NAME = os.path.join(BASE_DIR, "forum.db")

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")  # 关键：开启 WAL 模式
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''create table if not exists users (
        id integer primary key autoincrement,
        username text not null unique,
        password text not null,
        telephone text,
        avatar text,
        bio text,
        create_at timestamp default current_timestamp
    )''')

    # 创建帖子表 增加浏览/点赞/收藏/分享字段
    cursor.execute('''create table if not exists posts(
        id integer primary key autoincrement,
        user_id integer not null,
        content text not null,
        create_at timestamp default current_timestamp,
        tag text default 'Question_discussion',
        view_count integer default 0,
        like_count integer default 0,
        collect_count integer default 0,
        share_count integer default 0,
        foreign key(user_id) references users(id) on delete cascade              
    )''')

    # 创建帖子图片表
    cursor.execute('''create table if not exists post_image(
        id integer primary key autoincrement,
        post_id integer not null,
        image_url text not null,
        sort_order integer not null,
        create_at timestamp default current_timestamp,
        foreign key(post_id) references posts(id) on delete cascade
    )''')

    # 新增：创建评论表
    cursor.execute('''create table if not exists comments (
        id integer primary key autoincrement,
        post_id integer not null,
        user_id integer not null,
        content text not null,
        create_at timestamp default current_timestamp,
        like_count integer default 0,
        parent_id integer default null, 
        foreign key(post_id) references posts(id) on delete cascade,
        foreign key(user_id) references users(id) on delete cascade,
        foreign key(parent_id) references comments(id) on delete cascade
    )''')

    # 点赞/收藏表
    cursor.execute('''create table if not exists user_interact (
        id integer primary key autoincrement,
        user_id integer not null,
        post_id integer not null,
        type text not null,  -- 'like' / 'collect'
        create_at timestamp default current_timestamp,
        unique(user_id, post_id, type), 
        foreign key(user_id) references users(id) on delete cascade,
        foreign key(post_id) references posts(id) on delete cascade
    )''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("建表成功 ✅")
if __name__ == "__main__":
    init_db()
    print("建表成功")
                  