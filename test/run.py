import sys
sys.path.append('..')
import subprocess
import unittest
import time
from time import sleep

from gpt_tools import Browser

# Get the docker image name from ../config.ini
import configparser
config = configparser.ConfigParser()
config.read('../config.ini')

IMAGE_NAME = config['MAIN']['DOCKER_NAME']
START_TIMEOUT = 60


def run_shell_script(script_path):
    try:
        # The 'sudo' command will prompt for a password unless you've configured sudo to run without it for your user
        subprocess.Popen(['sudo', '/bin/bash', script_path])
    except Exception as e:
        print(f"An error occurred while trying to run the script: {e}")


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
        #app.testing = True
        #self.app = app.test_client()

        # Start the browser service and wait for it to be ready
        # The service is in a docker container
        run_shell_script('../run-service')

        while not is_container_running('autobrowser-container'):
            sleep(1)

        # Load token from file '../token.txt'
        with open('../token.txt', 'r') as f:
            self.token = f.read().strip()

        browser = Browser(self.token, trusted_ca=False)
        start_ts = time.time()
        while not browser.tabs_list():
            if time.time() - start_ts > START_TIMEOUT:
                raise TimeoutError("Timed out waiting for the browser service to start")
            sleep(1)

        print ("Service is ready")
        print ("Token: ", self.token)

    def tearDown(self):
        # Stop the browser service
        try:
            subprocess.Popen(['sudo', 'docker', 'kill', 'autobrowser-container'])
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
