"""
院校PK API 路由 — 同学之间通过答题比赛进行PK。
支持: 快速配对、双人对战、院校PK、排行榜。
"""

import random
import time
from fastapi import APIRouter, Body
from database.db import get_db_connection
from utils.response import ApiResponse

router = APIRouter()

# 内存存储房间状态
# room_code -> { host, college, mode, players: [{name, score, answers}], status, questions, current_q, start_time }
rooms = {}

# 随机配对队列：[{player_name, college, joined_at}]
match_queue = []

# 院校PK配对队列：[{player_name, college, joined_at}]
college_queue = []

# 每场PK题目数
QUESTIONS_PER_ROUND = 10
# 每题答题时间（秒）
TIME_PER_QUESTION = 30

# 支持的院校列表（常见高中）
COLLEGES = [
    "北京四中", "北京人大附中", "北京清华附中", "北京101中学", "北京景山学校",
    "上海中学", "上海复旦附中", "上海交大附中", "上海南模中学", "上海向明中学",
    "华师一附中", "黄冈中学", "衡水中学", "石家庄二中", "唐山一中",
    "南京外国语学校", "南京师范大学附中", "金陵中学", "苏州中学", "苏州外国语学校",
    "杭州二中", "杭州学军中学", "杭州高级中学", "宁波中学", "镇海中学",
    "成都七中", "成都外国语学校", "成都实验外国语学校", "绵阳中学", "绵阳南山中学",
    "长沙四大名校", "长沙一中", "雅礼中学", "长郡中学", "湖南师大附中",
    "广州执信中学", "广州二中", "广州六中", "广东实验中学", "深圳中学",
    "武汉外国语学校", "武汉二中", "武汉六中", "华中师大一附中",
    "重庆一中", "重庆南开中学", "重庆巴蜀中学", "重庆八中",
    "天津南开中学", "天津一中", "耀华中学", "实验中学",
    "福州一中", "厦门一中", "厦门双十中学", "泉州五中",
    "青岛二中", "青岛五十八中", "山东师大附中", "济南外国语学校",
    "郑州外国语学校", "郑州一中", "河南省实验中学", "郑州二中",
    "西安中学", "西安交大附中", "西北工大附中", "陕师大附中",
    "东北师大附中", "长春十一高", "吉林大学附中", "哈尔滨三中",
    "辽宁省实验中学", "东北育才学校", "大连育明高中", "大连二十四中",
    "昆明一中", "昆明三中", "云南师大附中", "贵阳一中",
    "兰州一中", "西北师大附中", "兰大附中", "银川一中",
    "海南中学", "海南华侨中学", "海口一中", "三亚一中",
    "河北衡水中学", "河北正定中学", "唐山一中", "保定一中",
    "其他学校"
]


def _generate_room_code():
    """生成4位房间码"""
    while True:
        code = str(random.randint(1000, 9999))
        if code not in rooms:
            return code


def _get_random_questions(count=QUESTIONS_PER_ROUND):
    """从数据库随机抽取选择题"""
    db = get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, stem, option_a, option_b, option_c, option_d, answer
            FROM questions
            WHERE option_a != '' AND option_b != '' AND answer != ''
            ORDER BY RANDOM()
            LIMIT ?
        """, (count,))
        rows = cursor.fetchall()
        questions = []
        for r in rows:
            questions.append({
                "id": r[0],
                "stem": r[1],
                "options": {
                    "A": r[2],
                    "B": r[3],
                    "C": r[4],
                    "D": r[5],
                },
                "answer": r[6],
            })
        return questions
    finally:
        db.close()


def _save_game_result(room_code, room):
    """将比赛结果保存到数据库"""
    db = get_db_connection()
    try:
        cursor = db.cursor()
        ranking = sorted(room["players"], key=lambda p: p["score"], reverse=True)
        for rank, p in enumerate(ranking, 1):
            correct_count = sum(1 for a in p["answers"] if a["correct"])
            cursor.execute("""
                INSERT INTO pk_records (room_code, player_name, college, score, correct_count, total_count, result)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (room_code, p["name"], room.get("college", ""), p["score"],
                  correct_count, len(p["answers"]), "win" if rank == 1 else "lose"))
        db.commit()
    except Exception as e:
        print(f"保存PK结果失败: {e}")
        db.rollback()
    finally:
        db.close()


# ===== 房间管理 =====

