import requests
from synchromoodle.config import WebServiceConfig, ConstantesConfig
from typing import List


class WebService:
    """
    Couche d'accès au webservice Moodle.
    """

    def __init__(self, config: WebServiceConfig):
        self.config = config
        self.url = "%s/webservice/rest/server.php" % config.moodle_host

    def delete_users(self, userids: List[int]):
        i = 0
        params = {
            'wstoken': self.config.token,
            'moodlewsrestformat': "json",
            'wsfunction': "core_user_delete_users"
        }
        for userid in userids:
            params["userids[%d]" % i] = userid
            i += 1
        return requests.get(
            url=self.url,
            params=params
        )
