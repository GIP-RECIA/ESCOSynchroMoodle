# coding: utf-8
"""
Webservice
"""

from typing import List
import requests
from synchromoodle.config import WebServiceConfig


class WebService:
    """
    Couche d'accès au webservice Moodle.
    """

    def __init__(self, config: WebServiceConfig):
        self.config = config
        self.url = "%s/webservice/rest/server.php" % config.moodle_host

    def delete_users(self, userids: List[int]):
        """
        Supprime des utilisateurs via le webservice moodle
        :param userids:
        :return:
        """
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
