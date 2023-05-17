from typing import Literal, Optional, Any, Coroutine
from requests.sessions import Session
import aiohttp
import asyncio

from aiohttp import TCPConnector

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from ._browser_protocol import BrowserProtocol, BrowserAsyncProtocol, SessionProtocol

BASE_URL = "https://127.0.0.1:1837"


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
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def base_request(self, 
                    method: Literal["POST", "GET"], 
                    url: str, 
                    **kwargs) -> dict:
        # Add the token to the URL
        url += f'?token={self.token}'

        response = self.session.request(method, url, **kwargs)
        if response.status_code == 401:
            raise ValueError("Unauthorized Access. Please check your token.")
        try:
            return response.json()
        except ValueError as e:
            raise ValueError(f"Error parsing JSON: {e}")
    
    def close_tab_by_id(self, 
                        tab_id: int) -> bool:
        result = self.request("POST", f"{self.base_url}/closeTabById", json={"tab_id": tab_id})
        return result["status"] == "success"

    def tabs_list(self) -> Optional[dict]:
        result = self.request("GET", f"{self.base_url}/tabsList")
        if result["status"] == "success":
            return result['tabs']

    def open_tab(self, url: str) -> int:
        result = self.request("POST", f"{self.base_url}/openTab", json={"url": url})
        if result["status"] == "success":
            return result['result']

    def execute_script(self, 
                       tab_id: int, 
                       code: str) -> dict:
        return self.request("POST", 
                            f"{self.base_url}/executeScript", 
                            json={"tab_id": tab_id, "code": code})

    def inject_script(self, tab_id, code):
        result = self.request("POST",
                            f"{self.base_url}/injectScript",
                            json={"tab_id": tab_id, "code": code})
        if result["status"] == "success":
            return result['result']


    def wait_for_element(self, tab_id, selector, timeout=None):
        data = {"tab_id": tab_id, "selector": selector}
        if timeout:
            data["timeout"] = timeout
        print ("browser.wait_for_element called with args: ", data)
        result = self.request("POST",
                            f"{self.base_url}/waitForElement",
                            json=data)
        if result["status"] == "success":
            return True
        return False

    def get_tab_html(self, tab_id: int) -> Optional[str]:
        result = self.request("GET", f"{self.base_url}/getTabHTML/{tab_id}")
        if result["status"] == "success":
            return result['result']

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
