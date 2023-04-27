# coding: utf-8
# pylint: disable=too-many-lines
"""
Accès à la base de données Moodle
"""

import mysql.connector
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from synchromoodle.config import DatabaseConfig, ConstantesConfig

###############################################################################
# CONSTANTS
###############################################################################

#######################################
# CONTEXTES
#######################################
# Id du contexte systeme
ID_CONTEXT_SYSTEM = 1

# Profondeur pour le contexte etablissement
PROFONDEUR_CTX_ETAB = 2

# Profondeur pour le contexte du bloc de recherche de la zone privee
PROFONDEUR_CTX_BLOCK_ZONE_PRIVEE = 4

# Profondeur pour le contexte du module de la zone privee
PROFONDEUR_CTX_MODULE_ZONE_PRIVEE = 4

# Profondeur pour le contexte de la zone privee
PROFONDEUR_CTX_ZONE_PRIVEE = 3

#######################################
# COURS
#######################################

# Format pour la zone privee d'un etablissement
COURSE_FORMAT_ZONE_PRIVEE = "topics"

# Fullname pour la zone privee d'un etablissement
COURSE_FULLNAME_ZONE_PRIVEE = "Zone privée"

# Shortname pour la zone privee d'un etablissement
# Le (%s) est reserve au siren de l'etablissement
COURSE_SHORTNAME_ZONE_PRIVEE = "ZONE-PRIVEE-%s"

# Summary pour la zone privee d'un etablissement
# Le (%s) est reserve a l'organisation unit de l'etablissement
COURSE_SUMMARY_ZONE_PRIVEE = "Forum réservé au personnel éducatif de l'établissement %s"

# Visibilite pour la zone privee d'un etablissement
COURSE_VISIBLE_ZONE_PRIVEE = 0

#######################################
# MODULE DE COURS
#######################################
# Nombre pour le module du forum dans la zone privee
COURSE_MODULES_MODULE = 5

#######################################
# ROLES
#######################################
# Enrol method => manual enrolment
ENROL_METHOD_MANUAL = "manual"

# Shortname du role admin local
SHORTNAME_ADMIN_LOCAL = "adminlocal"

# Shortname du role extended teacher
SHORTNAME_EXTENDED_TEACHER = "extendedteacher"

# Shortname du role advanced teacher
SHORTNAME_ADVANCED_TEACHER = "advancedteacher"

#######################################
# USER
#######################################
# Default authentication mode for a user
USER_AUTH = "cas"

# Default city for a user
USER_CITY = "Non renseignée"

# Default country for a user
USER_COUNTRY = "FR"

# Default language for a user
USER_LANG = "fr"

# Default moodle site for the user
# This field is a foreign key of the mdl_mnet_host
# Here "3" stands for the ID of lycees.netocentre.fr
USER_MNET_HOST_ID = 3


def array_to_safe_sql_list(elements: list, name=None) -> str:
    """
    Formate une liste python en chaine de caractères pour
    l'intégrer dans une requête sql par la suite.

    :param elements: La liste à traiter
    :param name:
    :return: La liste sous forme d'une chaine de caractères
    """
    if name:
        format_strings = []
        params = {}
        for i, element in enumerate(elements):
            format_strings.append(f'%({name}_{i})s')
            params[f'{name}_{i}'] = element
        return ','.join(format_strings), params
    format_strings = ['%s'] * len(elements)
    params = tuple(elements)
    return ','.join(format_strings), params


class Cohort:
    """
    Données associées à une cohorte.
    """

    def __init__(self, cohortid=None, contextid=None,
                 name=None, idnumber=None,
                 description=None, descriptionformat=None,
                 visible=None, component=None,
                 timecreated=None, timemodified=None,
                 theme=None):
        self.id = cohortid
        self.contextid = contextid
        self.name = name
        self.idnumber = idnumber
        self.description = description
        self.descriptionformat = descriptionformat
        self.visible = visible
        self.component = component
        self.timecreated = timecreated
        self.timemodified = timemodified
        self.theme = theme


