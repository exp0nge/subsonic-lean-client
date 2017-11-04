import unittest
from unittest import mock

from api import SubsonicClient


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.username = self.password = 'test_case'
        self.server_address = 'http://127.0.0.1/rest'
        with mock.patch.object(SubsonicClient, '_request_get', return_value={}):
            self.api = SubsonicClient(self.username, self.password, self.server_address)

    def tearDown(self):
        pass