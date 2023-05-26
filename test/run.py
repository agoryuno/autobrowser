import os
import sys
sys.path.append('..')
import subprocess
import unittest
import time
from time import sleep

from gpt_tools import Browser


class PortOccupied(Exception):
    ...

class EmptyToken(Exception):
    ...

BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.ini')
TOKEN_PATH = os.path.join(BASE_DIR, "token.txt")

# Get the docker image name from ../config.ini
import configparser
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

IMAGE_NAME = config['MAIN']['DOCKER_NAME']
START_TIMEOUT = 60
CONTAINER_NAME = 'autobrowser-testing'


def read_token(token_path=TOKEN_PATH, attempts=10):
    for i in range(attempts):
        with open(token_path, 'r') as f:
            token = f.read().strip()
        if token != "":
            return token
        sleep(1)
    raise EmptyToken(f"Token file is empty after {attempts} attempts")
    

def kill_container(container_name=CONTAINER_NAME):
    proc = subprocess.Popen(['sudo', 'docker', 'kill', container_name],
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
    proc.wait()

def run_shell_script(script_path):
    try:
        # The 'sudo' command will prompt for a password unless you've configured sudo to run without it for your user
        subprocess.Popen(['sudo', '/bin/bash', script_path])
    except Exception as e:
        print(f"An error occurred while trying to run the script: {e}")


def restart_container(image_name=IMAGE_NAME, 
                      container_name=CONTAINER_NAME,
                      config_path=CONFIG_PATH,
                      base_dir=BASE_DIR):
    command = ['sudo', 'docker', 'run', 
               '-d',
               '--name', container_name, 
               '-v', f'{config_path}:/app/config.ini:ro',
               '-v', f'{base_dir}/token.txt:/app/token.txt',
               '-v', f'{base_dir}/flask-log.txt:/app/flask-log.txt',
               '-p', '443:443',
               '-p', '5900:5900',
               image_name]
    try:
        kill_container(container_name)
        while is_container_running(container_name):
            sleep(1)
        proc = subprocess.Popen(['sudo', 'docker', 'rm', container_name],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc.wait()

        result = subprocess.run(command, 
                                check=True, 
                                text=True,
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)

        print (f"Started the container: {result.stdout=}, {result.stderr=}")
        start_ts = time.time()
        while not is_container_running(container_name):
            sleep(1)
            if time.time() - start_ts > START_TIMEOUT:
                raise TimeoutError("Timed out while waiting for the container to start")
    except subprocess.CalledProcessError as e:
        print(f"Docker command failed: {e.stderr}")
        proc = subprocess.Popen(['sudo', 'docker', 'kill', container_name],
                                stderr=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,)
        proc.wait()
        proc = subprocess.Popen(['sudo', 'docker', 'rm', container_name],
                                stderr=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,)
        proc.wait()
        if  "port is already allocated" in e.stderr:
            raise PortOccupied(e.stderr)
        
    except Exception as e:
        print(f"An error occurred while trying to restart the container: {e}")


def is_container_running(container_name):
    try:
        output = subprocess.check_output(['sudo', 'docker', 'ps', '-f', f'name={container_name}'])
        if container_name in output.decode():
            return True
        else:
            return False
    except Exception as e:
        print(f"An error occurred while checking the container status: {e}")
        return False



class TestAddFunction(unittest.TestCase):
 
    def setUp(self):

        try:
            restart_container()
        except PortOccupied:
            print ("One of the service's ports is occupied. "
                   "This likely means that a different container is already running. "
                   "Stop all running containers before running the tests.")
            kill_container()
            sys.exit(1)

        try:
            self.token = read_token()
        except:
            kill_container()
            raise
        
        print (f"Using token: {self.token}")

        try:
            browser = Browser(self.token, trusted_ca=False)
            res = browser.tabs_list()
            print (f"browser.tabs_list(): {res}")

            print ("Service is ready")
        except Exception as e:
            print(f"An error occurred while trying to connect to the service: {e}")
            kill_container()
            sys.exit(1)

    def tearDown(self):
        # Stop the browser service
        try:
            proc = subprocess.Popen(['sudo', 'docker', 'kill', CONTAINER_NAME],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.wait()
            while is_container_running('autobrowser-container'):
                sleep(1)
            print ("Stopped the browser service")
        except Exception as e:
            print(f"An error occurred while trying to stop the service: {e}")
        
    def test_sync_browser(self):
        browser = Browser(self.token, trusted_ca=False)
        tabs = browser.tabs_list()
        print (tabs)


if __name__ == '__main__':
    unittest.main()
