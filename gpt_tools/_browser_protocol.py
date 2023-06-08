from abc import ABC, abstractmethod
from typing import Literal, Optional, Any, Protocol, Coroutine, Tuple
from typing import Union, List, Dict
import aiohttp

from .exceptions import BrowserError, ServerError

APIReturnValue = Tuple[dict, Literal[200, 400, 408, 500]]
WaitForElementReturnValue = Union[Literal[True], BrowserError, TimeoutError, 
                                  ServerError, Exception]
OpenTabReturnValue = Union[int, BrowserError, TimeoutError, ServerError, Exception]
CloseTabByIdReturnValue = WaitForElementReturnValue
TabsListReturnValue = Union[List[Dict[str, Union[int, str]]], 
                            BrowserError, TimeoutError, ServerError, Exception]
TabHTMLReturnValue = Union[str, BrowserError, TimeoutError, ServerError, Exception]
InjectScriptReturnValue = TabHTMLReturnValue
SearchReturnValue = Union[list[dict], BrowserError, TimeoutError, ServerError, Exception]

class SessionProtocol(Protocol):
    def request(self, method: Literal["POST", "GET"], url: str, **kwargs) -> Any:
        ...


class BrowserProtocol(ABC):
    @abstractmethod
    def __init__(self, 
                 token: str, 
                 base_url: str, 
                 trusted_ca: bool) -> None:
        ...

    @abstractmethod
    def create_session(self, 
                       trusted_ca: bool) -> SessionProtocol:
        ...

    @abstractmethod
    def base_request(self, 
                     method: Literal["POST", "GET"], 
                     url: str, 
                     **kwargs) -> dict:
        ...

    @abstractmethod
    def close_tab_by_id(self, 
                        tab_id: int) -> CloseTabByIdReturnValue:
        ...

    @abstractmethod
    def tabs_list(self) -> TabsListReturnValue:
        ...

    @abstractmethod
    def open_tab(self, url: str) -> OpenTabReturnValue:
        ...

    @abstractmethod
    def execute_script(self, 
                       tab_id: int, 
                       code: str) -> dict:
        ...

    @abstractmethod
    def inject_script(self, 
                      tab_id: int, 
                      code: str) -> InjectScriptReturnValue:
        ...

    @abstractmethod
    def wait_for_element(self,
                         tab_id: int,
                         selector: str,
                         ) -> WaitForElementReturnValue:
        ...

    @abstractmethod
    def get_tab_html(self, tab_id: int) -> TabHTMLReturnValue:
        ...

    @abstractmethod
    def search(
               self, 
               query: str, 
               max_results: int, 
               timeout: Optional[int]
               ) -> SearchReturnValue:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def request(self, 
                method: Literal["POST", "GET"], 
                url: str, 
                **kwargs) -> dict:
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        ...

class BrowserAsyncProtocol(BrowserProtocol, ABC):
    @abstractmethod
    def create_session(self, trusted_ca: bool) -> aiohttp.ClientSession:
        ...

    @abstractmethod
    async def base_request(self, 
                           method: Literal["POST", "GET"],
                           url: str, 
                           **kwargs) -> Coroutine[Any, Any, dict]:
        ...

    @abstractmethod
    def request(self, method: Literal["POST", "GET"], url: str, **kwargs) -> dict:
        ...
