#帖子功能数据库操作

def create_post(db,user_id, content):
    cursor= db.cursor()
    cursor.execute("insert into posts(user_id, content) values(?,?)",(user_id, content))
    db.commit()
    post_id = cursor.lastrowid  #获取新插入的帖子ID
    return post_id

def create_post_image(db, post_id, image_url, sort_order):
    cursor = db.cursor()
    cursor.execute("insert into post_image(post_id, image_url, sort_order) values(?,?,?)",(post_id, image_url, sort_order))
    db.commit()
    


    