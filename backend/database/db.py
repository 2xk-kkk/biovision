import sqlite3

DB_NAME = "forum.db"

def get_db_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    

    #建立用户表
    cursor.execute('''create table if not exists users (
        id integer primary key autoincrement,
        username text not null unique,
        password text not null,
        telephone text,
        avatar text,
        bio text,
        create_at timestamp default current_timestamp
    )''')

    #创建帖子表
    cursor.execute('''create table if not exists posts(
        id integer primary key autoincrement,
        user_id integer not null,
        content text not null,
        create_at timestamp default current_timestamp,
        tag text default 'Question_discussion',
        foreign key(user_id) references users(id) on delete cascade              
    )''')

    #创建帖子图片表
    cursor.execute('''create table if not exists post_image(
        id integer primary key autoincrement,
        post_id integer not null,
        image_url text not null,
        sort_order integer not null,
        create_at timestamp default current_timestamp,
        foreign key(post_id) references posts(id) on delete cascade
    )''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("建表成功")
                  