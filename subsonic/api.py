import hashlib
import random

import tortilla


class Sonic(object):
    API_VERSION = '1.16.0'

    def __init__(self, username, password, server_location, app_name='cloudplayer'):
        self.username = username
        self.password = password
        self.app_name = app_name
        self.api = tortilla.wrap('{0}/rest'.format(server_location))

        self.validate()

    def _auth(self):
        salt = str(random.getrandbits(64))
        hashed_password = hashlib.md5(self.password.encode() + salt.encode()).hexdigest()
        return {'u': self.username, 't': hashed_password, 's': salt}

    def __metadata(self):
        return {'v': Sonic.API_VERSION, 'c': self.app_name, 'f': 'json'}

    def _request_get(self, route, params=None):
        params = {**self._auth(), **self.__metadata(), **(params if params else {})}
        return route.get(params=params)['subsonic-response']

    def validate(self):
        ping = self._request_get(self.api.ping)
        if ping['status'] == 'failed':
            raise ValueError(ping['error']['message'])


if __name__ == '__main__':
    import os

    api = Sonic(os.environ['USERNAME'], os.environ['PASSWORD'], os.environ['LOCATION'])