@router.post("/pk/create")
def create_room(
    player_name: str = Body(..., embed=True),
    college: str = Body("", embed=True),
    mode: str = Body("private", embed=True),
):
    """创建PK房间，返回房间码"""
    code = _generate_room_code()
    rooms[code] = {
        "host": player_name,
        "college": college,
        "mode": mode,  # private / random / college
        "players": [{"name": player_name, "score": 0, "answers": [], "ready": True}],
        "status": "waiting",
        "questions": [],
        "current_q": 0,
        "start_time": None,
        "q_start_time": None,
        "max_players": 6,
    }
    return ApiResponse.success({"room_code": code, "player_name": player_name, "college": college})


@router.post("/pk/join")
def join_room(
    room_code: str = Body(..., embed=True),
    player_name: str = Body(..., embed=True),
    college: str = Body("", embed=True),
):
    """加入PK房间"""
    room = rooms.get(room_code)
    if not room:
        return ApiResponse.error(msg="房间不存在")
    if room["status"] != "waiting":
        return ApiResponse.error(msg="比赛已开始，无法加入")
    if len(room["players"]) >= room["max_players"]:
        return ApiResponse.error(msg="房间已满")
    if any(p["name"] == player_name for p in room["players"]):
        return ApiResponse.error(msg="该昵称已被使用")

    # 如果房间有院校限制，检查匹配
    if room.get("college") and college and room["college"] != college:
        return ApiResponse.error(msg=f"该房间仅限 {room['college']} 同学加入")

    room["players"].append({
        "name": player_name, "score": 0, "answers": [], "ready": True,
        "college": college
    })
    return ApiResponse.success({"room_code": room_code, "player_name": player_name})


@router.get("/pk/colleges")
def get_colleges():
    """获取支持的院校列表"""
    return ApiResponse.success({"colleges": COLLEGES})


@router.get("/pk/{room_code}")
def get_room_status(room_code: str):
    """获取房间状态（自动超时推进）"""
    room = rooms.get(room_code)
    if not room:
        return ApiResponse.error(msg="房间不存在")

    # 自动超时推进
    if room["status"] == "playing" and room["q_start_time"]:
        elapsed = time.time() - room["q_start_time"]
        idx = room["current_q"]
        if elapsed >= TIME_PER_QUESTION and idx < len(room["questions"]):
            for p in room["players"]:
                if not any(a["q_index"] == idx for a in p["answers"]):
                    p["answers"].append({
                        "q_index": idx,
                        "answer": "",
                        "correct": False,
                        "score": 0,
                    })
            room["current_q"] += 1
            room["q_start_time"] = time.time()
            if room["current_q"] >= len(room["questions"]):
                room["status"] = "finished"
                _save_game_result(room_code, room)

    idx = room["current_q"]
    return ApiResponse.success({
        "room_code": room_code,
        "host": room["host"],
        "college": room.get("college", ""),
        "mode": room.get("mode", "private"),
        "status": room["status"],
        "players": [
            {
                "name": p["name"],
                "score": p["score"],
                "college": p.get("college", ""),
                "answered": any(a["q_index"] == idx for a in p["answers"]),
                "correct_count": sum(1 for a in p["answers"] if a["correct"]),
                "total_answered": len(p["answers"]),
            }
            for p in room["players"]
        ],
        "current_q": idx,
        "total_q": len(room["questions"]),
        "q_start_time": room["q_start_time"],
        "time_per_q": TIME_PER_QUESTION,
    })


@router.post("/pk/{room_code}/start")
def start_game(room_code: str, player_name: str = Body(..., embed=True)):
    """开始PK比赛（仅房主可操作）"""
    room = rooms.get(room_code)
    if not room:
        return ApiResponse.error(msg="房间不存在")
    if room["host"] != player_name:
        return ApiResponse.error(msg="只有房主才能开始比赛")
    if room["status"] != "waiting":
        return ApiResponse.error(msg="比赛已经开始")
    if len(room["players"]) < 2:
        return ApiResponse.error(msg="至少需要2名玩家才能开始")

    room["questions"] = _get_random_questions()
    room["status"] = "playing"
    room["current_q"] = 0
    room["start_time"] = time.time()
    room["q_start_time"] = time.time()
    return ApiResponse.success({"msg": "比赛开始", "total_q": len(room["questions"])})


