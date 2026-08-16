# 3D 模型学习记录：数据访问层
# 模型目录元数据复用 model.model_favorite.MODEL_CATALOG
from model.model_favorite import MODEL_CATALOG


# 标记模型为已学习（重复学习不重复记录）
def mark_model_learned(db, user_id, model_id):
    cursor = db.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO model_learning(user_id, model_id) VALUES(?,?)",
        (user_id, model_id),
    )
    db.commit()


# 获取用户已学习的模型 id 列表
def get_user_learned_model_ids(db, user_id):
    cursor = db.cursor()
    cursor.execute("SELECT model_id FROM model_learning WHERE user_id=?", (user_id,))
    return [row[0] for row in cursor.fetchall()]


# 计算用户学习统计：总体 + 按教材分册
def get_user_learning_stats(db, user_id):
    learned = set(get_user_learned_model_ids(db, user_id))
    books = {}
    for m in MODEL_CATALOG:
        book = books.setdefault(m["book"], {"total": 0, "learned": 0})
        book["total"] += 1
        if m["id"] in learned:
            book["learned"] += 1
    return {
        "total": len(MODEL_CATALOG),
        "learned": sum(1 for m in MODEL_CATALOG if m["id"] in learned),
        "learned_ids": sorted(learned),
        "books": books,
    }
