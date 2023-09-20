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

        try:
            res = requests.get(url=self.url,
                               params={
                                   'wstoken': self.config.token,
                                   'moodlewsrestformat': "json",
                                   'wsfunction': "core_user_delete_users",
                                   **users_to_delete
                               },
                               timeout=120)
        except requests.exceptions.ConnectionError:
            log.error("Déconnexion du webservice delete_users sur suppression utilisateurs %s", str(userids))
            return None
        except requests.exceptions.Timeout:
            log.warning("Délai de requête au webservice delete_users maximum dépassé sur suppression utilisateurs %s", str(userids))
            return None

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

        try:
            res = requests.get(url=self.url,
                               params={
                                   'wstoken': self.config.token,
                                   'moodlewsrestformat': "json",
                                   'wsfunction': "core_course_delete_courses",
                                   **params
                               },
                               timeout=600)
        except requests.exceptions.ConnectionError:
            log.error("Déconnexion du webservice delete_courses sur suppression cours %s", str(courseid))
            return None
        except requests.exceptions.Timeout:
            log.warning("Délai de requête au webservice delete_courses maximum dépassé sur suppression cours %s", str(courseid))
            return None

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

        try:
            res = requests.get(url=self.url,
                               params={
                                   'wstoken': self.config.token,
                                   'moodlewsrestformat': "json",
                                   'wsfunction': "core_enrol_get_users_courses",
                                   **params
                               },
                               timeout=60)
        except requests.exceptions.ConnectionError:
            log.error("Déconnexion du webservice get_users_courses sur %s", str(userid))
            return None
        except requests.exceptions.Timeout:
            log.warning("Délai de requête au webservice get_users_courses maximum dépassé sur %s", str(userid))
            return None

        try:
            json_data = json.loads(res.text)
            if json_data is not None and 'exception' in json_data:
                log.warning(json_data['message'])
                return None
            return json_data
        except json.decoder.JSONDecodeError:
            log.warning("Problème avec appel au WebService get_courses_user_enrolled. "
                        "Message retourné : %s.", res.text)
            return None


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

        try:
            res = requests.get(url=self.url,
                               params={
                                   'wstoken': self.config.token,
                                   'moodlewsrestformat': "json",
                                   'wsfunction': "core_cohort_delete_cohorts",
                                   **cohorts_to_delete
                               },
                               timeout=600)
        except requests.exceptions.ConnectionError:
            log.error("Déconnexion du webservice delete_cohorts sur suppression cohortes %s", str(cohortids))
            return None
        except requests.exceptions.Timeout:
            log.warning("Délai de requête au webservice delete_cohorts maximum dépassé sur suppression cohortes %s", str(cohortids))
            return None

        try:
            json_data = json.loads(res.text)
            if json_data is not None and 'exception' in json_data:
                log.warning("Exception suppression cohortes %s : "+json_data['message'],
                            str(cohortids))
        except json.decoder.JSONDecodeError:
            log.warning("Problème avec appel au WebService delete_cohorts. "
                        "Message retourné : %s. Cohortes traitées : %s",
                        res.text, str(cohortids))


    def get_users_enrolled_in_course(self, courseid: int, log=getLogger()):
        """
        Récupère la liste des utilisateurs inscrits dans un cours donné.
        L'utilisateur WebService doit avoir les permissions .

        :param courseid: L'id du cours dont on veut récupérer la liste des utilisateurs
        :param log: Le logger
        :returns: La liste des utilisateurs inscrits au cours
        """

        params = {"courseid": courseid}

        try:
            res = requests.get(url=self.url,
                               params={
                                   'wstoken': self.config.token,
                                   'moodlewsrestformat': "json",
                                   'wsfunction': "core_enrol_get_enrolled_users",
                                   **params
                               },
                               timeout=600)
        except requests.exceptions.ConnectionError:
            log.error("Déconnexion du webservice core_enrol_get_enrolled_users sur cours %s", str(courseid))
            return None
        except requests.exceptions.Timeout:
            log.warning("Délai de requête au webservice core_enrol_get_enrolled_users maximum dépassé sur cours %s",
                        str(courseid))
            return None

        try:
            json_data = json.loads(res.text)
            if json_data is not None and 'exception' in json_data:
                log.warning("Exception core_enrol_get_enrolled_users %s : " + json_data['message'],
                            str(courseid))
                return None
            return json_data
        except json.decoder.JSONDecodeError:
            log.warning("Problème avec appel au WebService core_enrol_get_enrolled_users. "
                        "Message retourné : %s. Cours traité : %s",
                        res.text, str(courseid))
            return None


    def get_last_course_access(self, courseid: int, log=getLogger()):
        """
        Récupère le timestamp correspondant au dernier accès d'un cours donné.
        L'utilisateur WebService doit avoir les permissions moodle/cohort:manage.

        :param courseid: L'id du cours dont on veut récupérer le dernier accès
        :param log: Le logger
        :returns: Le timestamp du dernier accès au cours, 0 si le cours n'a jamais été accédé,
        """

        #Récupère la liste des utilisateurs inscrits
        course_users = self.get_users_enrolled_in_course(courseid)
        max_access = 0

        #Récupère le timestamp max parmi les utilisateurs = le dernier accès
        if course_users is not None:
            for user in course_users:
                lastcourseaccess = user["lastcourseaccess"]
                if max_access == 0:
                    max_access = lastcourseaccess
                else:
                    if lastcourseaccess > max_access:
                        max_access = lastcourseaccess

        return max_access
