"""
This blueprint is for endpoints manipulating the
browser's tabs.
"""

import logging
from urllib.parse import quote
import uuid

from flask import request
from flask import Blueprint, current_app

from gevent.event import Event
from gevent.timeout import Timeout

from utils import require_valid_token, timeout_response
from common import call_open_tab

from shared_data import events_by_id, results_by_id, TIMEOUT


logger = logging.getLogger("autobrowser")

tabs_blueprint = Blueprint('tabs', __name__)


@tabs_blueprint.route('/tabsList', methods=['GET'])
@require_valid_token
def get_tabs():
    socketio = current_app.config['socketio']
    event = Event()
    request_id = str(uuid.uuid4())
    events_by_id[request_id] = event

    logger.debug(f'get_tabs: {request_id=}')
    logger.debug('get_tabs: emitting tabs_list event')
    socketio.emit('tabs_list', {'request_id': request_id})

    try:
        with Timeout(TIMEOUT):  # Set a timeout (e.g., 10 seconds) to avoid blocking indefinitely
            event.wait()
    except Timeout:
        del events_by_id[request_id]
        if request_id in results_by_id:
            del results_by_id[request_id]
        return timeout_response('tabsList'), 408

    tabs = results_by_id.get(request_id)
    del events_by_id[request_id]
    del results_by_id[request_id]
    if tabs['result']:
        return {'status': 'success', 'result': [tab for tab in tabs['result']],
            'message': 'OK'}, 200
    return {'status': 'error', 'message': tabs['message'], 'result': False}, 400


@tabs_blueprint.route('/openTab', methods=['POST'])
@require_valid_token
def open_tab():
    logger.debug(f"open_tab: {request.json=}")
    socketio = current_app.config['socketio']
    _url = request.json['url']
    logger.debug(f"open_tab: call_open_tab() with {_url=}")
    result, code = call_open_tab(socketio, _url)
    logger.debug(f"open_tab: call_open_tab() returned {result=}, {code=}")

    return result, code


@tabs_blueprint.route('/closeTabById', methods=['POST'])
@require_valid_token
def close_tab_by_id():
    socketio = current_app.config['socketio']
    tab_id = request.json['tab_id']
    event = Event()
    request_id = str(uuid.uuid4())
    events_by_id[request_id] = event

    socketio.emit('close_tab_by_id', {'tab_id': tab_id, 'request_id': request_id})

    try:
        with Timeout(TIMEOUT):
            event.wait()
    except Timeout:
        del events_by_id[request_id]
        if request_id in results_by_id:
            del results_by_id[request_id]
        return timeout_response('closeTabById'), 408

    result = results_by_id.get(request_id)
    del events_by_id[request_id]
    del results_by_id[request_id]

    if not result["result"]:
        return {'status': 'error', 'message': result["message"]}, 400

    return {'status': 'success', 'message': ''}, 200
