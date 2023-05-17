"""
This implements authentication for the browser
The procedure is as follows:
1. The `start-firefox` script starts the browser pointing to the /auth
   URL with the token read from the same file the server reads it from
2. Upon receiving the GET request, the browser server checks the token
   and automatically logs in the browser if the token is valid.
3. The browser is redirected to the root path, which serves an empty
   HTML page which the browser can use to inject the content script into.
This module implements only the session and authentication logic. The
root route is implemented in the browser/server/app.py module.
The secret key is also set in the main app.py module.
The logout function allows the server to terminate the session without
requiring any requests from the browser. This is needed to forcefully
reset sessions on a timer or some other way to be decided later.
"""

from functools import wraps
import logging

from flask import Blueprint
from flask import request, redirect, url_for, session

from utils import require_valid_token

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


valid_token = None

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/auth')
@require_valid_token
def auth():
    session['logged_in'] = True
    logging.info('User logged in successfully.')
    return redirect(url_for('root'))


def logout():
    session.clear()
    logging.info('User logged out successfully.')
    return redirect(url_for('root'))

def requires_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            logging.error('Unauthorized access attempt. User not logged in.')
            return redirect(url_for('auth.auth'))
        return f(*args, **kwargs)
    return decorated_function
