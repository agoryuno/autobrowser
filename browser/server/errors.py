from dataclasses import dataclass
from typing import Optional


@dataclass
class BasicError(Exception):
    status: Optional[str] = 'error'
    result: Optional[bool] = False
    code: Optional[int] = 400
    message: Optional[str] = 'Error'

    def to_response(self) -> tuple[dict, int]:
        dct = {'status': self.status, 'result': self.result, 'message': self.message}
        return dct, self.code

@dataclass
class ArgumentTypeError(BasicError):
    message: Optional[str] = 'Invalid argument type'


@dataclass
class TimeoutError(BasicError):
    message: Optional[str] = 'Timeout reached while waiting for response'
    code: Optional[int] = 408


@dataclass
class PageNotFoundError(BasicError):
    message: Optional[str] = "URL not found"
    code: Optional[int] = 404


@dataclass
class TabNotFoundError(BasicError):
    message: Optional[str] = 'No tab with given ID was found'
    code: Optional[int] = 400


@dataclass
class UnknownServerError(BasicError):
    message: Optional[str] = 'Unknown server error occured.'
    code: Optional[int] = 500

@dataclass
class UnableToCreateTabError(BasicError):
    message: Optional[str] = 'Unable to create tab'
    code: Optional[int] = 500



if __name__ == "__main__":
    url_ = 123
    err = TimeoutError()
    print (err.to_response())