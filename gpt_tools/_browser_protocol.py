from abc import ABC, abstractmethod
from typing import Literal, Optional, Any, Protocol, Coroutine, Tuple
import aiohttp

APIReturnValue = Tuple[dict, Literal[200, 400, 408, 500]]

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
                        tab_id: int) -> APIReturnValue:
        ...

    @abstractmethod
    def tabs_list(self) -> Optional[dict]:
        ...

    @abstractmethod
    def open_tab(self, url: str) -> APIReturnValue:
        ...

    @abstractmethod
    def execute_script(self, 
                       tab_id: int, 
                       code: str) -> dict:
        ...

    @abstractmethod
    def inject_script(self, 
                      tab_id: int, 
                      code: str) -> Any:
        ...

    @abstractmethod
    def wait_for_element(self,
                         tab_id: int,
                         selector: str,
                         ) -> bool:
        ...

    @abstractmethod
    def get_tab_html(self, tab_id: int) -> Optional[str]:
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
