#ApiResponse 统一返回格式


class ApiResponse:
    @staticmethod
    def success(data=None, msg="Success"):
        return {
            "success": True,
            "msg": msg,
            "data": data
        }
    
    @staticmethod
    def error( data=None,msg="Error"):
        return {
            "success": False,
            "msg": msg,
            "data": data
        }