import os
from functools import wraps
from flask import Response, request

valid_token = None

def read_token_from_file(config):
    # Get the base directory
    base_directory = get_base_directory(config)

    # Get the relative path to the token file
    token_file = config.get('FLASK', 'TOKEN_FILE')

    # Combine the base directory and the relative path to get the full path to the token file
    filename = os.path.join(base_directory, token_file)

    print (f"App: reading token from file: {filename}")

    # Read the token from the file
    with open(filename, 'r') as f:
        return f.read().strip()


def require_valid_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.args.get('token')
        print ("App received token: ", token)
        print ("App is looking for token: ", valid_token)
        print ("App is comparing: ", token == valid_token)
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