from dataclasses import dataclass
from typing import Optional, Literal

@dataclass
class BasicSuccess:
    status: Optional[Literal['success']] = 'success'
    result: Optional[Literal[True]] = True
    code: Optional[Literal[200]] = 200
    message: Optional[str] = 'OK'

    def to_response(self) -> tuple[dict, int]:
        dct = {'status': self.status, 'result': self.result, 'message': self.message}
        return dct, self.code
    
@dataclass
class OpenUrlSuccess(BasicSuccess):
    message: Optional[str] = 'URL opened successfully'