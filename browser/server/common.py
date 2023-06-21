import uuid

from gevent.event import Event
from gevent.timeout import Timeout

from shared_data import events_by_id, results_by_id, TIMEOUT
from utils import timeout_response

def call_open_tab(socketio, url_: str) -> tuple[dict, int]:
    event = Event()
    request_id = str(uuid.uuid4())
    socketio.emit('open_new_tab', {'url': url_, 'request_id': request_id})
    events_by_id[request_id] = event

    try:
        with Timeout(TIMEOUT):
            event.wait()
    except Timeout:
        del events_by_id[request_id]
        if request_id in results_by_id:
            del results_by_id[request_id]
        return timeout_response('openTab'), 408
    
    result = results_by_id.get(request_id)
    del events_by_id[request_id]
    del results_by_id[request_id]

    code = 200
    if not result:
        return {'status': 'error',
                'message': 'Unknown server error occured. Failed to receive a result from the browser.',
                'result': False}, 500
    if not result["result"]:
        code = 400
    return {'status': 'success' if result['result'] else 'error', 
            'result': result['result'],
            'message': result['message'] if not result['result'] else 'OK'}, code