@router.get("/pk/{room_code}/question")
def get_current_question(room_code: str):
    """获取当前题目（自动超时推进）"""
    room = rooms.get(room_code)
    if not room:
        return ApiResponse.error(msg="房间不存在")
    if room["status"] != "playing":
        return ApiResponse.error(msg="比赛未在进行中")

    idx = room["current_q"]

    # 自动超时推进
    if room["q_start_time"]:
        elapsed = time.time() - room["q_start_time"]
        if elapsed >= TIME_PER_QUESTION and idx < len(room["questions"]):
            for p in room["players"]:
                if not any(a["q_index"] == idx for a in p["answers"]):
                    p["answers"].append({
                        "q_index": idx,
                        "answer": "",
                        "correct": False,
                        "score": 0,
                    })
            room["current_q"] += 1
            room["q_start_time"] = time.time()
            idx = room["current_q"]
            if idx >= len(room["questions"]):
                room["status"] = "finished"
                _save_game_result(room_code, room)
                return ApiResponse.error(msg="题目已答完")

    if idx >= len(room["questions"]):
        return ApiResponse.error(msg="题目已答完")

    q = room["questions"][idx]
    elapsed = time.time() - (room["q_start_time"] or time.time())
    remaining = max(0, TIME_PER_QUESTION - int(elapsed))
    return ApiResponse.success({
        "question_index": idx + 1,
        "total": len(room["questions"]),
        "stem": q["stem"],
        "options": q["options"],
        "remaining": remaining,
        "time_limit": TIME_PER_QUESTION,
    })


@router.post("/pk/{room_code}/answer")
def submit_pk_answer(
    room_code: str,
    player_name: str = Body(..., embed=True),
    answer: str = Body(..., embed=True),
):
    """提交当前题目的答案"""
    room = rooms.get(room_code)
    if not room:
        return ApiResponse.error(msg="房间不存在")
    if room["status"] != "playing":
        return ApiResponse.error(msg="比赛未在进行中")

    idx = room["current_q"]
    if idx >= len(room["questions"]):
        return ApiResponse.error(msg="题目已答完")

    player = None
    for p in room["players"]:
        if p["name"] == player_name:
            player = p
            break
    if not player:
        return ApiResponse.error(msg="玩家不在房间中")

    if any(a["q_index"] == idx for a in player["answers"]):
        return ApiResponse.error(msg="已答过此题")

    correct_answer = room["questions"][idx]["answer"].strip().upper()
    user_answer = answer.strip().upper()
    is_correct = user_answer == correct_answer

    elapsed = time.time() - (room["q_start_time"] or time.time())
    remaining = max(0, TIME_PER_QUESTION - int(elapsed))
    score = 10 + remaining if is_correct else 0
    player["answers"].append({
        "q_index": idx,
        "answer": user_answer,
        "correct": is_correct,
        "score": score,
    })
    player["score"] += score

    all_answered = all(
        any(a["q_index"] == idx for a in p["answers"])
        for p in room["players"]
    )

    if all_answered:
        room["current_q"] += 1
        room["q_start_time"] = time.time()
        if room["current_q"] >= len(room["questions"]):
            room["status"] = "finished"
            _save_game_result(room_code, room)

    return ApiResponse.success({
        "correct": is_correct,
        "correct_answer": correct_answer,
        "score": score,
        "all_answered": all_answered,
    })


@router.get("/pk/{room_code}/result")
def get_result(room_code: str):
    """获取比赛结果"""
    room = rooms.get(room_code)
    if not room:
        return ApiResponse.error(msg="房间不存在")
    if room["status"] != "finished":
        return ApiResponse.error(msg="比赛未结束")

    ranking = sorted(room["players"], key=lambda p: p["score"], reverse=True)
    result = []
    for rank, p in enumerate(ranking, 1):
        correct_count = sum(1 for a in p["answers"] if a["correct"])
        result.append({
            "rank": rank,
            "name": p["name"],
            "score": p["score"],
            "college": p.get("college", ""),
            "correct": correct_count,
            "total": len(p["answers"]),
        })

    return ApiResponse.success({
        "ranking": result,
        "total_questions": len(room["questions"]),
        "college": room.get("college", ""),
    })


