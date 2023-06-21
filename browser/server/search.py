import logging
from urllib.parse import quote

from flask import request
from flask import Blueprint, current_app

from utils import require_valid_token
from common import call_open_tab


logger = logging.getLogger("autobrowser")

#valid_token = None

search_blueprint = Blueprint('search', __name__)

@search_blueprint.route('/search', methods=['GET'])
@require_valid_token
def search():
    socketio = current_app.config['socketio']
    logger.debug(f"search/: {socketio=}")
    data: dict = request.get_json()
    query = data.get('query')
    try:
        query = str(query)
    except:
        return {'status': 'error', 'result': False, 
                'message': f'Unable to convert query to string, {query=}'}, 400
    logger.debug(f"search/: {query=}")
    timeout = data.get('timeout', 60)
    logger.debug(f"search/: {timeout=}")
    max_results = data.get('max_results', 20)
    logger.debug(f"search/: {max_results=}")

    logger.debug(f"search/: calling open_tab with {socketio=}, {query=}")
    result, code = call_open_tab(socketio, 
                                 f'https://www.google.com/search?q={quote(query)}',
                                 )
    logger.debug(f"search/ call_open_tab returns: {result=}, {code=}")

    if code == 500:
        logger.debug(f"/search: failed to open tab: {result=}, {code=}")

    if code == 200:
        tab_id = result['result']
        logger.debug(f"/search: opened tab {tab_id=}")
    
    return result, code
