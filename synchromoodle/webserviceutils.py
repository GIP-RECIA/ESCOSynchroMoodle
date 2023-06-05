# coding: utf-8
"""
Module comprenant les différentes fonctions permattant de
faire des appels aux webservices de moodle
"""
from typing import List
from logging import getLogger
import json
import requests
from synchromoodle.config import WebServiceConfig

class WebService:
    """
    Couche d'accès au webservice Moodle.
    """

    def __init__(self, config: WebServiceConfig):
        self.config = config
        self.url = f"{config.moodle_host}/webservice/rest/server.php"


    def delete_users(self, userids: List[int], log=getLogger()):
        """
        Supprime des utilisateurs via le webservice moodle.
        L'utilisateur WebService doit avoir la permission moodle/user:delete.

        :param userids: La liste des ids des utilisateurs à supprimer
        :param log: Le logger
        """
        i = 0
        users_to_delete = {}
        for userid in userids:
            users_to_delete[f"userids[{i}]"] = userid
            i += 1
        res = requests.get(url=self.url,
                           params={
                               'wstoken': self.config.token,
                               'moodlewsrestformat': "json",
                               'wsfunction': "core_user_delete_users",
                               **users_to_delete
                           },
                           timeout=120)

        try:
            json_data = json.loads(res.text)
            if json_data is not None and 'exception' in json_data:
                log.warning("Exception suppression utilisateurs %s : "+json_data['message'],
                            str(userids))
        except json.decoder.JSONDecodeError:
            log.warning("Problème avec appel au WebService delete_users. "
                        "Message retourné : %s. Utilisateurs traités : %s",
                        res.text, str(userids))


    def delete_course(self, courseid: list[int], log=getLogger()):
        """
        Supprime un cours via le webservice moodle.
        L'utilisateur WebService doit avoir les permissions
        moodle/course:delete, moodle/course:view
        et moodle/course:viewhiddencourses.

        :param courseid: L'id du cours à supprimer
        :param log: Le logger
        """

        params = {}
        params["courseids[0]"] = courseid

        res = requests.get(url=self.url,
                           params={
                               'wstoken': self.config.token,
                               'moodlewsrestformat': "json",
                               'wsfunction': "core_course_delete_courses",
                               **params
                           },
                           timeout=600)

        try:
            json_data = json.loads(res.text)
            if json_data is not None and 'exception' in json_data:
                log.warning("Exception cours %s : "+json_data['message'], str(courseid))
        except json.decoder.JSONDecodeError:
            log.warning("Problème avec appel au WebService delete_courses. "
                        "Message retourné : %s. Cours traité : %s",
                        res.text, str(courseid))


    def get_courses_user_enrolled(self, userid: int, returnusercount=0, log=getLogger()) -> dict:
        """
        Récupère la liste de tous les cours auxquels est inscrit un utilisateur.
        L'utilisateur WebService doit avoir les permissions
        moodle/course:viewparticipants et moodle/user:viewdetails.

        :param log: Le logger
        :param userid: L'id de l'utilisateur
        :param returnusercount: - 0 si on ne retourne pas le nombre d'utilisateurs inscrits à un cours
                                - 1 si on retourne le nombre d'utilisateurs inscrits à un cours
        :returns: Un dictionnaire contenant les cours de l'utilisateur
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
                           },
                           timeout=60)
        try:
            json_data = json.loads(res.text)
            if json_data is not None and 'exception' in json_data:
                log.warning(json_data['message'])
                return {}
            return json_data
        except json.decoder.JSONDecodeError:
            log.warning("Problème avec appel au WebService get_courses_user_enrolled. "
                        "Message retourné : %s.", res.text)
            return {}


    def delete_cohorts(self, cohortids: list[int], log=getLogger()):
        """
        Supprime une cohorte de moodle.
        L'utilisateur WebService doit avoir la permission moodle/cohort:manage.

        :param cohortids: La liste des identifiants des cohortes
        :param log: Le logger
        """

        cohorts_to_delete = {}
        for i,cohort_id in enumerate(cohortids):
            cohorts_to_delete[f"cohortids[{i}]"] = cohort_id

        res = requests.get(url=self.url,
                           params={
                               'wstoken': self.config.token,
                               'moodlewsrestformat': "json",
                               'wsfunction': "core_cohort_delete_cohorts",
                               **cohorts_to_delete
                           },
                           timeout=600)

        try:
            json_data = json.loads(res.text)
            if json_data is not None and 'exception' in json_data:
                log.warning("Exception suppression cohortes %s : "+json_data['message'],
                            str(cohortids))
        except json.decoder.JSONDecodeError:
            log.warning("Problème avec appel au WebService delete_cohorts. "
                        "Message retourné : %s. Cohortes traitées : %s",
                        res.text, str(cohortids))
