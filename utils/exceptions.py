from fastapi import HTTPException

class CustomException(HTTPException):
    def __init__(self, code: str, message: str, dev_message: str = "", status_code: int = 400, detail: str = ""):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.dev_message = dev_message
        self.detail = detail

    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
            "dev_message": self.dev_message
        } 