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
        Attention à bien donner à l'utilisateur WebService le rôle moodle/user:delete
        :param userids: La liste des ids des utilisateurs à supprimer
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


    def delete_courses(self, courseids: list[int]):
        """
        Supprime des cours via le webservice moodle
        Attention à bien donner à l'utilisateur WebService les rôles
        moodle/course:delete ET moodle/course:view
        :param courseid: La liste des id des cours à supprimer
        :returns: Un dictionnaire avec la liste des warnings
        :raises Exception:
        """

        params = {}

        for i in range(len(courseids)):
            params["courseids[%i]" % i] = courseids[i]

        res = requests.get(url=self.url,
                           params={
                               'wstoken': self.config.token,
                               'moodlewsrestformat': "json",
                               'wsfunction': "core_course_delete_courses",
                               **params
                           })

        json_data = json.loads(res.text)

        if json_data is not None and 'exception' in json_data:
            raise Exception(json_data['message'])
        else:
            return(json_data)
