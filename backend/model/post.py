# 帖子功能数据库操作

def create_post(db,user_id, content, tag):
    cursor= db.cursor()
    cursor.execute("insert into posts(user_id, content, tag) values(?,?,?)",(user_id, content, tag))
    db.commit()
    post_id = cursor.lastrowid
    return post_id

def create_post_image(db, post_id, image_url, sort_order):
    cursor = db.cursor()
    cursor.execute("insert into post_image(post_id, image_url, sort_order) values(?,?,?)",(post_id, image_url, sort_order))
    db.commit()
    
def get_post_images(db, post_ids):
    cursor = db.cursor()
    placeholders = ",".join(["?"] * len(post_ids))
    cursor.execute(f"select post_id, image_url from post_image where post_id in ({placeholders}) order by post_id, sort_order", post_ids)
    images_dict = {}
    for row in cursor.fetchall():
        post_id = row[0]
        if post_id not in images_dict:
            images_dict[post_id] = []
        images_dict[post_id].append(row[1])
    return images_dict

def get_posts_by_tag_db(db, tag, page=1, page_size=10):
    cursor = db.cursor()
    offset = (page-1) * page_size
    
    if tag:
        cursor.execute('''select posts.id, posts.user_id, users.username, posts.content, posts.create_at, posts.tag from posts 
                       join users on posts.user_id = users.id where posts.tag = ? order by posts.create_at desc limit ? offset ?''', (tag, page_size, offset))
    else:
        cursor.execute('''select posts.id, posts.user_id, users.username, posts.content, posts.create_at, posts.tag from posts 
                       join users on posts.user_id = users.id order by posts.create_at desc limit ? offset ?''', (page_size, offset))
    
    return cursor.fetchall()

def get_posts(db, page=1, page_size=20):
    cursor = db.cursor()
    offset = (page - 1) * page_size
    
    cursor.execute("""
        SELECT posts.id, posts.user_id, users.username, posts.content, posts.tag, posts.create_at,
               posts.view_count, posts.like_count, posts.collect_count
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.create_at DESC
        LIMIT ? OFFSET ?
    """, (page_size, offset))
    return cursor.fetchall()


def get_post_images_by_post_ids(db, post_ids):
    if not post_ids:
        return {}
    
    cursor = db.cursor()
    placeholders = ','.join(['?'] * len(post_ids))
    
    cursor.execute(f"""
        SELECT post_id, image_url, sort_order
        FROM post_image
        WHERE post_id IN ({placeholders})
        ORDER BY post_id, sort_order
    """, post_ids)
    
    images_map = {}
    for row in cursor.fetchall():
        post_id = row[0]
        image_url = row[1]
        
        if post_id not in images_map:
            images_map[post_id] = []
        images_map[post_id].append(image_url)
    
    return images_map


# 1. 获取单篇帖子详情（浏览量+1）
def get_post_detail(db, post_id):
    cursor = db.cursor()
    cursor.execute('''
        SELECT 
            posts.id, posts.user_id, users.username,
            posts.content, posts.tag, posts.create_at,
            posts.view_count, posts.like_count, posts.collect_count
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.id = ?
    ''', (post_id,))
    return cursor.fetchone()

# 2. 编辑帖子-
def update_post(db, post_id, content, tag):
    cursor = db.cursor()
    cursor.execute('''
        UPDATE posts 
        SET content = ?, tag = ?
        WHERE id = ?
    ''', (content, tag, post_id))
    db.commit()


