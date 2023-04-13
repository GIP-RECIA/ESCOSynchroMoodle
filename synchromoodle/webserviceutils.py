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
        L'utilisateur WebService doit avoir la permission moodle/user:delete
        :param userids: La liste des ids des utilisateurs à supprimer
        :return: None si la fonction s'est éxécutée correctement
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
        L'utilisateur WebService doit avoir les permissions
        moodle/course:delete et moodle/course:view
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


    def get_courses_user_enrolled(self, userid: int, returnusercount=0):
        """
        Récupère la liste de tous les cours auxquels est inscrit un utilisateur
        L'utilisateur WebService doit avoir les permissions
        moodle/course:viewparticipants et moodle/user:viewdetails

        :param userid: L'id de l'utilisateur
        :param returnusercount: - 0 si on ne retourne pas le nombre d'utilisateurs inscrits à un cours
                                - 1 si on retourne le nombre d'utilisateurs inscrits à un cours
                                (influe sur le temps de réponse)
        :returns: Un dictionnaire contenant les cours de l'utilisateur
        :raises Exception:
        """

        params = {}
        params["userid"] = userid
        params["returnusercount"] = returnusercount

        res = requests.get(url=self.url,
                           params={
                               'wstoken': self.config.token,
                               'moodlewsrestformat': "json",
                               'wsfunction': "core_enrol_get_users_courses",
                               **params
                           })

        json_data = json.loads(res.text)

        if json_data is not None and 'exception' in json_data:
            raise Exception(json_data['message'])
        else:
            return(json_data)


    def unenrol_user_from_course(self, userid: int, courseid: int):
        """
        Désinscris un utilisateur à un cours
        L'utilisateur WebService doit avoir la permission enrol/manual:unenrol
        :param userid: L'id de l'utilisateur à désinscrire
        :param courseid: L'id du cours duquel on déinscrit l'utilisateur
        :returns: None si la fonction s'est éxécutée correctement
        :raises Exception:
        """

        params = {}
        params["enrolments[0][userid]"] = userid
        params["enrolments[0][courseid]"] = courseid

        res = requests.get(url=self.url,
                           params={
                               'wstoken': self.config.token,
                               'moodlewsrestformat': "json",
                               'wsfunction': "enrol_manual_unenrol_users",
                               **params
                           })

        json_data = json.loads(res.text)

        if json_data is not None and 'exception' in json_data:
            raise Exception(json_data['message'])
        else:
            return(json_data)
