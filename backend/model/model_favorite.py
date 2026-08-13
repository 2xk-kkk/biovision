# 3D 模型收藏：模型目录（元数据唯一来源） + 数据访问层
# icon 为图片路径（以 ../images/ 开头）或 emoji/文字

MODEL_CATALOG = [
    # ===== 必修一 · 分子与细胞（main.html）=====
    {"id": "linzhi", "name": "磷脂双分子层", "book": "必修一",
     "desc": "构成生物膜的基本骨架，亲水头部朝外、疏水尾部朝内，形成稳定的双层结构",
     "tag": "第3章 · 细胞的基本结构", "page": "linzhi.html", "icon": "../images/plasma-membrane.png"},
    {"id": "dongwuxibao", "name": "动物细胞", "book": "必修一",
     "desc": "无细胞壁，含线粒体、内质网等细胞器，以有丝分裂方式增殖",
     "tag": "第3章 · 细胞的基本结构", "page": "dongwuxibao.html", "icon": "../images/animal-cell.png"},
    {"id": "zhiwuxibao", "name": "植物细胞", "book": "必修一",
     "desc": "具有细胞壁、叶绿体和大液泡，是光合作用和渗透作用的重要场所",
     "tag": "第3章 · 细胞的基本结构", "page": "zhiwuxibao.html", "icon": "../images/plant-cell.png"},
    {"id": "baotunbaotu", "name": "胞吞胞吐", "book": "必修一",
     "desc": "大分子物质进出细胞的方式，依赖膜的流动性，消耗ATP提供能量",
     "tag": "第4章 · 细胞的物质输入与输出", "page": "baotunbaotu.html", "icon": "../images/golgi.png"},
    {"id": "nengliang", "name": "能量转换", "book": "必修一",
     "desc": "光合作用将光能转化为化学能，呼吸作用释放能量供生命活动",
     "tag": "第5章 · 细胞的能量供应与利用", "page": "nengliang.html", "icon": "../images/mitocondria.png"},
    {"id": "yousifenlie", "name": "有丝分裂", "book": "必修一",
     "desc": "有丝分裂的全过程，染色体行为与数量变化",
     "tag": "第6章 · 细胞的生命历程", "page": "yousifenlie.html", "icon": "../images/cell-division.png"},

    # ===== 必修二 · 遗传与进化（main2.html）=====
    {"id": "fenlidinglv", "name": "分离定律", "book": "必修二",
     "desc": "成对的遗传因子在形成配子时彼此分离，分别进入不同配子。",
     "tag": "第1章 · 遗传因子的发现", "page": "fenlidinglv.html", "icon": "Aa"},
    {"id": "ziyouzhuhe", "name": "自由组合定律", "book": "必修二",
     "desc": "不同对遗传因子在形成配子时独立分离，自由组合。",
     "tag": "第1章 · 遗传因子的发现", "page": "ziyouzhuhe.html", "icon": "9331"},
    {"id": "jianshufenlie", "name": "减数分裂", "book": "必修二",
     "desc": "细胞连续分裂两次，DNA复制一次，产生四个染色体减半的配子，实现遗传重组。",
     "tag": "第2章 · 基因和染色体的关系", "page": "jianshufenlie.html", "icon": "../images/cell-division2.png"},
    {"id": "DNAfuzhi", "name": "DNA的复制", "book": "必修二",
     "desc": "在细胞分裂前，DNA双链解开，以每条链为模板，按碱基互补配对原则合成新链，形成两个完全相同的DNA分子。",
     "tag": "第3章 · 基因的本质", "page": "DNAfuzhi.html", "icon": "../images/dna.png"},
    {"id": "pro_hecheng", "name": "蛋白质的合成", "book": "必修二",
     "desc": "DNA转录为mRNA，mRNA翻译成多肽链，折叠成蛋白质。",
     "tag": "第4章 · 基因的表达", "page": "pro_hecheng.html", "icon": "../images/dna.png"},

    # ===== 选择性必修一 · 稳态与调节（main3.html）=====
    {"id": "shenjingxitong", "name": "神经系统基本结构", "book": "选择性必修一",
     "desc": "神经系统由脑、脊髓和神经组成，通过神经元传递信号。",
     "tag": "第2章 · 神经调节", "page": "shenjingxitong.html", "icon": "🧠"},
    {"id": "shenjingyuan", "name": "神经元", "book": "选择性必修一",
     "desc": "神经系统的基本结构和功能单位，由细胞体、树突和轴突组成，负责接收、整合和传递信息。",
     "tag": "第2章 · 神经调节", "page": "shenjingyuan.html", "icon": "../images/neuron.png"},
    {"id": "fanshehu", "name": "反射弧", "book": "选择性必修一",
     "desc": "完成反射活动的神经通路，包括感受器、传入神经、神经中枢、传出神经和效应器五个部分。",
     "tag": "第2章 · 神经调节", "page": "fanshehu.html", "icon": "../images/neuron3.png"},
    {"id": "shenjingchongdong", "name": "神经冲动传导", "book": "选择性必修一",
     "desc": "神经冲动沿轴突以电信号传导，经突触传递。",
     "tag": "第2章 · 神经调节", "page": "shenjingchongdong.html", "icon": "⚡"},
    {"id": "tuchu", "name": "突触", "book": "选择性必修一",
     "desc": "神经元之间或神经元与效应器之间传递信息的结构，通过神经递质实现信号的化学传递。",
     "tag": "第2章 · 神经调节", "page": "tuchu.html", "icon": "⚡"},
    {"id": "neifenmian", "name": "人体内分泌腺", "book": "选择性必修一",
     "desc": "内分泌腺分泌激素，调节稳态；下丘脑是神经—体液调节枢纽。",
     "tag": "第3章 · 体液调节", "page": "main3.html", "icon": "../images/anatomy.png"},
    {"id": "mianyiguan", "name": "人体内免疫器官", "book": "选择性必修一",
     "desc": "胸腺、骨髓、淋巴结、脾等免疫器官构成免疫系统的重要组成。",
     "tag": "第4章 · 免疫调节", "page": "main3.html", "icon": "../images/anatomy.png"},
    {"id": "tiyemianyi", "name": "体液免疫", "book": "选择性必修一",
     "desc": "B细胞受抗原刺激后分化为浆细胞，产生抗体，抗体与抗原特异性结合，清除细胞外病原体。",
     "tag": "第4章 · 免疫调节", "page": "tiyemianyi.html", "icon": "../images/virus.png"},
    {"id": "xibaomianyi", "name": "细胞免疫", "book": "选择性必修一",
     "desc": "T细胞识别被感染的靶细胞，直接杀伤或激活其他免疫细胞，清除细胞内病原体和异常细胞",
     "tag": "第4章 · 免疫调节", "page": "xibaomianyi.html", "icon": "../images/microorganism.png"},

    # ===== 选择性必修二 · 生物与环境（main4.html）=====
    {"id": "zhongqunshuliang", "name": "种群数量变化曲线", "book": "选择性必修二",
     "desc": "种群数量变化有“J”型（指数增长）和“S”型（逻辑斯谛增长，受环境容纳量K值限制）两种曲线。",
     "tag": "第1章 · 总群及其动态", "page": "zhongqunshuliang.html", "icon": "📈"},
    {"id": "qunluoyanti", "name": "群落演替", "book": "选择性必修二",
     "desc": "一个群落被另一个群落取代的过程，分为初生演替和次生演替,最终趋向稳定顶极群落。",
     "tag": "第2章 · 群落及其演替", "page": "qunluoyanti.html", "icon": "../images/medical.png"},
    {"id": "nengliuliang", "name": "能量流动", "book": "选择性必修二",
     "desc": "太阳能经生产者固定后，沿食物链单向传递，逐级递减，传递效率约为10%～20%。",
     "tag": "第3章 · 生态系统及其稳定性", "page": "nengliuliang.html", "icon": "../images/ecosystem.png"},

    # ===== 选择性必修三 · 生物技术与工程（main5.html）=====
    {"id": "jiaomujunpeiyang", "name": "酵母菌的纯培养", "book": "选择性必修三",
     "desc": "在无菌条件下，用平板划线法或稀释涂布法分离单菌落，获得单一酵母菌种群。",
     "tag": "第1章 · 发酵工程", "page": "jiaomujunpeiyang.html", "icon": "../images/bacteria.png"},
    {"id": "plantcell_zhajiao", "name": "植物体细胞杂交", "book": "选择性必修三",
     "desc": "去壁融合原生质体，培养成杂种植株，克服远缘杂交障碍。",
     "tag": "第2章 · 细胞工程", "page": "plantcell_zhajiao.html", "icon": "../images/plant.png"},
    {"id": "dankelong", "name": "单克隆抗体制备", "book": "选择性必修三",
     "desc": "B细胞与骨髓瘤细胞融合，筛选杂交瘤细胞，生产特异性抗体。",
     "tag": "第2章 · 细胞工程", "page": "dankelong.html", "icon": "../images/sample.png"},
    {"id": "shoujing", "name": "哺乳动物受精过程", "book": "选择性必修三",
     "desc": "精子获能→顶体反应→穿越透明带→透明带反应→精卵融合→原核融合，完整呈现受精全过程。",
     "tag": "第2章 · 细胞工程", "page": "shoujing.html", "icon": "../images/reproduction.png"},
    {"id": "peitaifayu", "name": "胚胎早期发育", "book": "选择性必修三",
     "desc": "受精卵→卵裂→桑葚胚→囊胚→孵化→植入→原肠胚，完整展现胚胎早期发育全过程。",
     "tag": "第2章 · 细胞工程", "page": "peitaifayu.html", "icon": "../images/embryo.png"},
    {"id": "PCR", "name": "PCR反应过程", "book": "选择性必修三",
     "desc": "PCR通过变性、退火、延伸的循环，体外快速扩增特定DNA片段。",
     "tag": "第3章 · 基因工程", "page": "PCR.html", "icon": "🧪"},
    {"id": "zaitigoujian", "name": "基因表达载体构建", "book": "选择性必修三",
     "desc": "将目的基因插入含启动子、终止子、标记基因等元件的质粒中，形成能在宿主细胞中表达的重组DNA分子。",
     "tag": "第3章 · 基因工程", "page": "zaitigoujian.html", "icon": "../images/dna.png"},
]

