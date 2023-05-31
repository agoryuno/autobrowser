import uuid

from gevent import monkey
monkey.patch_all()

import configparser
import logging

from gevent.event import Event
from gevent.timeout import Timeout

import argparse

from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

import utils
from utils import read_token_from_file
from utils import require_valid_token
from auth import auth_blueprint, requires_login
from utils import setup_logger
from socket_manager import SocketManager

sock_status = SocketManager()

logger = setup_logger('/app/flask-log.txt')

logger.setLevel(logging.DEBUG)

# The dictionary to hold request ids
events_by_id = {}
# The dictionary to hold request results
results_by_id = {}

# Set up command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('token_file', help='Path to the file containing the security token')
parser.add_argument('config_file', help='Path to the config file')
args = parser.parse_args()

config = configparser.ConfigParser()
config.read(args.config_file)

HOST = config['FIREFOX']['SERVER_HOST']
PORT = int(config['FIREFOX']['SERVER_PORT'])
TIMEOUT = int(config['FLASK']['TIMEOUT'])

# Read security token from file
valid_token = read_token_from_file(args.token_file)
utils.valid_token = valid_token

print (f"App set valid token to: {valid_token}")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = valid_token

# Register blueprints
app.register_blueprint(auth_blueprint, url_prefix='/')

socketio = SocketIO(app,
                    cors_allowed_origins="*", 
                    async_mode='gevent',
                    )

connected_sockets = set()

