import logging
from urllib.parse import quote

from flask import request
from flask import Blueprint, current_app

from utils import require_valid_token, is_valid_url
from common import call_open_tab, load_url_in_tab
from errors import ArgumentTypeError, UnableToCreateTabError
from errors import ArgumentMissingError
from successes import OpenUrlSuccess


logger = logging.getLogger("autobrowser")

#valid_token = None

openUrl_blueprint = Blueprint('search', __name__)

@openUrl_blueprint.route('/openUrl', methods=['POST'])
@require_valid_token
def openUrl():
    socketio = current_app.config['socketio']
    data = request.get_json()
    logger.debug(f"openUrl/: {data=}")
    url_ = data.get('url')
    try:
        url_ = str(url_)
    except:
        raise ArgumentTypeError(message=f'Unable to convert URL to string, URL={url_}')

    if not is_valid_url(url_):
        raise ArgumentTypeError(message=f'Invalid URL={url_}. URL must be fully qualified, e.g. https://www.google.com')

    tab_id = data.get('tab_id')
    if not tab_id:
        #result, code = call_open_tab(socketio, url_)
        logger.debug(f"openUrl/: called without tab ID")
        raise ArgumentMissingError(message=f"openUrl called without tab ID")
        #if code == 200:
        #    tab_id = result.get('result')
        #    if not tab_id:
        #        raise UnableToCreateTabError(message=f"/openUrl endpoint wasn't able to create a new tab for URL={url_}")
        #    logger.debug(f"openUrl/: opened tab {tab_id=}")
    result, code = load_url_in_tab(socketio, tab_id, url_)
    logger.debug(f"openUrl/: load_url_in_tab returns: {result=}, {code=}")

    if code == 200:
        return OpenUrlSuccess().to_response()