_MODEL_BY_ID = {m["id"]: m for m in MODEL_CATALOG}


def get_model_info(model_id):
    """根据模型 id 获取元数据，不存在返回 None"""
    return _MODEL_BY_ID.get(model_id)


# 切换收藏：已收藏则取消返回 False，否则收藏返回 True
def toggle_model_favorite(db, user_id, model_id):
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM model_favorites WHERE user_id=? AND model_id=?", (user_id, model_id))
    exists = cursor.fetchone()
    if exists:
        cursor.execute("DELETE FROM model_favorites WHERE user_id=? AND model_id=?", (user_id, model_id))
        db.commit()
        return False
    else:
        cursor.execute("INSERT INTO model_favorites(user_id, model_id) VALUES(?,?)", (user_id, model_id))
        db.commit()
        return True


# 获取用户已收藏的模型 id 列表
def get_user_favorited_model_ids(db, user_id):
    cursor = db.cursor()
    cursor.execute("SELECT model_id FROM model_favorites WHERE user_id=?", (user_id,))
    return [row[0] for row in cursor.fetchall()]


# 获取用户收藏的模型（含元数据），按收藏时间倒序
def get_user_model_favorites(db, user_id):
    cursor = db.cursor()
    cursor.execute(
        "SELECT model_id, create_at FROM model_favorites WHERE user_id=? ORDER BY create_at DESC, id DESC",
        (user_id,)
    )
    result = []
    for model_id, create_at in cursor.fetchall():
        info = get_model_info(model_id)
        if not info:
            continue
        item = dict(info)
        item["create_at"] = create_at
        result.append(item)
    return result