# Define HTML content
html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPT browser</title>
</head>
<body>
<h1>GPT_tools browser</h1>
<p>Successfully authenticated and ready for work.</p>
</body>
</html>
'''

# Create a route for the root path
@app.route('/')
@requires_login
def root():
    logger.debug('root() called')
    # Return the HTML content as a response with a content type of 'text/html'
    return Response(html_content, content_type='text/html')

@app.route('/closeTabByUrl', methods=['POST'])
@require_valid_token
def close_tab_by_url():
    _url = request.json['url']
    event = Event()
    request_id = str(uuid.uuid4())
    events_by_id[request_id] = event

    socketio.emit('close_tab_by_url', {'url': _url, 'request_id': request_id})

    try:
        with Timeout(TIMEOUT):
            event.wait()
    except Timeout:
        del events_by_id[request_id]
        return {'status': 'error', 'message': 'Timeout waiting for closeTabByUrl',
                'error': 'timeout'}, 408

    result = results_by_id.get(request_id)
    del events_by_id[request_id]
    del results_by_id[request_id]
    return {'status': 'success' if result else 'error', 'result': result}


@app.route('/closeTabById', methods=['POST'])
@require_valid_token
def close_tab_by_id():
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
        return {'status': 'error', 'message': 'timeout'}, 408

    result = results_by_id.get(request_id)
    del events_by_id[request_id]
    del results_by_id[request_id]

    if not result["result"]:
        return {'status': 'error', 'message': result["message"]}, 400

    return {'status': 'success', 'message': ''}, 200


@app.route('/tabsList', methods=['GET'])
@require_valid_token
def get_tabs():
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
        return {'status': 'error', 'message': 'Timeout waiting for tabsList',
                'result': 'timeout'}, 408

    tabs = results_by_id.get(request_id)
    del events_by_id[request_id]
    del results_by_id[request_id]
    if tabs['result']:
        return {'status': 'success', 'result': [tab for tab in tabs['result']],
            'message': 'OK'}, 200
    return {'status': 'error', 'message': tabs['message'], 'result': False}, 400



@app.route('/openTab', methods=['POST'])
@require_valid_token
def open_tab():
    _url = request.json['url']
    event = Event()
    request_id = str(uuid.uuid4())
    events_by_id[request_id] = event

    socketio.emit('open_new_tab', {'url': _url, 'request_id': request_id})

    logger.debug ("open_tab: emitted open_new_tab event")
    try:
        with Timeout(TIMEOUT):
            event.wait()
    except Timeout:
        del events_by_id[request_id]
        if request_id in results_by_id:
            del results_by_id[request_id]
        return {'status': 'error', 'message': 'Timeout waiting for openTab',
                'result': 'timeout'}, 408
    
    result = results_by_id.get(request_id)
    del events_by_id[request_id]
    del results_by_id[request_id]
    logger.debug(f"open_tab: {result=}")
    code = 200
    if not result["result"]:
        code = 400
    return {'status': 'success' if result['result'] else 'error', 
            'result': result['result'],
            'message': result['message'] if not result['result'] else 'OK'}, code


@app.route('/injectScript', methods=['POST'])
@require_valid_token
def inject_script():
    """
    Runs the script in the browser tab.
    A result object can be assigned to `window.result` in the script to return it.
    """
    tab_id = request.json['tab_id']
    code = request.json['code']
    timeout = request.json.get('timeout', TIMEOUT)
    event = Event()
    request_id = str(uuid.uuid4())
    events_by_id[request_id] = event

    socketio.emit('inject_script', {
                        'tab_id': tab_id,
                        'code': code,
                        'request_id': request_id})
    try:
        with Timeout(timeout):
            event.wait()
    except Timeout:
        del events_by_id[request_id]
        return {'status': 'error', 'message': 'Timeout waiting for openTab',
                'error': 'timeout'}, 408
    
    result = results_by_id.get(request_id)
    del events_by_id[request_id]
    del results_by_id[request_id]
    return {'status': 'success' if result else 'error', 'result': result}


@app.route('/waitForElement', methods=['POST'])
@require_valid_token
def wait_for_element():
    tab_id = request.json['tab_id']
    selector = request.json['selector']
    timeout = int(request.json.get('timeout', TIMEOUT))
    event = Event()
    request_id = str(uuid.uuid4())
    events_by_id[request_id] = event

    logger.debug ('waitForElement route in app, calling browser: ', tab_id, selector, timeout, request_id)
    socketio.emit('wait_for_element', {
        'tab_id': tab_id,
        'selector': selector,
        'timeout': timeout*1000,
        'request_id': request_id
    })

    try:
        with Timeout(timeout):
            event.wait()
    except Timeout:
        del events_by_id[request_id]
        return {'status': 'error', 'message': 'Timeout waiting for waitForElement',
                'result': 'timeout'}, 408

    result = results_by_id.get(request_id)
    del events_by_id[request_id]
    del results_by_id[request_id]
    code = 200
    if result['result'] == 'error':
        code = 400
    return {'status': result['result'], 
            'result': result['result'] == 'success',
            'message': 'OK' if result['result'] == 'success' else result['message']}, code


@app.route('/executeScript', methods=['POST'])
@require_valid_token
def execute_script():
    """
    
    """
    tab_id = request.json['tab_id']
    code = request.json['code']
    event = Event()
    request_id = str(uuid.uuid4())
    events_by_id[request_id] = event

    socketio.emit('execute_script', {
                        'tab_id': tab_id, 
                        'code': code, 
                        'request_id': request_id})
    try:
        with Timeout(TIMEOUT):
            event.wait()
    except Timeout:
        del events_by_id[request_id]
        return {'status': 'error', 'message': 'Timeout waiting for openTab',
                'error': 'timeout'}, 408
    
    result = results_by_id.get(request_id)
    del events_by_id[request_id]
    del results_by_id[request_id]
    return {'status': 'success' if result else 'error', 'result': result}


@app.route('/getTabHTML/<tab_id>', methods=['GET'])
@require_valid_token
def get_tab_html(tab_id):
    event = Event()
    request_id = str(uuid.uuid4())
    events_by_id[request_id] = event

    socketio.emit('get_tab_html', {'tab_id': tab_id, 'request_id': request_id})

    try:
        with Timeout(TIMEOUT):
            event.wait()
    except Timeout:
        del events_by_id[request_id]
        return {'status': 'error', 'message': 'Timeout waiting for getTabHTML',
                'error': 'timeout'}, 408

    result = results_by_id.get(request_id)
    del events_by_id[request_id]
    del results_by_id[request_id]
    return {'status': 'success' if result else 'error', 'result': result}

@app.route('/health', methods=['GET'])
@require_valid_token
def health():
    if sock_status.connected:
        return {'status': 'success', 'message': "The service is up and running."}
    return {'status': 'error', 'message': "The service is not connected to the browser."}

@socketio.on('connect')
@requires_login
def handle_connect():
    logger.debug('Client connected: %s', request.sid)
    sock_status.connected = True


@socketio.on('disconnect')
@requires_login
def handle_disconnect():
    logger.debug(f'Client disconnected: {request.sid}')
    sock_status.connected = False

@socketio.on('message')
@requires_login
def handle_message(data):
    logger.debug(f'received message: {data}')

    request_id = data.get('request_id')
    if not request_id:
        return

    event = events_by_id.get(request_id)
    if event:
        del data['request_id']
        results_by_id[request_id] = data
        event.set()


@app.route("/response", methods=['POST'])
@requires_login
def handle_response():
    data = request.get_json()
    logger.debug (f'received message over POST: {data}')

    request_id = data.get('request_id')
    if not request_id:
        return
    event = events_by_id.get(request_id)
    if event:
        results_by_id[request_id] = data.get('result')
        event.set()
    return jsonify({'message': 'success'}), 200


# Run the Flask app with optional host and port
if __name__ == '__main__':
    import ssl
    import os

    script_dir = os.path.dirname(os.path.realpath(__file__))

    cert_path = os.path.join(script_dir, 'certs/cert.pem')
    key_path = os.path.join(script_dir, 'certs/key.pem')
    
    # Check if certificate file exists and is readable
    if not os.path.exists(cert_path):
        raise FileNotFoundError(f"Certificate file not found: {cert_path}")
    if not os.access(cert_path, os.R_OK):
        raise PermissionError(f"Cannot read certificate file: {cert_path}")

    # Check if key file exists and is readable
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Key file not found: {key_path}")
    if not os.access(key_path, os.R_OK):
        raise PermissionError(f"Cannot read key file: {key_path}")

    # Read in the cert file
    with open(cert_path, 'r') as f:
        cert = f.read()
        logger.debug("Loaded cert file: %s", cert_path)
    # Read in the key file
    with open(key_path, 'r') as f:
        key = f.read()
        logger.debug("Loaded key file: %s", key_path)

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_path,
                                key_path)
    
    logger.debug("Starting server on %s:%s", HOST, PORT)
    socketio.run(
                 app, 
                 host=HOST, 
                 port=PORT, 
                 #debug=True,
                 ssl_context=ssl_context,
                 )

