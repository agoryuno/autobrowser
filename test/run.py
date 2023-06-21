import os
import sys
sys.path.append('..')
import subprocess
import unittest
import time
import logging
from time import sleep
from html.parser import HTMLParser


from gpt_tools import Browser
from gpt_tools.exceptions import BrowserError


# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='[%(asctime)s] %(levelname)s: %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)

class PortOccupied(Exception):
    ...

class EmptyToken(Exception):
    ...

class MyHTMLParser(HTMLParser):
    def error(self, message):
        raise ValueError(message)

def is_valid_html(html):
    parser = MyHTMLParser()
    try:
        parser.feed(html)
    except ValueError:
        return False
    return True

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
        logger.error(f"An error occurred while trying to run the script: {e}")


def restart_container(image_name=IMAGE_NAME, 
                      container_name=CONTAINER_NAME,
                      config_path=CONFIG_PATH,
                      base_dir=BASE_DIR):
    logger.info(f"Restarting container {container_name}...")
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
        logger.info("Stopping the container...")
        kill_container(container_name)

        while is_container_running(container_name):
            sleep(1)

        logger.info("Removing the container...")
        proc = subprocess.Popen(['sudo', 'docker', 'rm', container_name],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc.wait()

        logger.info("Removing the token file...")
        p =subprocess.Popen(['rm', '-f', f'{base_dir}/token.txt'])
        p.wait()

        logger.info("Recreating the token file...")
        p = subprocess.Popen(['touch', f'{base_dir}/token.txt'], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        )
        p.wait()


        logger.info("Starting the container...")
        result = subprocess.run(command, 
                                check=True, 
                                text=True,
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)

        logger.info (f"\033[32mStarted the container: {result.stdout=}, {result.stderr=}\033[0m")
        start_ts = time.time()
        while not is_container_running(container_name):
            sleep(1)
            if time.time() - start_ts > START_TIMEOUT:
                raise TimeoutError("Timed out while waiting for the container to start")
        logger.info("Container is running.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Docker command failed: {e.stderr}")
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
        logger.error(f"An error occurred while trying to restart the container: {e}")


def is_container_running(container_name):
    try:
        output = subprocess.check_output(['sudo', 'docker', 'ps', '-f', f'name={container_name}'])
        if container_name in output.decode():
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"An error occurred while checking the container status: {e}")
        return False


class TestAddFunction(unittest.TestCase):
 
    @classmethod
    def setUpClass(cls):

        logger.debug ("Test:: Setting up the tests")
        try:
            restart_container()
        except PortOccupied:
            logger.error ("One of the service's ports is occupied. "
                   "This likely means that a different container is already running. "
                   "Stop all running containers before running the tests.")
            kill_container()
            sys.exit(1)

        try:
            cls.token = read_token()
        except:
            kill_container()
            raise
        
        logger.debug (f"Test:: Using token: {cls.token}")

        try:
            logger.debug("Test:: Starting the service...")
            browser = Browser(cls.token, trusted_ca=False)
            res = browser.is_ready()
            #res = browser.tabs_list()
            while not res:
                sleep(1)
                logger.debug("\033[35mTest:: Retrying browser.is_ready()...\033[0m")
                res = browser.is_ready()
            logger.debug ("\033[32mTest:: Service is ready\033[0m")
        except Exception as e:
            logger.error(f"Test:: An error occurred while trying to connect to the service: {e}")
            kill_container()
            sys.exit(1)

    @classmethod
    def tearDownClass(cls):
        # Stop the browser service
        try:
            proc = subprocess.Popen(['sudo', 'docker', 'kill', CONTAINER_NAME],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.wait()
            while is_container_running('autobrowser-container'):
                sleep(1)
            logger.debug ("Stopped the browser service")
        except Exception as e:
            logger.error(f"An error occurred while trying to stop the service: {e}")
        
    def atest_tabsList(self):
        browser = Browser(TestAddFunction.token, trusted_ca=False)
        tabs = browser.tabs_list()
        self.assertIsInstance(tabs, list)
        self.assertGreater(len(tabs), 0)
        self.assertIsInstance(tabs[0], dict)
        self.assertIn('id', tabs[0])
        self.assertIn('title', tabs[0])
        self.assertIn('url', tabs[0])

    def atest_openUrl(self):
        browser = Browser(TestAddFunction.token, trusted_ca=False)
        tab_id = browser.open_tab("https://www.google.com")
        self.assertIsInstance(tab_id, int)
        result = browser.close_tab_by_id(tab_id)
        self.assertTrue(result)
        tab_id = browser.open_tab("")
        self.assertIsInstance(tab_id, int)

    def atest_close_tab_by_id(self):
        browser = Browser(TestAddFunction.token, trusted_ca=False)
        self.assertRaises(BrowserError, 
                          browser.close_tab_by_id, 18446744073709551615
                          )
        try:
            browser.close_tab_by_id(18446744073709551615)
        except BrowserError as e:
            s = "Type error for parameter tabIds"
            self.assertEqual(str(e)[:len(s)], s)
        
        self.assertRaises(BrowserError,
                          browser.close_tab_by_id, 10)
        try:
            browser.close_tab_by_id(10)
        except BrowserError as e:
            s = "Invalid tab ID: 10"
            self.assertEqual(str(e)[:len(s)], s)

    def atest_wait_for_element(self):
        browser = Browser(TestAddFunction.token, trusted_ca=False)
        tab_id = browser.open_tab("https://www.google.com")
        self.assertIsInstance(tab_id, int)
        tab_id = browser.wait_for_element(tab_id, "html body form textarea")
        self.assertIsInstance(tab_id, int)

    def atest_get_tab_html(self):
        browser = Browser(TestAddFunction.token, trusted_ca=False)
        tab_id = browser.open_tab("https://www.google.com")
        browser.wait_for_element(tab_id, "html body form textarea")
        html = browser.get_tab_html(tab_id)
        self.assertIsInstance(html, str)
        self.assertTrue(is_valid_html(html))

    def atest_inject_script(self):
        browser = Browser(TestAddFunction.token, trusted_ca=False)
        tab_id = browser.open_tab("https://www.google.com")
        res = browser.wait_for_element(tab_id, "html body form textarea")
        res = browser.inject_script(tab_id, 
        """
        window.result = 4 + 5;
        """)
        self.assertEqual(int(res), 9)

        res = browser.inject_script(tab_id,
                              """const a = 1;
                              a = 2;
                              """)
        self.assertEqual(res, "TypeError: invalid assignment to const 'a'")

    def test_search(self):
        browser = Browser(TestAddFunction.token, trusted_ca=False)
        tab_id = browser.open_tab("https://www.google.com")
        res = browser.wait_for_element(tab_id, "html body form textarea")
        res = browser.search(tab_id, "google")
        print (res)


if __name__ == '__main__':
    unittest.main()
