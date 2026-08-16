import json
from fastapi.responses import Response


class ApiResponse:
    @staticmethod
    def _to_response(code: int, success: bool, msg: str, data):
        payload = {
            "code": code,
            "success": success,
            "msg": msg,
            "data": data,
        }
        # 显式 ensure_ascii=False + charset=utf-8，彻底避免中文被转义导致前端乱码
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return Response(
            content=body,
            status_code=200,
            media_type="application/json; charset=utf-8",
        )

    @staticmethod
    def success(data=None, msg="Success"):
        return ApiResponse._to_response(200, True, msg, data)

    @staticmethod
    def error(data=None, msg="Error"):
        return ApiResponse._to_response(500, False, msg, data)