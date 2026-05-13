#帖子功能数据库操作

def create_post(db,user_id, content, tag):
    cursor= db.cursor()
    cursor.execute("insert into posts(user_id, content, tag) values(?,?,?)",(user_id, content, tag))
    db.commit()
    post_id = cursor.lastrowid  #获取新插入的帖子ID
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
        SELECT posts.id, posts.user_id, users.username, posts.content, posts.tag, posts.create_at
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.create_at DESC
        LIMIT ? OFFSET ?
    """, (page_size, offset))
    return cursor.fetchall()


def get_post_images_by_post_ids(db, post_ids):
    """批量获取多个帖子的图片
    
    Args:
        db: 数据库连接
        post_ids: 帖子ID列表，例如 [10, 11, 12]
    
    Returns:
        dict: {帖子ID: [图片URL列表], ...}
    """
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
    
    # 按 post_id 分组
    images_map = {}
    for row in cursor.fetchall():
        post_id = row[0]
        image_url = row[1]
        
        if post_id not in images_map:
            images_map[post_id] = []
        images_map[post_id].append(image_url)
    
    return images_map