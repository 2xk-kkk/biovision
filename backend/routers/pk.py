"""
院校PK API 路由 — 同学之间通过答题比赛进行PK。
使用内存存储房间状态（适合小型应用）。
"""

import random
import time
from fastapi import APIRouter, Body
from database.db import get_db_connection
from utils.response import ApiResponse

router = APIRouter()

# 内存存储房间状态
# room_code -> { host, players: [{name, score, answers}], status, questions, current_q, start_time }
rooms = {}

# 随机配对队列：[{player_name, joined_at}]，按加入时间排序自动匹配为2人房间
match_queue = []

# 每场PK题目数
QUESTIONS_PER_ROUND = 10
# 每题答题时间（秒）
TIME_PER_QUESTION = 30


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


@router.post("/pk/create")
def create_room(player_name: str = Body(..., embed=True)):
    """创建PK房间，返回房间码"""
    code = _generate_room_code()
    rooms[code] = {
        "host": player_name,
        "players": [{"name": player_name, "score": 0, "answers": [], "ready": True}],
        "status": "waiting",  # waiting -> playing -> finished
        "questions": [],
        "current_q": 0,
        "start_time": None,
        "q_start_time": None,
        "max_players": 6,
    }
    return ApiResponse.success({"room_code": code, "player_name": player_name})


@router.post("/pk/join")
def join_room(room_code: str = Body(..., embed=True), player_name: str = Body(..., embed=True)):
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

    room["players"].append({"name": player_name, "score": 0, "answers": [], "ready": True})
    return ApiResponse.success({"room_code": room_code, "player_name": player_name})


@router.get("/pk/{room_code}")
def get_room_status(room_code: str):
    """获取房间状态"""
    room = rooms.get(room_code)
    if not room:
        return ApiResponse.error(msg="房间不存在")
    return ApiResponse.success({
        "room_code": room_code,
        "host": room["host"],
        "status": room["status"],
        "players": [{"name": p["name"], "score": p["score"], "answered": len(p["answers"])} for p in room["players"]],
        "current_q": room["current_q"],
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
    """获取当前题目"""
    room = rooms.get(room_code)
    if not room:
        return ApiResponse.error(msg="房间不存在")
    if room["status"] != "playing":
        return ApiResponse.error(msg="比赛未在进行中")
    idx = room["current_q"]
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

    # 找到玩家
    player = None
    for p in room["players"]:
        if p["name"] == player_name:
            player = p
            break
    if not player:
        return ApiResponse.error(msg="玩家不在房间中")

    # 检查是否已答过
    if any(a["q_index"] == idx for a in player["answers"]):
        return ApiResponse.error(msg="已答过此题")

    correct_answer = room["questions"][idx]["answer"].strip().upper()
    user_answer = answer.strip().upper()
    is_correct = user_answer == correct_answer

    # 计算得分（答对+10分，剩余时间奖励每秒+1分）
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

    # 检查是否所有玩家都已答题
    all_answered = all(
        any(a["q_index"] == idx for a in p["answers"])
        for p in room["players"]
    )
    # 或者超时自动进入下一题
    time_up = elapsed >= TIME_PER_QUESTION

    if all_answered or time_up:
        # 进入下一题
        room["current_q"] += 1
        room["q_start_time"] = time.time()
        if room["current_q"] >= len(room["questions"]):
            room["status"] = "finished"

    return ApiResponse.success({
        "correct": is_correct,
        "correct_answer": correct_answer,
        "score": score,
        "all_answered": all_answered,
        "time_up": time_up,
    })


@router.get("/pk/{room_code}/result")
def get_result(room_code: str):
    """获取比赛结果"""
    room = rooms.get(room_code)
    if not room:
        return ApiResponse.error(msg="房间不存在")
    if room["status"] != "finished":
        return ApiResponse.error(msg="比赛未结束")

    # 按分数排序
    ranking = sorted(room["players"], key=lambda p: p["score"], reverse=True)
    result = []
    for rank, p in enumerate(ranking, 1):
        correct_count = sum(1 for a in p["answers"] if a["correct"])
        result.append({
            "rank": rank,
            "name": p["name"],
            "score": p["score"],
            "correct": correct_count,
            "total": len(p["answers"]),
        })

    return ApiResponse.success({
        "ranking": result,
        "total_questions": len(room["questions"]),
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


# ===== 随机配对 =====

@router.post("/pk/match/join")
def join_match_queue(player_name: str = Body(..., embed=True)):
    """加入随机配对队列，匹配到对手后自动创建房间并开始"""
    global match_queue

    # 防止重名
    if any(p["player_name"] == player_name for p in match_queue):
        return ApiResponse.error(msg="该昵称已在配对队列中")

    # 若队列中有其他玩家，自动匹配
    if match_queue:
        opponent = match_queue.pop(0)
        code = _generate_room_code()
        rooms[code] = {
            "host": opponent["player_name"],
            "players": [
                {"name": opponent["player_name"], "score": 0, "answers": [], "ready": True},
                {"name": player_name, "score": 0, "answers": [], "ready": True},
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

    # 否则加入队列等待
    match_queue.append({"player_name": player_name, "joined_at": time.time()})
    queue_size = len(match_queue)
    pos = next((i for i, p in enumerate(match_queue) if p["player_name"] == player_name), 0) + 1
    return ApiResponse.success({
        "matched": False,
        "queue_size": queue_size,
        "position": pos,
        "player_name": player_name,
    })


@router.get("/pk/match/status")
def check_match_status(player_name: str):
    """查询是否已匹配到对手"""
    # 先检查是否已匹配（在某个房间中且matched=True）
    for code, room in rooms.items():
        if room.get("matched") and any(p["name"] == player_name for p in room["players"]):
            return ApiResponse.success({
                "matched": True,
                "room_code": code,
                "status": room["status"],
            })

    # 检查是否在队列中
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
