# coding: utf-8
"""
Module comprenant les différentes fonctions permattant de
faire des appels aux webservices de moodle
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
        self.url = f"{config.moodle_host}/webservice/rest/server.php"


    def delete_users(self, userids: List[int]):
        """
        Supprime des utilisateurs via le webservice moodle.
        L'utilisateur WebService doit avoir la permission moodle/user:delete.

        :param userids: La liste des ids des utilisateurs à supprimer
        :return: None si la fonction s'est éxécutée correctement
        :raises Exception: Si le WebService renvoie une exception
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
                           timeout=10)
        json_data = json.loads(res.text)

        if json_data is not None and 'exception' in json_data:
            raise Exception(json_data['message'])
        return json_data


    def delete_courses(self, courseids: list[int]):
        """
        Supprime des cours via le webservice moodle.
        L'utilisateur WebService doit avoir les permissions
        moodle/course:delete et moodle/course:view.

        :param courseid: La liste des id des cours à supprimer
        :returns: Un dictionnaire avec la liste des warnings
        :raises Exception: Si le WebService renvoie une exception
        """

        params = {}

        for i,course_id in enumerate(courseids):
            params[f"courseids[{i}]"] = course_id

        res = requests.get(url=self.url,
                           params={
                               'wstoken': self.config.token,
                               'moodlewsrestformat': "json",
                               'wsfunction': "core_course_delete_courses",
                               **params
                           },
                           timeout=10)

        json_data = json.loads(res.text)

        if json_data is not None and 'exception' in json_data:
            raise Exception(json_data['message'])
        return json_data


    def get_courses_user_enrolled(self, userid: int, returnusercount=0):
        """
        Récupère la liste de tous les cours auxquels est inscrit un utilisateur.
        L'utilisateur WebService doit avoir les permissions
        moodle/course:viewparticipants et moodle/user:viewdetails.

        :param userid: L'id de l'utilisateur
        :param returnusercount: - 0 si on ne retourne pas le nombre d'utilisateurs inscrits à un cours
                                - 1 si on retourne le nombre d'utilisateurs inscrits à un cours

        :returns: Un dictionnaire contenant les cours de l'utilisateur
        :raises Exception: Si le WebService renvoie une exception
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
                           timeout=10)

        json_data = json.loads(res.text)

        if json_data is not None and 'exception' in json_data:
            raise Exception(json_data['message'])
        return json_data


    def unenrol_user_from_course(self, userid: int, courseid: int):
        """
        Désinscris un utilisateur à un cours.
        L'utilisateur WebService doit avoir la permission enrol/manual:unenrol.

        :param userid: L'id de l'utilisateur à désinscrire
        :param courseid: L'id du cours duquel on déinscrit l'utilisateur
        :returns: None si la fonction s'est éxécutée correctement
        :raises Exception: Si le WebService renvoie une exception
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
                           },
                           timeout=10)

        json_data = json.loads(res.text)

        if json_data is not None and 'exception' in json_data:
            raise Exception(json_data['message'])
        return json_data


    def enrol_user_to_course(self, roleid: int, userid: int, courseid: int):
        """
        Inscris un utilisateur à un cours.
        L'utilisateur WebService doit avoir la permission enrol/manual:enrol.

        :param roleid: Le rôle de l'utilisateur dans le cours
        :param userid: L'id de l'utilisateur à inscrire
        :param courseid: L'id du cours auquel on inscrit l'utilisateur
        :returns: None si la fonction s'est éxécutée correctement
        :raises Exception: Si le WebService renvoie une exception
        """

        enrolments = {}
        enrolments["enrolments[0][roleid]"] = roleid
        enrolments["enrolments[0][userid]"] = userid
        enrolments["enrolments[0][courseid]"] = courseid

        res = requests.get(url=self.url,
                           params={
                               'wstoken': self.config.token,
                               'moodlewsrestformat': "json",
                               'wsfunction': "enrol_manual_enrol_users",
                               **enrolments
                           },
                           timeout=10)

        json_data = json.loads(res.text)

        if json_data is not None and 'exception' in json_data:
            raise Exception(json_data['message'])
        return json_data


    def create_course(self, fullname: str, shortname: str, categoryid: int):
        """
        Ajoute un nouveau cours.
        L'utilisateur WebService doit avoir la permission moodle/course:create.

        :param fullname: Le nom complet du cours
        :param shortname: Le nom court du cours
        :param categoryid: L'id de la catégorie dans laquelle va être insérée le cours
        :returns: Un dictionnaire avec les informations du cours créé
        :raises Exception: Si le WebService renvoie une exception
        """

        params = {}
        params["courses[0][fullname]"] = fullname
        params["courses[0][shortname]"] = shortname
        params["courses[0][categoryid]"] = categoryid

        res = requests.get(url=self.url,
                           params={
                               'wstoken': self.config.token,
                               'moodlewsrestformat': "json",
                               'wsfunction': "core_course_create_courses",
                               **params
                           },
                           timeout=10)

        json_data = json.loads(res.text)

        if json_data is not None and 'exception' in json_data:
            raise Exception(json_data['message'])
        return json_data


    def delete_cohorts(self, cohortids: list[int]):
        """
        Supprime une cohorte de moodle.
        L'utilisateur WebService doit avoir la permission moodle/cohort:manage.

        :param cohortids: La liste des identifiants des cohortes
        :returns: None si la fonction s'est éxécutée correctement
        :raises Exception: Si le WebService renvoie une exception
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
                           timeout=10)

        json_data = json.loads(res.text)

        if json_data is not None and 'exception' in json_data:
            raise Exception(json_data['message'])
        return json_data
