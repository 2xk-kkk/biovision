class ApiResponse:
    @staticmethod
    def success(data=None, msg="Success"):
        return {
            "code": 200,
            "success": True,
            "msg": msg,
            "data": data
        }
    
    @staticmethod
    def error(data=None, msg="Error"):
        return {
            "code": 500,
            "success": False,
            "msg": msg,
            "data": data
        }