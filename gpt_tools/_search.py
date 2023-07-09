from typing import Optional
from urllib.parse import quote

selector_js = """
let container = document.querySelector("#rso > div:nth-child(3)");

"""

def search(browser: "gpt_tools.Browser", 
           query: str, 
           tab_id: Optional[int]=None,
           max_results: int=20, 
           timeout: Optional[int]=None):

    assert isinstance(query, str)

    # make the URL
    url_ = f'https://www.google.com/search?q={quote(query)}'
    #open a new tab
    if not tab_id:
        tab_id = browser.open_tab(url_)
    
    assert browser.wait_for_element(tab_id, "div#main.main div#cnt div#sfooter div#footcnt div#fbarcnt div#fbar span#fsl")

    js = """
    
    """

    print (res)
