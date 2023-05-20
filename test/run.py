import sys
sys.path.append('..')

import unittest
from app import app
from gpt_tools import Browser


# Assuming this is the function you're testing
def add(a, b):
    return a + b

class TestAddFunction(unittest.TestCase):
 
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

        # Start the browser service and wait for it to be ready
        # The service is in a docker container

        # Load token from file '../token.txt'
        with open('../token.txt', 'r') as f:
            self.token = f.read().strip()

    def test_sync_browser(self):
        browser = Browser(self.token)


if __name__ == '__main__':
    unittest.main()
