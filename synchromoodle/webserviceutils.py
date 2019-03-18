# coding: utf-8
"""
Webservice
"""
from typing import List
import json
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
        users_to_delete = {}
        for userid in userids:
            users_to_delete["userids[%d]" % i] = userid
            i += 1
        res = requests.get(url=self.url,
                           params={
                               'wstoken': self.config.token,
                               'moodlewsrestformat': "json",
                               'wsfunction': "core_user_delete_users",
                               **users_to_delete
                           })
        json_data = json.loads(res.text)

        if json_data is not None and 'exception' in json_data:
            raise Exception(json_data['message'])
        return json_data