# 3. 删除帖子图片
def delete_post_images(db, post_id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM post_image WHERE post_id = ?", (post_id,))
    db.commit()


# 4. 删除帖子
def delete_post(db, post_id):
    delete_post_images(db, post_id)
    cursor = db.cursor()
    cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()

# 5. 浏览量 +1
def add_view_count(db, post_id):
    cursor = db.cursor()
    cursor.execute("UPDATE posts SET view_count = view_count + 1 WHERE id = ?", (post_id,))
    db.commit()


# 6. 分享数 +1
def add_share_count(db, post_id):
    cursor = db.cursor()
    cursor.execute("UPDATE posts SET share_count = share_count + 1 WHERE id = ?", (post_id,))
    db.commit()


# 7. 获取帖子作者ID
def get_post_user_id(db, post_id):
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
    res = cursor.fetchone()
    return res[0] if res else None


# 8. 帖子总数
def get_posts_count(db, tag=None):
    cursor = db.cursor()
    if tag:
        cursor.execute("SELECT COUNT(*) FROM posts WHERE tag = ?", (tag,))
    else:
        cursor.execute("SELECT COUNT(*) FROM posts")
    return cursor.fetchone()[0]


# 点赞
def toggle_like(db, user_id, post_id):
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM user_interact WHERE user_id=? AND post_id=? AND type='like'", 
                   (user_id, post_id))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("DELETE FROM user_interact WHERE user_id=? AND post_id=? AND type='like'", 
                       (user_id, post_id))
        cursor.execute("UPDATE posts SET like_count = like_count - 1 WHERE id=?", (post_id,))
        return False
    else:
        cursor.execute("INSERT INTO user_interact(user_id, post_id, type) VALUES(?,?,'like')", 
                       (user_id, post_id))
        cursor.execute("UPDATE posts SET like_count = like_count + 1 WHERE id=?", (post_id,))
        return True


def is_liked(db, user_id, post_id):
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM user_interact WHERE user_id=? AND post_id=? AND type='like'", 
                   (user_id, post_id))
    return cursor.fetchone() is not None


# 收藏
def toggle_collect(db, user_id, post_id):
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM user_interact WHERE user_id=? AND post_id=? AND type='collect'", 
                   (user_id, post_id))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("DELETE FROM user_interact WHERE user_id=? AND post_id=? AND type='collect'", 
                       (user_id, post_id))
        cursor.execute("UPDATE posts SET collect_count = collect_count - 1 WHERE id=?", (post_id,))
        return False
    else:
        cursor.execute("INSERT INTO user_interact(user_id, post_id, type) VALUES(?,?,'collect')", 
                       (user_id, post_id))
        cursor.execute("UPDATE posts SET collect_count = collect_count + 1 WHERE id=?", (post_id,))
        return True


def is_collected(db, user_id, post_id):
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM user_interact WHERE user_id=? AND post_id=? AND type='collect'", 
                   (user_id, post_id))
    return cursor.fetchone() is not None


#  获取用户收藏的帖子列表
def get_user_collect_posts(db, user_id, page=1, page_size=10):
    offset = (page-1)*page_size
    cursor = db.cursor()
    sql = '''
        SELECT p.id, p.user_id, u.username, p.content, p.tag, p.create_at,
               p.view_count, p.like_count, p.collect_count
        FROM user_interact c
        JOIN posts p ON c.post_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE c.user_id = ? AND c.type='collect'
        ORDER BY c.create_at DESC
        LIMIT ? OFFSET ?
    '''
    cursor.execute(sql, (user_id, page_size, offset))
    return cursor.fetchall()


# 评论功能（新增）
def create_comment(db, post_id, user_id, content):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO comments(post_id, user_id, content) VALUES(?,?,?)",
        (post_id, user_id, content)
    )
    db.commit()
    return cursor.lastrowid


def get_post_comments(db, post_id):
    cursor = db.cursor()
    cursor.execute('''
        SELECT c.id, c.user_id, u.username, c.content, c.create_at, c.like_count
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.create_at ASC
    ''', (post_id,))
    return cursor.fetchall()


# 获取某个用户发布的所有帖子
def get_user_posts(db, user_id, page=1, page_size=10):
    offset = (page-1)*page_size
    cursor = db.cursor()
    cursor.execute('''
        SELECT p.id, p.user_id, u.username, p.content, p.tag, p.create_at,
               p.view_count, p.like_count, p.collect_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.user_id = ?
        ORDER BY p.create_at DESC
        LIMIT ? OFFSET ?
    ''', (user_id, page_size, offset))
    return cursor.fetchall()