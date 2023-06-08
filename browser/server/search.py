import logging
from urllib.parse import quote

from flask import request
from flask import Blueprint, current_app
from flask import redirect, url_for, session

from utils import require_valid_token_auth
from shared_data import events_by_id, results_by_id
from common import call_open_tab
from utils import setup_logger, timeout_response

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = setup_logger('/app/flask-log.txt')

logger.setLevel(logging.DEBUG)

#valid_token = None

search_blueprint = Blueprint('search', __name__)

@search_blueprint.route('/search', methods=['GET'])
@require_valid_token_auth
def search():
    query = request.args.get('query', type=str)
    timeout = request.args.get('timeout', default=60, type=int)
    max_results = request.args.get('max_results', default=20, type=int)

    result, code = call_open_tab(current_app.socketio, f'https://www.google.com/search?q={quote(query)}')

    if code == 200:
        tab_id = result['result']
        logger.debug(f"/search: opened tab {tab_id=}")
