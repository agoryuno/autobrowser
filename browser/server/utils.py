import os
from urllib.parse import unquote
import logging
from dataclasses import dataclass, field, asdict

from functools import wraps
from flask import Response, request


valid_token = None

@dataclass
class TimeoutResponse:
    route_name: str = field(init=True)
    message: str = field(init=False)
    result: str = 'timeout'
    status: str = 'error'
    
    def __post_init__(self):
        self.message = f'Timeout waiting for {self.route_name}'

def timeout_response(route_name):
    return TimeoutResponse(route_name=route_name).asdict()


def setup_logger(log_file, logger_name=__name__, level=logging.DEBUG):
    """
    Set up logging configuration.

    Parameters:
    - log_file: Path to the log file.
    - logger_name: Name of the logger. Default is __name__.
    - level: Log level. Default is logging.DEBUG.
    """

    # Create a logger object
    logger = logging.getLogger(logger_name)

    # Set the log level you want -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    logger.setLevel(level)

    # Create a file handler object
    file_handler = logging.FileHandler(log_file)

    # Create a formatter object
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Set the formatter for the file handler object
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger


def read_token_from_file(filepath):
    # Read the token from the file
    with open(filepath, 'r') as f:
        return f.read().strip()


def read_token_from_file2(config):
    # Get the base directory
    base_directory = get_base_directory(config)

    print (f"utils.py: {base_directory=}")

    # Get the relative path to the token file
    token_file = config.get('FLASK', 'TOKEN_FILE')

    print (f"utils.py: {token_file=}")

    # Combine the base directory and the relative path to get the full path to the token file
    filename = os.path.join(base_directory, token_file)

    print (f"App: reading token from file: {filename}")

    # Read the token from the file
    with open(filename, 'r') as f:
        return f.read().strip()


def require_valid_token_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.args.get('token')
        token = unquote(token)
        print ("App received token: ", token)
        print ("App is looking for token: ", valid_token)
        print ("App is comparing: ", token == valid_token)
        if not token or token != valid_token:
            return Response("Unauthorized Access", status=401)
        return f(*args, **kwargs)
    return decorated_function

def require_valid_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header is not None:
            try:
                scheme, token = auth_header.split(" ") 
                if scheme.lower() != "bearer":
                    return Response("Unauthorized Access - Invalid token scheme", status=401)
            except ValueError:
                return Response("Unauthorized Access - Invalid token format", status=401)
        else:
            return Response("Unauthorized Access - No Authorization Header", status=401)

        token = unquote(token)
        print("App received token: ", token)
        print("App is looking for token: ", valid_token)
        print("App is comparing: ", token == valid_token)
        if not token or token != valid_token:
            return Response("Unauthorized Access", status=401)
        return f(*args, **kwargs)
    return decorated_function

def get_base_directory(config):
    # Get the application mode
    mode = config.get('MAIN', 'MODE')

    # Get the path corresponding to the current mode
    if mode == 'DEV':
        root_path = config.get('DEV', 'PATH')
    elif mode == 'DEPLOY':
        root_path = config.get('DEPLOY', 'PATH')
    else:
        raise ValueError("Invalid mode in config.ini")

    # Interpolate the $HOME variable in the root_path
    root_path = root_path.replace('$HOME', os.getenv('HOME'))

    return root_path


def test():
    print (f"{valid_token=}")