@router.post("/pk/{room_code}/leave")
def leave_room(room_code: str, player_name: str = Body(..., embed=True)):
    """离开房间"""
    room = rooms.get(room_code)
    if not room:
        return ApiResponse.error(msg="房间不存在")
    room["players"] = [p for p in room["players"] if p["name"] != player_name]
    if not room["players"]:
        del rooms[room_code]
    return ApiResponse.success({"msg": "已离开房间"})


# ===== 排行榜 =====

@router.get("/pk/stats/rank")
def get_leaderboard(
    period: str = "weekly",
    college: str = "",
    top_n: int = 20,
):
    """获取PK排行榜"""
    db = get_db_connection()
    try:
        cursor = db.cursor()
        if college:
            cursor.execute("""
                SELECT player_name, college,
                       SUM(score) as total_score,
                       SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                       COUNT(*) as games,
                       ROUND(AVG(CASE WHEN result = 'win' THEN 1.0 ELSE 0.0 END) * 100, 1) as win_rate
                FROM pk_records
                WHERE college = ?
                GROUP BY player_name, college
                ORDER BY total_score DESC
                LIMIT ?
            """, (college, top_n))
        else:
            cursor.execute("""
                SELECT player_name, college,
                       SUM(score) as total_score,
                       SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                       COUNT(*) as games,
                       ROUND(AVG(CASE WHEN result = 'win' THEN 1.0 ELSE 0.0 END) * 100, 1) as win_rate
                FROM pk_records
                GROUP BY player_name, college
                ORDER BY total_score DESC
                LIMIT ?
            """, (top_n,))

        rows = cursor.fetchall()
        ranking = []
        for i, r in enumerate(rows):
            ranking.append({
                "rank": i + 1,
                "player_name": r[0],
                "college": r[1],
                "score": r[2],
                "wins": r[3],
                "games": r[4],
                "win_rate": r[5],
            })

        # 院校排行
        cursor.execute("""
            SELECT college,
                   SUM(score) as total_score,
                   COUNT(DISTINCT player_name) as player_count,
                   COUNT(*) as games
            FROM pk_records
            WHERE college != ''
            GROUP BY college
            ORDER BY total_score DESC
            LIMIT 10
        """)
        college_rows = cursor.fetchall()
        college_ranking = []
        for i, r in enumerate(college_rows):
            college_ranking.append({
                "rank": i + 1,
                "college": r[0],
                "total_score": r[1],
                "player_count": r[2],
                "games": r[3],
            })

        # 获取今日/本周新增数据统计
        cursor.execute("SELECT COUNT(*) FROM pk_records")
        total_games = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT player_name) FROM pk_records")
        total_players = cursor.fetchone()[0]

        return ApiResponse.success({
            "ranking": ranking,
            "college_ranking": college_ranking,
            "stats": {
                "total_games": total_games,
                "total_players": total_players,
            }
        })
    finally:
        db.close()


# ===== 随机配对 =====

@router.post("/pk/match/join")
def join_match_queue(
    player_name: str = Body(..., embed=True),
    college: str = Body("", embed=True),
):
    """加入随机配对队列"""
    global match_queue

    if any(p["player_name"] == player_name for p in match_queue):
        return ApiResponse.error(msg="该昵称已在配对队列中")

    if match_queue:
        opponent = match_queue.pop(0)
        code = _generate_room_code()
        rooms[code] = {
            "host": opponent["player_name"],
            "college": college or opponent.get("college", ""),
            "mode": "random",
            "players": [
                {"name": opponent["player_name"], "score": 0, "answers": [], "ready": True,
                 "college": opponent.get("college", "")},
                {"name": player_name, "score": 0, "answers": [], "ready": True,
                 "college": college},
            ],
            "status": "waiting",
            "questions": [],
            "current_q": 0,
            "start_time": None,
            "q_start_time": None,
            "max_players": 6,
            "matched": True,
        }
        return ApiResponse.success({
            "matched": True,
            "room_code": code,
            "opponent": opponent["player_name"],
            "player_name": player_name,
        })

    match_queue.append({"player_name": player_name, "college": college, "joined_at": time.time()})
    pos = len(match_queue)
    return ApiResponse.success({
        "matched": False,
        "queue_size": len(match_queue),
        "position": pos,
        "player_name": player_name,
    })