class Database:
    """
    Couche d'accès à la base de données Moodle.
    """
    config = None  # type: DatabaseConfig
    constantes = None  # type: ConstantesConfig
    connection = None  # type: MySQLConnection
    mark = None  # type: MySQLCursor
    entete = None  # type: str

    def __init__(self, config: DatabaseConfig, constantes: ConstantesConfig):
        self.config = config
        self.constantes = constantes
        self.entete = config.entete

    def connect(self):
        """
        Etablit la connexion à la base de données Moodle
        """
        self.connection = mysql.connector.connect(host=self.config.host,
                                                  user=self.config.user,
                                                  passwd=self.config.password,
                                                  db=self.config.database,
                                                  charset=self.config.charset,
                                                  port=self.config.port)
        self.mark = self.connection.cursor()

    def disconnect(self):
        """
        Ferme la connexion à la base de données Moodle
        """
        if self.mark:
            self.mark.close()
            self.mark = None
        if self.connection:
            self.connection.close()
            self.connection = None

    def safe_fetchone(self) -> tuple:
        """
        Retourne uniquement 1 résultat et lève une exception si la requête invoquée récupère plusieurs resultats.

        raises DatabaseError: Si il y a plus d'un résultat
        :return: Le résultat obtenu
        """
        rows = self.mark.fetchall()
        count = len(rows)
        if count > 1:
            raise mysql.connector.DatabaseError("Résultat de requête SQL invalide: 1 résultat attendu, %d reçus:\n%s"
                                                % (count, self.mark.statement))
        return rows[0] if count == 1 else None

    def add_role_to_user(self, role_id: int, id_context: int, id_user: int):
        """
        Fonction permettant d'ajouter un role a un utilisateur
        pour un contexte donne.

        :param role_id: L'id du rôle moodle
        :param id_context: L'id du contexte moodle
        :param id_user: L'id de l'utilisateur
        """
        id_role_assignment = self.get_id_role_assignment(role_id, id_context, id_user)
        if not id_role_assignment:
            # Ajout du role dans le contexte
            s = "INSERT INTO {entete}role_assignments( roleid, contextid, userid )" \
                " VALUES ( %(role_id)s, %(id_context)s, %(id_user)s )".format(entete=self.entete)
            self.mark.execute(s, params={'role_id': role_id, 'id_context': id_context, 'id_user': id_user})

    def remove_role_to_user(self, role_id: int, id_context: int, id_user: int):
        """
        Fonction permettant de supprimer un role a un utilisateur
        pour un contexte donne.

        :param role_id: L'id du rôle moodle
        :param id_context: L'id du contexte moodle
        :param id_user: L'id de l'utilisateur
        """
        id_role_assignment = self.get_id_role_assignment(role_id, id_context, id_user)
        if id_role_assignment:
            # Ajout du role dans le contexte
            s = "DELETE FROM {entete}role_assignments" \
                " WHERE roleid = %(role_id)s" \
                " AND contextid = %(id_context)s" \
                " AND userid = %(id_user)s".format(entete=self.entete)
            self.mark.execute(s, params={'role_id': role_id, 'id_context': id_context, 'id_user': id_user})

    def get_id_role_assignment(self, role_id: int, id_context: int, id_user: int) -> int:
        """
        Fonction permettant de recuperer l'id d'un "role_assignement" au sein de la BD moodle.

        :param role_id: L'id du rôle moodle
        :param id_context: L'id du contexte moodle
        :param id_user: L'id de l'utilisateur
        :return: L'id récupéré dans la table mdl_role_assignments
        """
        s = "SELECT id FROM {entete}role_assignments" \
            " WHERE roleid = %(role_id)s AND contextid = %(id_context)s AND userid = %(id_user)s" \
            " LIMIT 1" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'role_id': role_id, 'id_context': id_context, 'id_user': id_user})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def enroll_user_in_course(self, role_id: int, id_course: int, id_user: int):
        """
        Fonction permettant d'enroler un utilisateur dans un cours.

        :param role_id: L'id du rôle à donner à l'utilisateur dans le cours
        :param id_course: L'id du cours dans lequel on veut inscrire l'utilisateur
        :param id_user: L'id de l'utilisateur à inscrire
        """
        id_enrol = self.get_id_enrol(ENROL_METHOD_MANUAL, role_id, id_course)
        if not id_enrol:
            # Ajout de la methode d'enrolment dans le cours
            s = "INSERT INTO {entete}enrol(enrol, courseid, roleid)" \
                " VALUES (%(ENROL_METHOD_MANUAL)s, %(id_course)s, %(role_id)s)" \
                .format(entete=self.entete)
            self.mark.execute(s, params={'ENROL_METHOD_MANUAL': ENROL_METHOD_MANUAL, 'id_course': id_course,
                                         'role_id': role_id})
            id_enrol = self.get_id_enrol_max()
        if id_enrol:
            # Enrolement de l'utilisateur dans le cours
            s = "INSERT IGNORE INTO {entete}user_enrolments(enrolid, userid)" \
                " VALUES (%(id_enrol)s, %(id_user)s)" \
                .format(entete=self.entete)
            self.mark.execute(s, params={'id_enrol': id_enrol, 'id_user': id_user})

    def get_id_enrol_max(self) -> int:
        """
        Récupère l'id maximum present dans la table permettant les enrolments.

        :return: L'id maximum
        """
        s = f"SELECT id FROM {self.entete}enrol ORDER BY id DESC LIMIT 1"
        self.mark.execute(s)
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def create_cohort(self, id_context: int, name: str, id_number: str,
     description: str, time_created):
        """
        Fonction permettant de creer une nouvelle cohorte pour un contexte donné.

        :param id_context: L'id du contexte dans lequel on veut créer la cohorte
        :param name: Le nom de la cohorte à créer
        :param id_number: L'id_number de la cohorte à créer
        :param description: La description de la cohorte à créer
        :param time_created: La date de création de la cohorte
        """
        s = "INSERT INTO {entete}cohort(contextid, name, idnumber, description, descriptionformat, timecreated," \
            " timemodified)" \
            " VALUES (%(id_context)s, %(name)s, %(id_number)s, %(description)s, 0, %(time_created)s," \
            " %(time_created)s)" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'id_context': id_context, 'name': name, 'id_number': id_number,
                                     'description': description, 'time_created': time_created})

    def disenroll_user_from_username_and_cohortname(self, username: str, cohortname: str):
        """
        Désenrole un utilisateur d'une cohorte.

        :param username: Le nom de l'utilisateur
        :param cohortname: Le nom de la cohorte
        """
        self.mark.execute("DELETE {entete}cohort_members FROM {entete}cohort_members"
                          " INNER JOIN {entete}cohort"
                          " ON {entete}cohort_members.cohortid = {entete}cohort.id"
                          " INNER JOIN {entete}user"
                          " ON {entete}cohort_members.userid = {entete}user.id"
                          " WHERE {entete}user.username = %(username)s"
                          " AND {entete}cohort.name = %(cohortname)s".format(entete=self.entete),
                          params={
                              'username': username,
                              'cohortname': cohortname
                          })

    def disenroll_user_from_username_and_cohortid(self, username: str, cohortid: int):
        """
        Désenrole un utilisateur d'une cohorte.

        :param username: Le nom de l'utilisateur
        :param cohortid: L'id de la cohorte.
        """
        self.mark.execute("DELETE {entete}cohort_members FROM {entete}cohort_members"
                          " INNER JOIN {entete}cohort"
                          " ON {entete}cohort_members.cohortid = {entete}cohort.id"
                          " INNER JOIN {entete}user"
                          " ON {entete}cohort_members.userid = {entete}user.id"
                          " WHERE {entete}user.username = %(username)s"
                          " AND {entete}cohort.id = %(cohortid)s".format(entete=self.entete),
                          params={
                              'username': username,
                              'cohortid': cohortid
                          })

    def get_empty_cohorts(self) -> list[int]:
        """
        Récupère la liste des ids de toutes les cohortes qui n'ont aucun membre.

        :return: La liste des ids de toutes les cohortes qui n'ont aucun membre
        """
        s = "SELECT id FROM {entete}cohort WHERE id NOT IN (SELECT cohortid FROM {entete}cohort_members)" \
            .format(entete=self.entete)
        self.mark.execute(s)
        result_set = self.mark.fetchall()
        if not result_set:
            return []
        cohort_ids = [result[0] for result in result_set]
        return cohort_ids

    def get_id_cohort(self, id_context: int, cohort_name: str) -> int:
        """
        Fonction permettant de recuperer l'id d'une cohorte par son nom et son contexte de rattachement.

        :param id_context: L'id du contexte associé à la cohorte
        :param cohort_name: Le nom de la cohorte
        :return: L'id de la cohorte trouvée
        """
        s = "SELECT id" \
            " FROM {entete}cohort" \
            " WHERE contextid = %(id_context)s" \
            " AND name = %(cohort_name)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'id_context': id_context, 'cohort_name': cohort_name})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_user_id(self, username: str) -> int:
        """
        Fonction permettant de recuperer l'id d'un utilisateur moodle via son username.

        :param username: Le nom d'utilisateur recherché (colonne username).
        :return:
        """
        s = f"SELECT id FROM {self.entete}user WHERE username = %(username)s"
        self.mark.execute(s, params={'username': username.lower()})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def enroll_user_in_cohort(self, id_cohort: int, id_user: int, time_added: int):
        """
        Fonction permettant d'ajouter un utilisateur à une cohorte.

        :param id_cohort: L'id de la cohorte dans laquelle on veut enroler l'utilisateur
        :param id_user: L'id de l'utilisateur
        :param time_added: La date à laquelle on à ajouté l'utilisateur dans la cohorte
        """
        s = "INSERT IGNORE" \
            " INTO {entete}cohort_members(cohortid, userid, timeadded)" \
            " VALUES (%(id_cohort)s, %(id_user)s, %(time_added)s)" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'id_cohort': id_cohort, 'id_user': id_user, 'time_added': time_added})

    def delete_moodle_local_admins(self, id_context_categorie: int, ids_not_admin: list[int]):
        """
        Fonction permettant de supprimer les admins locaux
        d'un contexte en gardant uniquement les admins specifies.

        :param id_context_categorie: L'id du contexte
        :param ids_not_admin: Les ids à supprimer
        """
        if not ids_not_admin:
            return
        # Construction de la liste des ids admins a conserver
        ids_list, ids_list_params = array_to_safe_sql_list(ids_not_admin, 'ids_list')
        # Recuperation de l'id pour le role d'admin local
        id_role_admin_local = self.get_id_role_admin_local()
        # Suppression des admins non presents dans la liste
        s = "DELETE FROM {entete}role_assignments" \
            " WHERE roleid = %(id_role_admin_local)s" \
            " AND contextid = %(id_context_categorie)s" \
            " AND userid IN ({ids_list})" \
            .format(entete=self.entete, ids_list=ids_list)
        self.mark.execute(s, params={'id_role_admin_local': id_role_admin_local,
                                     'id_context_categorie': id_context_categorie, **ids_list_params})

    def get_id_role_admin_local(self) -> int:
        """
        Fonction permettant de recuperer l'id du role admin local
        au sein de la BD moodle.

        :return: L'id du role admin local
        """
        return self.get_id_role_by_shortname(SHORTNAME_ADMIN_LOCAL)

    def get_id_role_by_shortname(self, short_name: str) -> int:
        """
        Fonction permettant de recuperer l'id d'un role via son shortname.

        :param short_name: Le shortname du role
        :return: L'id du rôle
        """
        s = f"SELECT id FROM {self.entete}role WHERE shortname = %(short_name)s"
        self.mark.execute(s, params={'short_name': short_name})
        ligne = self.safe_fetchone()
        if ligne is None:
            raise ValueError(f"Le rôle {short_name} n'existe pas.")
        return ligne[0]

    def delete_moodle_local_admin(self, id_context_categorie: int, userid: int):
        """
        Fonction permettant de supprimer un admin local d'un contexte.

        :param id_context_categorie: L'id du contexte
        :param userid: L'id de l'ancien admin local
        """
        id_role_admin_local = self.get_id_role_admin_local()
        self.delete_moodle_assignment(id_context_categorie, userid, id_role_admin_local)

    def delete_moodle_assignment(self, id_context_category: int, userid: int, roleid: int):
        """
        Fonction permettant de supprimer un role à un utilisateur dans un contexte.

        :param id_context_category: L'id du contexte
        :param userid: L'id de l'utilisateur
        :param roleid: L'id du rôle
        """
        s = "DELETE FROM {entete}role_assignments" \
            " WHERE contextid = %(id_context_category)s" \
            " AND roleid = %(roleid)s" \
            " AND userid = %(userid)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'id_context_category': id_context_category, 'roleid': roleid, 'userid': userid})

    def delete_role_for_contexts(self, role_id: int, ids_contexts_by_courses: list[int], id_user: int):
        """
        Fonction permettant de supprimer un role sur differents
        contextes pour l'utilisateur spécifié.

        :param role_id: L'id du role
        :param ids_contexts_by_courses: La listttte des ids de contexte
        :param id_user: L'id de l'utilisateur
        """
        # Suppression des enrolments dans les cours
        for id_course in ids_contexts_by_courses:
            # Recuperation de la methode d'enrolment
            id_enrol = self.get_id_enrol(ENROL_METHOD_MANUAL, role_id, id_course)
            if not id_enrol:
                continue
            # Suppression de l'enrolment associe
            id_user_enrolment = self.get_id_user_enrolment(id_enrol, id_user)
            if id_user_enrolment:
                s = "DELETE FROM {entete}user_enrolments " \
                    "WHERE id = %(id_user_enrolment)s" \
                    .format(entete=self.entete)
                self.mark.execute(s, params={'id_user_enrolment': id_user_enrolment})

        # Suppression des roles dans les contextes
        ids_list, ids_list_params = array_to_safe_sql_list(ids_contexts_by_courses.values(), 'ids_list')
        s = "DELETE FROM {entete}role_assignments" \
            " WHERE roleid = %(role_id)s" \
            " AND contextid IN ({ids_list})" \
            " AND userid = %(id_user)s" \
            .format(entete=self.entete, ids_list=ids_list)
        self.mark.execute(s, params={'role_id': role_id, 'id_user': id_user, **ids_list_params})

    def get_id_enrol(self, enrol_method: str, role_id: int, id_course: int) -> int:
        """
        Fonction permettant de recuperer un id dans la table permettant les enrolments.

        :param enrol_method: La méthode d'enrolement
        :param role_id: L'id du rôle
        :param id_course: L'id du cours dans laquel on a donné le rôle avec cette méthode
        :return: L'id de l'enrolement
        """
        s = "SELECT e.id FROM {entete}enrol AS e" \
            " WHERE e.enrol = %(enrol_method)s" \
            " AND e.courseid = %(id_course)s" \
            " AND e.roleid = %(role_id)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'enrol_method': enrol_method, 'id_course': id_course, 'role_id': role_id})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_id_user_enrolment(self, id_enrol: int, id_user: int) -> int:
        """
        Fonction permettant de recuperer l'id d'un user enrolment.

        :param id_enrol: L'id de l'enrolement (table mdl_enrol)
        :param id_user: L'id de l'utilisateur
        :return: L'id du user enrolment
        """
        s = "SELECT id" \
            " FROM {entete}user_enrolments " \
            " WHERE userid = %(id_user)s" \
            " AND enrolid = %(id_enrol)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'id_user': id_user, 'id_enrol': id_enrol})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def delete_roles(self, ids_roles: list[int]):
        """
        Fonction permettant de supprimer des roles.

        :param ids_roles: Les ids des rpoles à supprimer
        """
        # Construction de la liste des ids des roles concernes
        ids_list, ids_list_params = array_to_safe_sql_list(ids_roles, 'ids_list')
        s = f"DELETE FROM {self.entete}role_assignments WHERE id IN ({ids_list})"
        self.mark.execute(s, params={**ids_list_params})

    def disenroll_user_from_cohorts(self, ids_cohorts_to_keep: list[int], id_user: int):
        """
        Fonction permettant d'enlever un utilisateur d'une ou plusieurs cohortes.
        Seules les inscriptions dans les cohortes passées en paramètres sont conservées.

        :param ids_cohorts_to_keep: Les ids des cohortes à garder
        :param id_user: L'id de l'utilisateur
        """
        # Construction de la liste des ids des cohortes concernes
        ids_list, ids_list_params = array_to_safe_sql_list(ids_cohorts_to_keep, 'ids_list')
        s = "DELETE FROM {entete}cohort_members" \
            " WHERE userid = %(id_user)s" \
            " AND cohortid NOT IN ({ids_list})" \
            .format(entete=self.entete, ids_list=ids_list)
        self.mark.execute(s, params={'id_user': id_user, **ids_list_params})

    def disenroll_user_from_cohort(self, id_cohort: int, id_user: int):
        """
        Fonction permettant d'enlever un utilisateur d'une cohorte.

        :param id_cohort: L'id de la cohorte
        :param id_user: L'id de l'utilisateur
        """
        s = "DELETE FROM {entete}cohort_members" \
            " WHERE cohortid = %(id_cohort)s" \
            " AND userid = %(id_user)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'id_cohort': id_cohort, 'id_user': id_user})

    def get_cohort_name(self, id_cohort: int) -> str:
        """
        Fonction permettant de recuperer le nom d'une cohorte à partir de son id.

        :param id_cohort: L'id de la cohorte
        :return: Le nom de la cohorte
        """
        s = f"SELECT name FROM {self.entete}cohort WHERE id = %(id_cohort)s"
        self.mark.execute(s, params={'id_cohort': id_cohort})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_description_course_category(self, id_category: int) -> str:
        """
        Fonction permettant de recuperer la description d'une catégorie.

        :param id_category: L'id de la catégorie
        :return: La description de la catégorie
        """
        s = "SELECT description" \
            " FROM {entete}course_categories" \
            " WHERE id = %(id_category)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'id_category': id_category})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_descriptions_course_categories_by_themes(self, themes: list[str]) -> list[str]:
        """
        Fonction permettant de recuperer les descriptions de categories.

        :param themes: La liste des thèmes dont on veut récupérer les descriptions
        :return: La liste des descriptions
        """
        ids_list, ids_list_params = array_to_safe_sql_list(themes, 'ids_list')
        s = "SELECT description" \
            " FROM {entete}course_categories" \
            " WHERE theme IN ({ids_list})" \
            .format(entete=self.entete, ids_list=ids_list)
        self.mark.execute(s, params={**ids_list_params})
        result_set = self.mark.fetchall()
        if not result_set:
            return []
        descriptions = [result[0] for result in result_set]
        return descriptions

    def get_id_block(self, parent_context_id: int) -> int:
        """
        Fonction permettant de recuperer l'id d'un bloc.

        :param parent_context_id: L'id du contexte
        :return: L'id du bloc
        """
        s = "SELECT id" \
            " FROM {entete}block_instances" \
            " WHERE parentcontextid = %(parent_context_id)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'parent_context_id': parent_context_id})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_course_timemodified(self, course_id: int) -> int:
        """
        Permet de récupérer la date de dernière modification d'un cours.

        :param course_id: L'id du cours recherché
        :return: La date de dernière modification
        """
        s = f"SELECT timemodified FROM {self.entete}course WHERE id = %(course_id)s"
        self.mark.execute(s, params={'course_id': course_id})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_courses_ids_owned_by(self, user_id: int) -> list[int]:
        """
        Recherche tous les cours dont l'utilisateur est propriétaire.

        :param user_id: L'id de l'utilisateur concerné
        :returns: La liste des cours dont l'utilisateur est propriétaire
        """
        s = "SELECT instanceid FROM {entete}context AS context" \
            " INNER JOIN {entete}role_assignments AS role_assignments" \
            " ON context.id = role_assignments.contextid" \
            " WHERE role_assignments.userid = %(userid)s AND role_assignments.roleid = %(roleid)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'userid': user_id, 'roleid': self.constantes.id_role_proprietaire_cours})
        return self.mark.fetchall()

    def get_courses_ids_owned_or_teach(self, user_id: int) -> list[int]:
        """
        Retourne tous les cours auxquels participe un utilisateur
        en tant qu'enseignant (role enseignant ou propriétaire de cours).

        :param user_id: L'id de l'utilisateur concerné
        :returns: La liste des cours dans lequel enseigne l'utilisateur
        """
        s = "SELECT instanceid FROM {entete}context AS context" \
            " INNER JOIN {entete}role_assignments AS role_assignments" \
            " ON context.id = role_assignments.contextid" \
            " WHERE role_assignments.userid = %(userid)s AND (role_assignments.roleid = %(roleidowner)s" \
            " OR role_assignments.roleid = %(roleidteacher)s)" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'userid': user_id, 'roleidowner': self.constantes.id_role_proprietaire_cours,
        'roleidteacher': self.constantes.id_role_enseignant})
        return self.mark.fetchall()

    def get_userids_owner_of_course(self, course_id: int) -> list[int]:
        """
        Retourne tous les utilisateurs qui sont propriétaires d'un cours.

        :param course_id: L'id du cours concerné
        :returns: La liste des utilisateurs propriétaires du cours
        """
        s = "SELECT userid FROM {entete}role_assignments AS role_assignments" \
            " INNER JOIN {entete}context AS context" \
            " ON role_assignments.contextid = context.id" \
            " WHERE context.instanceid = %(courseid)s AND role_assignments.roleid = %(roleid)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'courseid': course_id, 'roleid': self.constantes.id_role_proprietaire_cours})
        return self.mark.fetchall()

    def get_user_data(self, user_id: int) -> tuple:
        """
        Retourne les informations détaillées sur un utilisateur (table mdl_user).

        :param user_id: L'id de l'utilisateur dont on veut récupére les infos
        :returns: Un tuple représentant la ligne récupérée depuis la BD
        """
        s = f"SELECT * FROM {self.entete}user WHERE id = %(userid)s"
        self.mark.execute(s, params={'userid': user_id})
        return self.mark.fetchone()

    def user_has_used_moodle(self, user_id: int) -> bool:
        """
        Indique si un utilisateur à déjà utilisé moodle, c'est-à-dire s'il s'est déjà connecté.

        :param user_id: L'id de l'utilisateur qu'on veut vérifier
        :returns: Un booléen, qui vaut True si l'utilisateur à déjà utilisé moodle, et False sinon
        """
        s = f"SELECT lastlogin FROM {self.entete}user WHERE id = %(userid)s"
        self.mark.execute(s, params={'userid': user_id})
        return self.mark.fetchone()[0] != 0

    def eleve_has_references(self, user_id: int) -> bool:
        """
        Indique si un élève dipose de références dans des exercices ou des notations moodle.
        Les références comprennent :
        - des notes obtenues dans n'importe quelle activité (historique de notes)
        - des réponses à une activité (feedback, test, consultation, sondage)
        - des participations à une activités (forum, chat)

        :param user_id: L'id de l'utilisateur qu'on veut vérifier
        :returns: Un booléen à vrai si l'utilisateur à des références, faux sinon
        """

        #Dès qu'on trouve une référence on renvoie True
        s = f"SELECT count(*) FROM {self.entete}forum_posts WHERE userid = %(userid)s"
        self.mark.execute(s, params={'userid': user_id})
        if self.mark.fetchone()[0] > 0:
            return True

        s = f"SELECT count(*) FROM {self.entete}grade_grades_history WHERE userid = %(userid)s"
        self.mark.execute(s, params={'userid': user_id})
        if self.mark.fetchone()[0] > 0:
            return True

        s = f"SELECT count(*) FROM {self.entete}feedback_completed WHERE userid = %(userid)s"
        self.mark.execute(s, params={'userid': user_id})
        if self.mark.fetchone()[0] > 0:
            return True

        s = f"SELECT count(*) FROM {self.entete}chat_messages WHERE userid = %(userid)s"
        self.mark.execute(s, params={'userid': user_id})
        if self.mark.fetchone()[0] > 0:
            return True

        s = f"SELECT count(*) FROM {self.entete}course_modules_completion WHERE userid = %(userid)s"
        self.mark.execute(s, params={'userid': user_id})
        if self.mark.fetchone()[0] > 0:
            return True

        s = f"SELECT count(*) FROM {self.entete}quiz_attempts WHERE userid = %(userid)s"
        self.mark.execute(s, params={'userid': user_id})
        if self.mark.fetchone()[0] > 0:
            return True

        s = f"SELECT count(*) FROM {self.entete}survey_answers WHERE userid = %(userid)s"
        self.mark.execute(s, params={'userid': user_id})
        if self.mark.fetchone()[0] > 0:
            return True

        s = f"SELECT count(*) FROM {self.entete}choice_answers WHERE userid = %(userid)s"
        self.mark.execute(s, params={'userid': user_id})
        if self.mark.fetchone()[0] > 0:
            return True

        #Si jamais on n'a trouvé aucune référence, alors on peut renvoyer False
        return False

    def enseignant_has_references(self, user_id: int) -> bool:
        """
        Indique si un enseignant dipose de références dans des exercices ou des notations moodle.
        Les références comprennent des notes qui ont été données à des étudiants dans des cours.

        :param user_id: L'id de l'utilisateur qu'on veut vérifier
        :returns: Un booléen à vrai si l'utilisateur à des références, faux sinon
        """
        s = f"SELECT count(*) FROM {self.entete}grade_grades_history WHERE loggeduser = %(userid)s"
        self.mark.execute(s, params={'userid': user_id})
        if self.mark.fetchone()[0] > 0:
            return True
        return False

    def get_id_categorie(self, categorie_name: str) -> int:
        """
        Fonction permettant de recuperer l'id correspondant à un nom de catégorie.

        :param categorie_name: Le nom de la catégorie
        :return: L'id de la catégorie trouvée
        """
        s = "SELECT id" \
            " FROM {entete}course_categories" \
            " WHERE name = %(categorie_name)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'categorie_name': categorie_name})
        ligne = self.safe_fetchone()
        return ligne[0] if ligne else None

    def get_id_context_no_depth(self, context_level: int, instance_id: int) -> int:
        """
        Fonction permettant de recuperer l'id d'un contexte via
        le niveau et l'id de l'instance associée.

        :param context_level: Le niveau du contexte recherché
        :param instance_id: L'id de l'instance recherché
        :return: L'id du contexte associé
        """
        s = "SELECT id" \
            " FROM {entete}context" \
            " WHERE contextlevel = %(context_level)s" \
            " AND instanceid = %(instance_id)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'context_level': context_level, 'instance_id': instance_id})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_id_context(self, context_level: int, depth: int, instance_id: int) -> int:
        """
        Fonction permettant de recuperer l'id d'un contexte via
        le niveau, la profondeur et l'id de l'instance associée.

        :param context_level: Le niveau du contexte recherché
        :param depth: La profondeur recherchée
        :param instance_id: L'id de l'instance recherché
        :return: L'id du contexte associé
        """
        s = "SELECT id" \
            " FROM {entete}context" \
            " WHERE contextlevel = %(context_level)s" \
            " AND depth = %(depth)s" \
            " AND instanceid = %(instance_id)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'context_level': context_level, 'depth': depth, 'instance_id': instance_id})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_id_context_categorie(self, id_etab_categorie: int) -> int:
        """
        Fonction permettant de recuperer l'id d'une contexte via l'id d'un etablissement.

        :param id_etab_categorie: L'id de la catégorie de cours associée à l'établissement
        :return: L'id du contexte associé
        """
        return self.get_id_context(self.constantes.niveau_ctx_categorie, 2, id_etab_categorie)

    def get_id_context_inter_etabs(self) -> int:
        """
        Fonction permettant de recuperer l'id du contexte de la categorie inter-etablissements.

        :return: L'id du contexte inter-établissements
        """
        s = "SELECT id" \
            " FROM {entete}context" \
            " WHERE contextlevel = %(context_level)s" \
            " AND instanceid = %(instanceid)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'context_level': self.constantes.niveau_ctx_categorie,
                                     'instanceid': self.constantes.id_instance_moodle})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_id_course_by_id_number(self, id_number: str) -> int:
        """
        Fonction permettant de recuperer l'id d'un cours a partir de son idnumber.

        :param id_number: L'idnumber recherché
        :return: L'id du cours
        """
        s = f"SELECT id FROM {self.entete}course WHERE idnumber = %(id)s"
        self.mark.execute(s, params={'id': id_number})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_id_course_category_by_id_number(self, id_number: str) -> int:
        """
        Récupère l'id d'une categorie à partir de son idnumber.

        :param id_number: L'idnumber recherché
        :return: L'id de la catégorie
        """
        s = f"SELECT id FROM {self.entete}course_categories WHERE idnumber LIKE %(id)s"
        self.mark.execute(s, params={'id': '%' + str(id_number) + '%'})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_id_course_category_by_theme(self, theme: str) -> int:
        """
        Récupère l'id d'une categorie à partir de son theme.

        :param theme: Le thème dont on veut recherher l'id de catégorie
        :return: L'id de catégorie associé au thème
        """
        s = f"SELECT id FROM {self.entete}course_categories WHERE theme = %(theme)s"
        self.mark.execute(s, params={'theme': theme})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_id_course_module(self, course: int) -> int:
        """
        Récupère l'id d'un module de cours.

        :param course: L'id du cours
        :return: L'id du module du cours
        """
        s = f"SELECT id FROM {self.entete}course_modules WHERE course = %(course)s"
        self.mark.execute(s, params={'course': course})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_id_forum(self, course: int) -> int:
        """
        Fonction permettant de recuperer l'id du forum associé à un cours.

        :param course: L'id du cours associé au forum
        :return: L'id du forum
        """
        s = f"SELECT id FROM {self.entete}forum WHERE course = %(course)s"
        self.mark.execute(s, params={'course': course})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_id_user_info_data(self, id_user: int, id_field: int) -> int:
        """
        Fonction permettant de recuperer l'id d'un info data via l'id-user et l'id_field.

        :param id_user: L'id de l'utilisateur
        :param id_field: L'id du field
        :return: L'id de l'info data
        """
        s = "SELECT id" \
            " FROM {entete}user_info_data " \
            " WHERE userid = %(id_user)s" \
            " AND fieldid = %(id_field)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'id_user': id_user, 'id_field': id_field})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_id_user_info_field_by_shortname(self, short_name: str) -> int:
        """
        Fonction permettant de recuperer l'id d'un info field via son shortname.

        :param short_name: Le short_name de l'info field
        :return: L'id du user info field
        """
        s = "SELECT id" \
            " FROM {entete}user_info_field" \
            " WHERE shortname = %(short_name)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'short_name': short_name})
        ligne = self.safe_fetchone()
        if ligne is None:
            return None
        return ligne[0]

    def get_ids_and_summaries_not_allowed_roles(self, id_user: int, allowed_forums_shortnames: list[str]) -> tuple[int,str]:
        """
        Fonction permettant de recuperer les ids des roles non autorises sur
        les forums, ainsi que les noms des forums sur lesquels portent ces roles.

        :param id_user: L'id de l'utilisateur
        :param allowed_forums_shortnames: Les noms des forums autorisés pour l'utilisateur
        :return: Un tuple avec la liste des ids et la liste des forums non autorisés
        """
        # Construction de la liste des shortnames
        ids_list, ids_list_params = array_to_safe_sql_list(allowed_forums_shortnames, 'ids_list')
        s = "SELECT mra.id, mco.summary" \
            " FROM {entete}course mco, {entete}role_assignments mra, {entete}context mc" \
            " WHERE mco.shortname LIKE 'ZONE-PRIVEE-%%'" \
            " AND mco.shortname NOT IN ({ids_list})" \
            " AND mco.id = mc.instanceid" \
            " AND mc.contextlevel = 50" \
            " AND mc.id = mra.contextid" \
            " AND mra.userid = %(id_user)s" \
            .format(entete=self.entete, ids_list=ids_list)
        self.mark.execute(s, params={'id_user': id_user, **ids_list_params})
        result_set = self.mark.fetchall()
        if not result_set:
            return [], []
        # Recuperation des ids et themes non autorises
        ids = [result[0] for result in result_set]
        summaries = [result[1] for result in result_set]
        return ids, summaries

    def get_ids_and_themes_not_allowed_roles(self, id_user: int, allowed_themes: list[str]) -> tuple[int,str]:
        """
        Fonction permettant de recuperer les ids des roles qui ne sont pas autorises pour l'utilisateur.

        :param id_user: L'id de l'utilisateur
        :param allowed_themes: La liste des thèmes autorisés
        :return: Un tuple avec la liste des ids et la liste des thèmes non autorisés
        """
        # Construction de la liste des themes
        ids_list, ids_list_params = array_to_safe_sql_list(allowed_themes, 'ids_list')
        # Recuperation des roles sur les etablissements qui ne devraient plus exister
        # (quand le prof n'est plus rattache aux etablissements)
        s = "SELECT mra.id, mcc.theme" \
            " FROM {entete}course_categories mcc, {entete}context mc, {entete}role_assignments mra" \
            " WHERE mcc.theme NOT IN ({ids_list})" \
            " AND mcc.theme IS NOT NULL" \
            " AND mcc.id = mc.instanceid " \
            " AND mc.contextlevel = %(NIVEAU_CTX_CATEGORIE)s AND mc.depth = %(PROFONDEUR_CTX_ETAB)s" \
            " AND mc.id = mra.contextid" \
            " AND mra.userid = %(id_user)s" \
            .format(entete=self.entete, ids_list=ids_list)
        self.mark.execute(s, params={**ids_list_params, 'NIVEAU_CTX_CATEGORIE': self.constantes.niveau_ctx_categorie,
                                     'PROFONDEUR_CTX_ETAB': PROFONDEUR_CTX_ETAB, 'id_user': id_user})
        result_set = self.mark.fetchall()
        if not result_set:
            return [], []
        # Recuperation des ids et themes non autorises
        ids = [result[0] for result in result_set]
        themes = [result[1] for result in result_set]
        return ids, themes

    def get_timestamp_now(self) -> int:
        """
        Fonction permettant de recuperer le timestamp actuel.

        :return: Le timestamp
        """
        s = "SELECT UNIX_TIMESTAMP( now( ) ) - 3600*2"
        self.mark.execute(s)
        now = self.mark.fetchone()[0]
        return now

    def get_users_ids(self, usernames: list[str]) -> list[int]:
        """
        Fonction permettant de recuperer les ids des utilisateurs moodle via leurs usernames.

        :param usernames: La liste des noms d'utilisateurs
        :return: La liste des ids des utilisateurs
        """
        users_ids = []
        for username in usernames:
            user_id = self.get_user_id(username)
            users_ids.append(user_id)
        return users_ids

    def user_has_role(self, userid: int, roles_list: list[int]) -> bool:
        """
        Vérifie si un utilisateur a au moins un role parmis une liste.

        :param userid: L'id de l'utilisateur
        :param roles_list: La liste des rôles
        :return: Vrai ou faux si il à au moins un rôle ou non
        """
        ids_list, ids_list_params = array_to_safe_sql_list(roles_list, 'ids_list')
        self.mark.execute("SELECT COUNT(role.id)"
                          " FROM {entete}role AS role"
                          " INNER JOIN {entete}role_assignments AS role_assignments"
                          " ON role.id = role_assignments.roleid"
                          " WHERE role_assignments.userid = %(userid)s"
                          " AND role.id IN ({ids_list})".format(entete=self.entete, ids_list=ids_list),
                          params={
                              'userid': userid,
                              **ids_list_params
                          })
        count = self.mark.fetchone()[0]
        return count > 0

    def get_all_valid_users(self) -> list[int]:
        """
        Retourne tous les utilisateurs de la base de données qui ne sont pas marqués comme "supprimés".

        :return: La liste des ids de tous utilisateurs qui ne sont pas marqués comme supprimés.
        """
        self.mark.execute("SELECT"
                          " id AS id,"
                          " username AS username,"
                          " lastlogin AS lastlogin"
                          " FROM {entete}user WHERE deleted = 0".format(entete=self.entete))
        return self.mark.fetchall()

    def anonymize_users(self, user_ids: list[int]):
        """
        Anonymise des utilisateurs de la BDD.

        :param user_ids: La liste des id à anonymiser
        """

        ids_list, ids_list_params = array_to_safe_sql_list(user_ids, 'ids_list')
        self.mark.execute("UPDATE {entete}user"
                          " SET firstname = %(anonymous_name)s,"
                          " lastname = %(anonymous_name)s,"
                          " firstnamephonetic = %(anonymous_name)s,"
                          " lastnamephonetic = %(anonymous_name)s,"
                          " middlename = %(anonymous_name)s,"
                          " alternatename = %(anonymous_name)s,"
                          " city = %(anonymous_name)s,"
                          " address = %(anonymous_name)s,"
                          " department = %(anonymous_name)s,"
                          " phone1 = %(anonymous_phone)s,"
                          " phone2 = %(anonymous_phone)s,"
                          " skype = %(anonymous_name)s,"
                          " yahoo = %(anonymous_name)s,"
                          " aim = %(anonymous_name)s,"
                          " msn = %(anonymous_name)s,"
                          " email = %(anonymous_mail)s,"
                          " description = NULL"
                          " WHERE id IN ({ids_list})"
                          .format(entete=self.entete, ids_list=ids_list),
                          params={
                              'anonymous_name': self.constantes.anonymous_name,
                              'anonymous_mail': self.constantes.anonymous_mail,
                              'anonymous_phone': self.constantes.anonymous_phone,
                              **ids_list_params
                          })

    def insert_moodle_block(self, block_name: str, parent_context_id: int, show_in_subcontexts: int,
     page_type_pattern: str, sub_page_pattern: int, default_region: str, default_weight: int):
        """
        Insère un bloc.

        :param block_name: Le nom du bloc
        :param parent_context_id: L'id du contexte parent
        :param show_in_subcontexts:
        :param page_type_pattern:
        :param sub_page_pattern:
        :param default_region:
        :param default_weight:
        """
        s = "INSERT INTO {entete}block_instances " \
            "( blockname, parentcontextid, showinsubcontexts, pagetypepattern, subpagepattern, defaultregion, " \
            "defaultweight, timecreated, timemodified ) " \
            " VALUES ( %(block_name)s, %(parent_context_id)s, %(show_in_subcontexts)s, %(page_type_pattern)s, " \
            "%(sub_page_pattern)s, %(default_region)s, %(default_weight)s, UNIX_TIMESTAMP( now( ) ) - 3600*2," \
            "UNIX_TIMESTAMP( now( ) ) - 3600*2 )" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'block_name': block_name,
                                     'parent_context_id': parent_context_id,
                                     'show_in_subcontexts': show_in_subcontexts,
                                     'page_type_pattern': page_type_pattern,
                                     'sub_page_pattern': sub_page_pattern,
                                     'default_region': default_region,
                                     'default_weight': default_weight})

    def insert_moodle_context(self, context_level: int, depth: int, instance_id: int):
        """
        Insère un contexte.

        :param context_level: Le niveau du contexte
        :param depth: La profondeur du contexte
        :param instance_id: L'id de l'instance associée au contexte
        """
        s = "INSERT INTO {entete}context (contextlevel, instanceid, depth)" \
            " VALUES (%(context_level)s, %(instance_id)s,  %(depth)s)" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'context_level': context_level, 'instance_id': instance_id, 'depth': depth})

    def insert_moodle_course(self, id_category: int, full_name: str, id_number: str, short_name: str, summary: str,
     format_: str, visible: int, start_date: int, time_created: int, time_modified: int):
        """
        Fonction permettant d'insérer un cours.

        :param id_category: L'id de la catégorie dans laquelle va être créée le cours
        :param full_name: Le nom du cours
        :param id_number: L'id_number du cours
        :param short_name: Le nom court du cours
        :param summary: Le sommaire du cours
        :param format_: Le format du cours
        :param visible: Si le cours est visible ou non
        :param start_date: La date de démarrge du cours
        :param time_created: La date de création du cours
        :param time_modified: La date de dernière modification du cours
        """
        s = "INSERT INTO {entete}course " \
            "(category, fullname, idnumber, shortname, summary, " \
            "format, visible, startdate, timecreated, timemodified) " \
            " VALUES (%(id_category)s, %(full_name)s, %(id_number)s, %(short_name)s, %(summary)s, " \
            "%(format)s, %(visible)s, %(start_date)s, %(time_created)s, %(time_modified)s)" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'id_category': id_category,
                                     'full_name': full_name,
                                     'id_number': id_number,
                                     'short_name': short_name,
                                     'summary': summary,
                                     'format': format_,
                                     'visible': visible,
                                     'start_date': start_date,
                                     'time_created': time_created,
                                     'time_modified': time_modified})

    def insert_moodle_course_category(self, name: str, id_number: str, description: str, theme: str):
        """
        Fonction permettant d'insérer une categorie.

        :param name: Le nom de la catégorie de cours
        :param id_number: L'id_number de la catégorie
        :param description: La description de la categorie
        :param theme: Le thème de la categorie
        """
        s = "INSERT INTO {entete}course_categories" \
            " (name, idnumber, description, parent, sortorder, coursecount, visible, depth,theme)" \
            " VALUES(%(name)s, %(id_number)s, %(description)s, 0, 999,0, 1, 1, %(theme)s)" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'name': name, 'id_number': id_number, 'description': description, 'theme': theme})

    def insert_moodle_course_module(self, course: int, module: int, instance: int, added):
        """
        Fonction permettant d'insérer un module de cours.

        :param course: L'id du cours dans lequel on créé ce module
        :param module: L'id du module
        :param instance: L'id de l'instance
        :param added:
        """
        s = "INSERT INTO {entete}course_modules (course, module, instance, added)" \
            " VALUES (%(course)s , %(module)s, %(instance)s , %(added)s)" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'course': course, 'module': module, 'instance': instance, 'added': added})

    def insert_moodle_enrol_capability(self, enrol: str, status: int,
     course_id: int, role_id: int):
        """
        Fonction permettant d'insérer une methode d'inscription à un cours.

        :param enrol: Le nom de la méthode d'enrolment
        :param status: Si la méthode est active ou non
        :param course_id: L'id cours concerné
        :param role_id: L'id du rôle qu'on va donner dans le cours avec cette méthode
        """
        s = "INSERT INTO {entete}enrol(enrol, status, courseid, roleid)" \
            " VALUES(%(enrol)s, %(status)s, %(course_id)s, %(role_id)s)" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'enrol': enrol, 'status': status, 'course_id': course_id, 'role_id': role_id})

    def insert_moodle_forum(self, course: int, name: str, intro: str, intro_format: int, max_bytes: int,
     max_attachements: int, time_modified: int):
        """
        Fonction permettant d'insérer un forum.

        :param course: L'id du cours associé
        :param name: Le nom du forum
        :param intro: L'intro du forum
        :param intro_format: L'intro_format du forum
        :param max_bytes: Le nombre d'octets max du forum
        :param max_attachements: Le nombre d'attachements max du forum
        :param time_modified: La date de dernière modification du forum
        """
        s = "INSERT INTO {entete}forum (course, name, intro, introformat, maxbytes, maxattachments, timemodified) " \
            "VALUES (%(course)s, %(name)s, %(intro)s, %(intro_format)s, %(max_bytes)s, %(max_attachements)s, " \
            "%(time_modified)s)" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'course': course,
                                     'name': name,
                                     'intro': intro,
                                     'intro_format': intro_format,
                                     'max_bytes': max_bytes,
                                     'max_attachements': max_attachements,
                                     'time_modified': time_modified})

    def is_moodle_local_admin(self, id_context_categorie: int, id_user: int) -> bool:
        """
        Fonction permettant de vérifier si un utilisateur est
        admin local pour un contexte donné.

        :param id_context_categorie: L'id de la catégorie de contexte
        :param id_user: L'id de l'utilisateur
        :return: True si c'est un admin local, False sinon
        """
        id_role_admin_local = self.get_id_role_admin_local()
        sql = "SELECT COUNT(id) FROM {entete}role_assignments" \
              " WHERE roleid = %(id_role_admin_local)s" \
              " AND contextid = %(id_context_categorie)s" \
              " AND userid = %(id_user)s" \
            .format(entete=self.entete)
        params = {'id_role_admin_local': id_role_admin_local, 'id_context_categorie': id_context_categorie,
                  'id_user': id_user}
        self.mark.execute(sql, params=params)
        result = self.safe_fetchone()
        is_local_admin = result[0] > 0
        return is_local_admin

    def insert_moodle_local_admin(self, id_context_categorie: int, id_user: int) -> bool:
        """
        Fonction permettant d'insérer un admin local pour un contexte donné.

        :param id_context_categorie: L'id du contexte
        :param id_user: L'id de l'utilisateur
        :return: True si insertion réalisée, False le cas échéant
        """
        if self.is_moodle_local_admin(id_context_categorie, id_user):
            return False
        id_role_admin_local = self.get_id_role_admin_local()
        s = "INSERT ignore INTO {entete}role_assignments(roleid, contextid, userid)" \
            " VALUES (%(id_role_admin_local)s, %(id_context_categorie)s, %(id_user)s)" \
            .format(entete=self.entete)
        params = {'id_role_admin_local': id_role_admin_local, 'id_context_categorie': id_context_categorie,
                  'id_user': id_user}
        self.mark.execute(s, params=params)
        return True

    def insert_moodle_user(self, username: str, first_name: str, last_name: str,
     email: str, mail_display: int, theme: str):
        """
        Fonction permettant d'insérer un utilisateur dans Moodle.

        :param id_user: L'id de l'utilisateur
        :param first_name: Le prénom de l'utilisateur
        :param last_name: Le nom de l'utilisateur
        :param email: L'email de l'utilisateur
        :param mail_display: Le mail_display de l'utilisateur
        :param theme: Le theme (code établissement) de l'utilisateur
        """
        user_id = self.get_user_id(username)
        username = username.lower()
        if user_id is None:
            s = "INSERT INTO {entete}user" \
                " (auth, confirmed, username, firstname, lastname, email, maildisplay, city, country, lang," \
                " mnethostid, theme )" \
                " VALUES (%(auth)s, %(confirmed)s, %(username)s, %(firstname)s, %(lastname)s, %(email)s," \
                " %(maildisplay)s, %(city)s, %(country)s, %(lang)s, %(mnethostid)s, %(theme)s)" \
                .format(entete=self.entete)

            self.mark.execute(s, params={'auth': USER_AUTH,
                                         'confirmed': 1,
                                         'username': username,
                                         'firstname': first_name,
                                         'lastname': last_name,
                                         'email': email,
                                         'maildisplay': mail_display,
                                         'city': USER_CITY,
                                         'country': USER_COUNTRY,
                                         'lang': USER_LANG,
                                         'mnethostid': USER_MNET_HOST_ID,
                                         'theme': theme})

    def insert_moodle_user_info_data(self, id_user: int, id_field: int, data: str):
        """
        Fonction permettant d'insérer un user info data.

        :param id_user: L'id de l'utilisateur
        :param id_field: L'id du user info field
        :param data: La data à insérer
        """
        s = "INSERT INTO {entete}user_info_data (userid, fieldid, data)" \
            " VALUES (%(id_user)s, %(id_field)s, %(data)s)" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'id_user': id_user, 'id_field': id_field, 'data': data})

    def insert_moodle_user_info_field(self, short_name: str, name: str, data_type: str,
     id_category: int, param1, param2, locked: int, visible: int):
        """
        Fonction permettant d'insérer un user info field.

        :param short_name: Le shortname du user info field
        :param name: Le shortname du user info field
        :param data_type: Le data type du user info field
        :param id_category: L'id de catégorie du user info field
        :param param1:
        :param param2:
        :param locked: Si le user info field est locked
        :param visible: Si le user info field est visible
        """
        s = "INSERT INTO {entete}user_info_field" \
            " (shortname, name, datatype, categoryid, param1, param2, locked, visible)" \
            " VALUES (%(short_name)s, %(name)s, %(data_type)s, %(id_category)s, %(param1)s, %(param2)s, %(locked)s," \
            " %(visible)s)" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'short_name': short_name,
                                     'name': name,
                                     'data_type': data_type,
                                     'id_category': id_category,
                                     'param1': param1,
                                     'param2': param2,
                                     'locked': locked,
                                     'visible': visible})

    def insert_zone_privee(self, id_categorie_etablissement: int, siren: str, ou: str, time: int) -> int:
        """
        Fonction permettant d'insérer le cours correspondant à la zone privée.

        :param id_categorie_etablissement: L'id de la catégorie de cours correspondant à l'établissement
        :param siren: Le siren de l'établissement
        :param ou: L'ou de l'établissement
        :param time: La date d'insertion de la zone privée
        :return: L'id de la zone privée créée
        """
        full_name = COURSE_FULLNAME_ZONE_PRIVEE
        id_number = short_name = COURSE_SHORTNAME_ZONE_PRIVEE % siren
        summary = COURSE_SUMMARY_ZONE_PRIVEE % ou.encode("utf-8")
        format_ = COURSE_FORMAT_ZONE_PRIVEE
        visible = COURSE_VISIBLE_ZONE_PRIVEE
        start_date = time_created = time_modified = time
        id_zone_privee = self.get_id_course_by_id_number(id_number)
        if id_zone_privee is not None:
            return id_zone_privee
        self.insert_moodle_course(id_categorie_etablissement, full_name, id_number, short_name, summary, format_,
                                  visible, start_date, time_created, time_modified)
        id_zone_privee = self.get_id_course_by_id_number(id_number)
        return id_zone_privee

    def insert_zone_privee_context(self, id_zone_privee: int) -> int:
        """
        Fonction permettant d'insérer le contexte correspond à la zone privée.

        :param id_zone_privee: L'id de la zone privée
        :return: L'id du contexte inséré
        """
        id_contexte_zone_privee = self.get_id_context(self.constantes.niveau_ctx_cours, PROFONDEUR_CTX_ZONE_PRIVEE,
                                                      id_zone_privee)
        if id_contexte_zone_privee:
            return id_contexte_zone_privee

        id_contexte_zone_privee = self.get_id_context_no_depth(self.constantes.niveau_ctx_cours, id_zone_privee)
        if id_contexte_zone_privee:
            return id_contexte_zone_privee

        self.insert_moodle_context(self.constantes.niveau_ctx_cours, PROFONDEUR_CTX_ZONE_PRIVEE, id_zone_privee)
        id_contexte_zone_privee = self.get_id_context(self.constantes.niveau_ctx_cours, PROFONDEUR_CTX_ZONE_PRIVEE,
                                                      id_zone_privee)
        return id_contexte_zone_privee

    def purge_cohorts(self, users_ids_by_cohorts_ids: dict[int,list[int]]):
        """
        Fonction permettant de purger des cohortes. Le dictionnaire fourni en paramètres
        indique la liste des ids utilisateurs appartenant à une cohorte.
        Ce dictionnaire est indéxé par id de cohortes.

        :param users_ids_by_cohorts_ids: Le dictionnaire associant les ids de cohortes aux utilisateurs
        """
        for cohort_id, users_ids in users_ids_by_cohorts_ids.items():
            ids_list, ids_list_params = array_to_safe_sql_list(users_ids, 'ids_list')
            s = "DELETE FROM {entete}cohort_members" \
                " WHERE cohortid = %(cohort_id)s" \
                " AND userid NOT IN ({ids_list})" \
                .format(entete=self.entete, ids_list=ids_list)
            self.mark.execute(s, params={'cohort_id': cohort_id, **ids_list_params})

    def get_user_filtered_cohorts(self, contextid: int, cohortname_pattern: str) -> list[Cohort]:
        """
        Obtient les cohortes de classes d'élèves.

        :param contextid: L'id du contexte dans lequel on recherche les cohortes
        :param cohortname_pattern: Le pattern à faire correspondre pour le nom de la cohorte
        :return: La liste des cohortes correspondantes
        """
        self.mark.execute("SELECT id, contextid, name FROM {entete}cohort"
                          " WHERE contextid = %(contextid)s AND name LIKE %(like)s"
                          .format(entete=self.entete),
                          params={
                              'contextid': contextid,
                              'like': cohortname_pattern
                          })
        return [Cohort(cohortid=result[0], contextid=result[1], name=result[2]) for result in self.mark.fetchall()]

    def get_cohort_members(self, cohortid: int) -> list:
        """
        Obtient les noms d'utilisateurs membres de la cohorte.

        :param cohortid: L'id de la cohorte
        :return: list de username
        """
        self.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members"
                          " INNER JOIN {entete}user ON {entete}cohort_members.userid = {entete}user.id"
                          " WHERE cohortid = %(cohortid)s"
                          .format(entete=self.entete),
                          params={
                              'cohortid': cohortid
                          })
        return map(lambda r: r[0], self.mark.fetchall())

    def get_cohort_members_list(self, cohortid: int) -> list[str]:
        """
        Obtient les noms d'utilisateurs membres de la cohorte sous forme d'une liste.

        :param cohortid: L'id de la cohorte
        :return: La liste des usernames
        """
        self.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members"
                          " INNER JOIN {entete}user ON {entete}cohort_members.userid = {entete}user.id"
                          " WHERE cohortid = %(cohortid)s"
                          .format(entete=self.entete),
                          params={
                              'cohortid': cohortid
                          })
        members_list = []
        for result in self.mark.fetchall():
            members_list.append(result[0])
        return members_list


    def update_context_path(self, id_context: int, new_path: str):
        """
        Fonction permettant de mettre a jour le path d'un contexte.

        :param id_context: L'id du contexte
        :param new_path: Le nouveau path
        :return:
        """
        s = "UPDATE {entete}context" \
            " SET path = %(new_path)s" \
            " WHERE id = %(id_context)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'new_path': new_path, 'id_context': id_context})

    def update_course_category_description(self, id_category: int, new_description: str):
        """
        Fonction permettant de mettre a jour la description d'une categorie.

        :param id_category: L'id de la catégorie
        :param new_description: La nouvelle description
        """
        s = "UPDATE {entete}course_categories" \
            " SET description = %(new_description)s" \
            " WHERE id = %(id_category)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'new_description': new_description, 'id_category': id_category})

    def update_course_category_name(self, id_category: int, new_name: str):
        """
        Fonction permettant de mettre a jour le nom d'une categorie.

        :param id_category: L'id de la catégorie
        :param new_name: Le nouveau nom
        """
        s = "UPDATE {entete}course_categories" \
            " SET name = %(new_name)s" \
            " WHERE id = %(id_category)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'new_name': new_name, 'id_category': id_category})

    def update_course_category_path(self, id_category: int, new_path: str):
        """
        Fonction permettant de mettre a jour le path d'une catégorie.

        :param id_category: L'id de la catégorie
        :param new_path: Le nouveau path
        """
        s = "UPDATE {entete}course_categories" \
            " SET path = %(new_path)s" \
            " WHERE id = %(id_category)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'new_path': new_path, 'id_category': id_category})

    def update_moodle_user(self, id_user: int, first_name: str, last_name: str,
     email: str, mail_display: int, theme: str):
        """
        Fonction permettant de mettre à jour un utilisateur.

        :param id_user: L'id de l'utilisateur
        :param first_name: Le prénom de l'utilisateur
        :param last_name: Le nom de l'utilisateur
        :param email: L'email de l'utilisateur
        :param mail_display: Le mail_display de l'utilisateur
        :param theme: Le theme (code établissement) de l'utilisateur
        """
        s = "UPDATE {entete}user" \
            " SET auth = %(USER_AUTH)s, firstname = %(first_name)s, lastname = %(last_name)s, email = %(email)s," \
            " maildisplay = %(mail_display)s, city = %(USER_CITY)s, country = %(USER_COUNTRY)s, lang = %(USER_LANG)s," \
            " mnethostid = %(USER_MNET_HOST_ID)s, theme = %(theme)s" \
            " WHERE id = %(id_user)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'USER_AUTH': USER_AUTH,
                                     'first_name': first_name,
                                     'last_name': last_name,
                                     'email': email,
                                     'mail_display': mail_display,
                                     'USER_CITY': USER_CITY,
                                     'USER_COUNTRY': USER_COUNTRY,
                                     'USER_LANG': USER_LANG,
                                     'USER_MNET_HOST_ID': USER_MNET_HOST_ID,
                                     'theme': theme,
                                     'id_user': id_user})

    def update_user_info_data(self, id_user: int, id_field: int, new_data: str):
        """
        Fonction permettant de mettre a jour le data d'un user info data.

        :param id_user: L'id de l'utilisateur
        :param id_field: L'id du field
        :param new_data: La data à écrire dans ce field
        """
        s = "UPDATE {entete}user_info_data" \
            " SET data = %(new_data)s " \
            " WHERE userid = %(id_user)s" \
            " AND fieldid = %(id_field)s" \
            .format(entete=self.entete)
        self.mark.execute(s, params={'new_data': new_data, 'id_user': id_user, 'id_field': id_field})

    def get_field_domaine(self) -> int:
        """
        Fonction pour récupére l'id du champ Domaine.

        :return: L'id du champ Domaine
        """
        id_field_domaine = []
        sql = "SELECT id" \
              " FROM {entete}user_info_field" \
              " WHERE shortname = 'Domaine'" \
              " AND name ='Domaine'" \
            .format(entete=self.entete)
        self.mark.execute(sql)
        row = self.mark.fetchall()

        # Si le champ n'existe pas, on le crée et on récupère l'id
        if not bool(row):
            id_field_domaine = 0
        else:
            id_field_domaine = row[0][0]

        return id_field_domaine

    def is_enseignant_avance(self, id_user: int, id_role_enseignant_avance: int) -> bool:
        """
        Indique si un utilisateur à le rôle enseignant avancé.

        :param id_user: L'id de l'utilisateur
        :param id_role_enseignant_avance: L'id du role enseignant avancé
        :return: Vrai ou faux en fonction de si il a le role ou non
        """
        sql = "SELECT COUNT(id)" \
              " FROM {entete}role_assignments" \
              " WHERE userid = %(id_user)s" \
              " AND roleid = %(id_role_enseignant_avance)s" \
            .format(entete=self.entete)
        self.mark.execute(sql, params={'id_user': id_user, 'id_role_enseignant_avance': id_role_enseignant_avance})
        result = self.safe_fetchone()
        return result[0] > 0

    def set_user_domain(self, id_user: int, id_field_domaine: int, user_domain):
        """
        Fonction pour saisir le Domaine d'un utilisateur Moodle.

        :param id_user: L'id de l'utilisateur
        :param id_field_domaine: L'id du champ domaine
        :param user_domain: Le nom du domaine à insérer
        """
        # pour un utilisateur qui est déjà dans la table "user_info_data" mais sur un autre domaine que
        # le domaine "user_domain",
        # le script va essayer de créer une nouvelle ligne (INSERT) avec le nouveau domaine => erreur !
        # la requête doit donc être modifiée :
        # sql = "SELECT id FROM %suser_info_data WHERE userid = %s AND fieldid = %s AND data = '%s'"
        sql = "SELECT id" \
              " FROM {entete}user_info_data" \
              " WHERE userid = %(id_user)s" \
              " AND fieldid = %(id_field_domaine)s" \
              " LIMIT 1" \
            .format(entete=self.entete)
        self.mark.execute(sql, params={'id_user': id_user, 'id_field_domaine': id_field_domaine})

        result = self.safe_fetchone()
        if result:
            sql = "REPLACE INTO {entete}user_info_data " \
                  "(id, userid, fieldid, data)" \
                  " VALUES (%(id)s, %(id_user)s, %(id_field_domaine)s, %(user_domain)s)" \
                .format(entete=self.entete)
            self.mark.execute(sql, params={'id': result[0],
                                           'id_user': id_user,
                                           'id_field_domaine': id_field_domaine,
                                           'user_domain': user_domain})
        else:
            sql = "INSERT INTO {entete}user_info_data " \
                  "(userid, fieldid, data)" \
                  " VALUES (%(id_user)s, %(id_field_domaine)s, %(user_domain)s)" \
                .format(entete=self.entete)
            self.mark.execute(sql, params={'id_user': id_user,
                                           'id_field_domaine': id_field_domaine,
                                           'user_domain': user_domain})
