from werkzeug.exceptions import HTTPException
from typing import Dict


class AbortException(HTTPException):
    def __init__(self, error: Dict, desc: str = 'Bad Request',  code: int = 400):
        super().__init__(description=desc)
        self.error = error
        self.code = code