@router.get("/pk/match/status")
def check_match_status(player_name: str):
    """查询是否已匹配到对手"""
    for code, room in rooms.items():
        if room.get("matched") and any(p["name"] == player_name for p in room["players"]):
            return ApiResponse.success({
                "matched": True,
                "room_code": code,
                "status": room["status"],
            })

    pos = next((i for i, p in enumerate(match_queue) if p["player_name"] == player_name), None)
    if pos is not None:
        return ApiResponse.success({
            "matched": False,
            "queue_size": len(match_queue),
            "position": pos + 1,
            "wait_seconds": int(time.time() - match_queue[pos]["joined_at"]),
        })

    return ApiResponse.error(msg="不在配对队列中")


@router.post("/pk/match/cancel")
def cancel_match_queue(player_name: str = Body(..., embed=True)):
    """取消随机配对"""
    global match_queue
    before = len(match_queue)
    match_queue = [p for p in match_queue if p["player_name"] != player_name]
    after = len(match_queue)
    if before == after:
        return ApiResponse.error(msg="不在配对队列中")
    return ApiResponse.success({"msg": "已取消配对", "queue_size": after})


# ===== 院校PK配对 =====

@router.post("/pk/college/join")
def join_college_queue(
    player_name: str = Body(..., embed=True),
    college: str = Body(..., embed=True),
):
    """加入院校PK配对队列"""
    global college_queue

    if not college:
        return ApiResponse.error(msg="请选择院校")

    if any(p["player_name"] == player_name for p in college_queue):
        return ApiResponse.error(msg="该昵称已在院校配对队列中")

    # 优先匹配同院校的对手
    same_college = [p for p in college_queue if p["college"] == college]
    if same_college:
        opponent = same_college[0]
        college_queue.remove(opponent)
        code = _generate_room_code()
        rooms[code] = {
            "host": opponent["player_name"],
            "college": college,
            "mode": "college",
            "players": [
                {"name": opponent["player_name"], "score": 0, "answers": [], "ready": True,
                 "college": college},
                {"name": player_name, "score": 0, "answers": [], "ready": True,
                 "college": college},
            ],
            "status": "waiting",
            "questions": [],
            "current_q": 0,
            "start_time": None,
            "q_start_time": None,
            "max_players": 6,
            "matched": True,
        }
        return ApiResponse.success({
            "matched": True,
            "room_code": code,
            "opponent": opponent["player_name"],
            "player_name": player_name,
            "college": college,
        })

    # 否则加入院校队列等待
    college_queue.append({"player_name": player_name, "college": college, "joined_at": time.time()})
    pos = next((i for i, p in enumerate(college_queue)
                if p["player_name"] == player_name), 0) + 1
    college_pos = next((i for i, p in enumerate(
        [p for p in college_queue if p["college"] == college]
    ) if p["player_name"] == player_name), 0) + 1

    return ApiResponse.success({
        "matched": False,
        "queue_size": len(college_queue),
        "position": pos,
        "college_position": college_pos,
        "college": college,
        "player_name": player_name,
    })


@router.get("/pk/college/status")
def check_college_status(player_name: str):
    """查询院校配对状态"""
    for code, room in rooms.items():
        if room.get("matched") and room.get("mode") == "college" and \
                any(p["name"] == player_name for p in room["players"]):
            return ApiResponse.success({
                "matched": True,
                "room_code": code,
                "status": room["status"],
                "college": room.get("college", ""),
            })

    pos = next((i for i, p in enumerate(college_queue)
                if p["player_name"] == player_name), None)
    if pos is not None:
        college = college_queue[pos]["college"]
        same_count = len([p for p in college_queue if p["college"] == college])
        same_pos = next((i for i, p in enumerate(
            [p for p in college_queue if p["college"] == college]
        ) if p["player_name"] == player_name), 0) + 1
        return ApiResponse.success({
            "matched": False,
            "college": college,
            "queue_size": len(college_queue),
            "same_college_size": same_count,
            "college_position": same_pos,
            "wait_seconds": int(time.time() - college_queue[pos]["joined_at"]),
        })

    return ApiResponse.error(msg="不在院校配对队列中")


@router.post("/pk/college/cancel")
def cancel_college_queue(player_name: str = Body(..., embed=True)):
    """取消院校配对"""
    global college_queue
    before = len(college_queue)
    college_queue = [p for p in college_queue if p["player_name"] != player_name]
    after = len(college_queue)
    if before == after:
        return ApiResponse.error(msg="不在院校配对队列中")
    return ApiResponse.success({"msg": "已取消院校配对", "queue_size": after})