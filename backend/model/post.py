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
                       join users on posts.user_id = users.id where posts.tag = ? limit ? offset ?''', (tag, page_size, offset))
    else:
        cursor.execute('''select posts.id, posts.user_id, users.username, posts.content, posts.create_at, posts.tag from posts 
                       join users on posts.user_id = users.id limit ? offset ?''', (page_size, offset))
    
    return cursor.fetchall()

    