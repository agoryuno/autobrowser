from typing import Literal, Optional, Any, Coroutine
from typing import Union
from requests.sessions import Session
import asyncio
from urllib.parse import quote

import aiohttp
from aiohttp import TCPConnector

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ._browser_protocol import BrowserProtocol
from .exceptions import BrowserError, ServerError, PageNotFound

BASE_URL = "https://localhost"


class Browser(BrowserProtocol):
    def __init__(self, 
                 token: str, 
                 base_url: str = BASE_URL, 
                 trusted_ca: bool = True) -> None:
        self.token = token
        self.base_url = base_url

        self.session = self.create_session(trusted_ca)

    def create_session(self, 
                       trusted_ca: bool) -> Session:
        session = requests.Session()

        if not trusted_ca:
            # Disable SSL certificate verification (for self-signed certificates)
            session.verify = False

        # Retry on failure
        retries = Retry(total=5, 
                        backoff_factor=1, 
                        status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def base_request(self, 
                    method: Literal["POST", "GET"], 
                    url: str, 
                    **kwargs) -> dict:
        
        # Add the token to the URL
        #url += f'?token={quote(self.token)}'
        headers = {
           'Authorization': f'Bearer {quote(self.token)}',
        }

        if not kwargs.get("headers"):
            kwargs["headers"] = {}

        kwargs["headers"].update(headers)

        response = self.session.request(method, url, **kwargs)
        if response.status_code == 401:
            raise ValueError("Unauthorized Access. Please check your token.")
        try:
            return response.json(), response.status_code
        except ValueError as e:
            return response.text, response.status_code
    
    def _reply(self, request_result):
        result, code = request_result
        if code == 400:
            raise BrowserError(result["message"])
        if code == 404:
            raise PageNotFound(result["message"])
        if code == 408:
            raise TimeoutError(result["message"])
        if code == 500:
            raise ServerError(result)
        if result["status"] == "success":
            return result.get('result', True)
        raise Exception(f"Unknown error: {result}")

    def close_tab_by_id(self, 
                        tab_id: int):
        return self._reply(self.request("POST", 
                                 f"{self.base_url}/closeTabById", 
                                 json={"tab_id": tab_id}))

    def tabs_list(self):
         return self._reply(self.request("GET", f"{self.base_url}/tabsList"))

    def open_tab(self, url: str):
        return self._reply(self.request("POST", 
                                 f"{self.base_url}/openTab", 
                                 json={"url": url}))

    def execute_script(self, 
                       tab_id: int, 
                       code: str) -> dict:
        return self.request("POST", 
                            f"{self.base_url}/executeScript", 
                            json={"tab_id": tab_id, "code": code})

    def inject_script(self, tab_id, code):
        """
        Runs Javascript code in the context of the page. Note that
        **the code is not sandboxed** and is injected directly into the
        page's context.

        The code can return an arbitrary object by assigning it to the
        `window.result` variable.
        """
        return self._reply(self.request("POST",
                            f"{self.base_url}/injectScript",
                            json={"tab_id": tab_id, "code": code}))


    def wait_for_element(self, tab_id, selector, timeout=None):
        data = {"tab_id": tab_id, "selector": selector}
        if timeout:
            data["timeout"] = timeout
        return self._reply(self.request("POST",
                                 f"{self.base_url}/waitForElement",
                                 json=data))

    def get_tab_html(self, tab_id: int) -> Union[str, dict]:
        return self._reply(self.request("GET", f"{self.base_url}/getTabHTML/{tab_id}"))

    def search(self, query, max_results, timeout=None):
        data = {'query': query,
                'max_results': max_results}
        if timeout:
            data["timeout"] = timeout
        res = self.request("GET", 
                     f"{self.base_url}/search",
                     json=data)
        print (res)
        assert False
        return self._reply(res)

    def is_ready(self):
        result, _ = self.request("GET", f"{self.base_url}/health")
        return result["status"] == "success"

    def close(self):
        self.session.close()

    def request(self, 
                method: Literal["POST", "GET"], 
                url: str, 
                **kwargs) -> dict:
        return self.base_request(method, url, **kwargs)
    

class BrowserAsync(Browser):

    def create_session(self, trusted_ca: bool) -> aiohttp.ClientSession:
        connector = TCPConnector(ssl=not trusted_ca)
        session = aiohttp.ClientSession(
                connector=connector)
        return session

    async def base_request(self, 
                           method: Literal["POST", "GET"],
                           url: str, 
                           **kwargs) -> Coroutine[Any, Any, dict]:
        url_with_token = f"{url}?token={self.token}"
        async with self.session.request(method, url_with_token, **kwargs) as response:
            if response.status == 401:
                raise ValueError("Unauthorized Access. Please check your token.")
            try:
                return await response.json()
            except ValueError as e:
                raise ValueError(f"Error parsing JSON: {e}")

    def request(self, method, url, **kwargs):
        return asyncio.run(self.base_request(method, url, **kwargs))
