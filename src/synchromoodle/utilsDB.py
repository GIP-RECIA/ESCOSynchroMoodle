# coding: utf-8

###############################################################################
# IMPORTS
###############################################################################
import logging
import sys
from typing import Tuple

import mysql.connector
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from .config import DatabaseConfig
from .ldaputils import Ldap

###############################################################################
# CONSTANTS
###############################################################################

#######################################
# COHORTS
#######################################
# Nom et description des cohortes crees pour les classes
COHORT_NAME_FOR_CLASS = 'Élèves de la Classe %s'
COHORT_DESC_FOR_CLASS = 'Élèves de la classe %s'
COHORT_ID_NUMBER_FOR_CLASS = "Classe %s"

# Nom et description des cohortes crees pour les niveaux de formation
COHORT_NAME_FOR_FORMATION = 'Élèves du Niveau de formation %s'
COHORT_DESC_FOR_FORMATION = 'Eleves avec le niveau de formation %s'

# Nom et description des cohortes crees pour les profs des etablissements
P_COHORT_NAME_FOR_ETAB = 'Profs de l\'établissement (%s)'
P_COHORT_DESC_FOR_ETAB = 'Enseignants de l\'établissement %s'
#######################################
# BLOCKS
#######################################
# Default region pour le bloc de recherche sur le forum de la zone privee
BLOCK_FORUM_SEARCH_DEFAULT_REGION = "side-pre"

# Default weight pour le bloc de recherche sur le forum de la zone privee
BLOCK_FORUM_SEARCH_DEFAULT_WEIGHT = 2

# Nom pour le bloc de recherche sur le forum de la zone privee
BLOCK_FORUM_SEARCH_NAME = "searches_forums"

# Page type pattern pour le bloc de recherche sur le forum de la zone privee
BLOCK_FORUM_SEARCH_PAGE_TYPE_PATTERN = "course-view-*"

# Show in sub context option pour le bloc de recherche sur le forum de la zone privee
BLOCK_FORUM_SEARCH_SHOW_IN_SUB_CTX = 0

# Sub page pattern pour le bloc de recherche sur le forum de la zone privee
BLOCK_FORUM_SEARCH_SUB_PAGE_PATTERN = ""

#######################################
# CONTEXTES
#######################################
# Id du contexte systeme
ID_CONTEXT_SYSTEM = 1

# Id de l'instance concernant Moodle
ID_INSTANCE_INTER_ETABS = 1

# Niveau de contexte pour une categorie
NIVEAU_CTX_CATEGORIE = 40

# Niveau de contexte pour un cours
NIVEAU_CTX_COURS = 50

# Niveau de contexte pour un forum
NIVEAU_CTX_FORUM = 70

# Niveau de contexte pour un bloc
NIVEAU_CTX_BLOC = 80

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
# Statut pour ouvrir l'inscription manuelle a un cours
COURSE_ENROL_MANUAL = "manual"
COURSE_ENROL_ENROL = 0

# Format pour la zone privee d'un etablissement
COURSE_FORMAT_ZONE_PRIVEE = "topics"

# Fullname pour la zone privee d'un etablissement
COURSE_FULLNAME_ZONE_PRIVEE = "Zone privée"

# Num. sections pour la zone privee d'un etablissement
COURSE_NUM_SECTIONS_ZONE_PRIVEE = 7

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
# FORUM
#######################################
# Nom du forum pour la zone privee 
# Le (%s) est reserve a l'organisation unit de l'etablissement
FORUM_NAME_ZONE_PRIVEE = "Forum réservé au personnel éducatif de l'établissement %s"

# Format d'intro. pour le forum de la zone privee
FORUM_INTRO_FORMAT_ZONE_PRIVEE = 1

# Introduction pour le forum de la zone privee
FORUM_INTRO_ZONE_PRIVEE = "<p></p>"

# Max attachements pour le forum de la zone privee
FORUM_MAX_ATTACHEMENTS_ZONE_PRIVEE = 2

# Max bytes pour le forum de la zone privee
FORUM_MAX_BYTES_ZONE_PRIVEE = 512000

#######################################
# ROLES
#######################################
# Enrol method => manual enrolment
ENROL_METHOD_MANUAL = "manual"

# Id pour le role administrateur
ID_ROLE_ADMIN = 1

# Id pour le role enseignant
ID_ROLE_ENSEIGNANT = 3

# Id pour le role eleve
ID_ROLE_ELEVE = 5

# Id pour le role inspecteur
ID_ROLE_INSPECTEUR = 9

# Id pour le role utilisateur Mahara
ID_ROLE_MAHARA = 16

# Shortname du role admin local
SHORTNAME_ADMIN_LOCAL = "adminlocal"

# Shortname du role extended teacher
SHORTNAME_EXTENDED_TEACHER = "extendedteacher"

# Shortname du role advanced teacher
SHORTNAME_ADVANCED_TEACHER = "advancedteacher"
#######################################
# USER INFO FIELD
#######################################
# Category id du user info field utilise pour la classe
USER_INFO_FIELD_CATEGORY_ID_CLASSE = 1

# Data type du user info field utilise pour la classe
USER_INFO_FIELD_DATATYPE_CLASSE = "text"

# Locked option du user info field utilise pour la classe
USER_INFO_FIELD_LOCKED_CLASSE = 1

# Name du user info field utilise pour la classe
USER_INFO_FIELD_NAME_CLASSE = "Classe"

# Param1 du user info field utilise pour la classe
USER_INFO_FIELD_PARAM1_CLASSE = 30

# Param2 du user info field utilise pour la classe
USER_INFO_FIELD_PARAM2_CLASSE = 512

# Shortname du user info field utilise pour la classe
USER_INFO_FIELD_SHORTNAME_CLASSE = "classe"

# Visibile option du user info field utilise pour la classe
USER_INFO_FIELD_VISIBLE_CLASSE = 2

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


###############################################################################
# FONCTIONS
###############################################################################

def array_to_safe_sql_list(elements, name=None):
    if name:
        format_strings = []
        params = {}
        for i, element in enumerate(elements):
            format_strings.append('%({name}_{i})s'.format(name=name, i=i))
            params['{name}_{i}'.format(name=name, i=i)] = element
        return ','.join(format_strings), params
    else:
        format_strings = ['%s'] * len(elements)
        params = tuple(elements)
        return ','.join(format_strings), params


###########################################################
# Fonction permettant d'ajouter un role a un utilisateur
# Mahaea pour un contexte donne 
###########################################################
def add_role_mahara_to_user(mark, entete, id_user):
    add_role_to_user(mark, entete, ID_ROLE_MAHARA, ID_CONTEXT_SYSTEM, id_user)


###########################################################
# Fonction permettant d'ajouter un role a un utilisateur
# pour un contexte donne 
###########################################################
def add_role_to_user(mark, entete, role_id, id_context, id_user):
    id_role_assignment = get_id_role_assignment(mark, entete, role_id, id_context, id_user)
    if not id_role_assignment:
        # Ajout du role dans le contexte
        s = "INSERT INTO {entete}role_assignments( roleid, contextid, userid )" \
            " VALUES ( %(role_id)s, %(id_context)s, %(id_user)s )".format(entete=entete)
        mark.execute(s, params={'role_id': role_id, 'id_context': id_context, 'id_user': id_user})


###########################################################
# Fonction permettant d'ajouter un role a un utilisateur
# pour plusieurs contextes donnes
###########################################################
def add_role_to_user_for_contexts(mark, entete, role_id, ids_contexts_by_courses, id_user):
    for id_course, id_context in ids_contexts_by_courses.iteritems():
        add_role_to_user(mark, entete, role_id, id_context, id_user)
        enroll_user_in_course(mark, entete, role_id, id_course, id_user)


###########################################################
# Fonction permettant d'etablir une connexion a une BD 
# MySQL
###########################################################
def connect_db(config: DatabaseConfig) -> Tuple[MySQLConnection, MySQLCursor]:
    # Etablissement de la connexion
    conn = mysql.connector.connect(host=config.host,
                                   user=config.user,
                                   passwd=config.password,
                                   db=config.database,
                                   charset=config.charset,
                                   port=config.port)

    # conn.set_character_set(db_charset)
    # Choix des options
    mark = conn.cursor()
    # mark.execute('SET NAMES ' + db_charset + ';')
    # mark.execute('SET CHARACTER SET ' + db_charset + ';')
    # mark.execute('SET character_set_connection=' + db_charset + ';')
    return conn, mark


###########################################################
# Fonction permettant de creer des cohortes a partir de
# classes liees a un etablissement.
###########################################################
def create_classes_cohorts(mark, entete, id_context_etab, classes_names, time_created):
    ids_cohorts = []
    for class_name in classes_names:
        cohort_name = COHORT_NAME_FOR_CLASS % (class_name)
        cohort_description = COHORT_DESC_FOR_CLASS % (class_name)
        id_cohort = create_cohort(mark, entete, id_context_etab, cohort_name, cohort_name, cohort_description,
                                  time_created)
        ids_cohorts.append(id_cohort)
    return ids_cohorts


###########################################################
# Fonction permettant de creer des cohortes a partir de
# etablissement.
# Puis de remplir la cohorte avec les enseignants de l'etablissement
###########################################################
def create_profs_etabs_cohorts(mark, entete, id_context_etab, etab_name, time_created, time_stamp,
                               ldap: Ldap):
    liste_professeurs_insere = []
    cohort_name = P_COHORT_NAME_FOR_ETAB % (etab_name)
    cohort_description = P_COHORT_DESC_FOR_ETAB % (etab_name)
    id_cohort = create_cohort(mark, entete, id_context_etab, cohort_name, cohort_name, cohort_description, time_created)

    ldap_teachers = ldap.search_teacher(since_timestamp=time_stamp, uai=etab_name, tous=True)

    maintenant_sql = get_timestamp_now(mark)
    for ldap_teacher in ldap_teachers:
        enseignant_infos = "%s %s %s" % (ldap_teacher.uid, ldap_teacher.given_name, ldap_teacher.sn)
        id_user = get_user_id(mark, entete, ldap_teacher.uid)
        enroll_user_in_cohort(mark, entete, id_cohort, id_user, enseignant_infos, maintenant_sql)
        liste_professeurs_insere.append(id_user)
    if time_stamp is None:
        # Si la purge à été definie ou si pas de trt precedent on purge la cohorte
        purge_cohort_profs(mark, entete, id_cohort, liste_professeurs_insere)


##############################################################
# fonction permettant la purge d'une cohort de profs
#
###############################################################
def purge_cohort_profs(mark, entete, id_cohort, list_profs):
    ids_list, ids_list_params = array_to_safe_sql_list(list_profs, 'ids_list')
    s = "DELETE FROM {entete}cohort_members WHERE cohortid = %(id_cohort)s AND userid NOT IN ( {ids_list} )".format(entete=entete, ids_list=ids_list)
    mark.execute(s, params={'id_cohort': id_cohort, **ids_list_params})


###########################################################
# Fonction permettant de creer une nouvelle cohorte pour
# un contexte donne.
###########################################################
def create_cohort(mark, entete, id_context, name, id_number, description, time_created):
    # Si la cohorte n'existe pas encore
    id_cohort = get_id_cohort(mark, entete, id_context, name)
    if id_cohort is None:
        s = "INSERT INTO {entete}cohort( contextid, name, idnumber, description, descriptionformat, timecreated, timemodified )" \
            " VALUES ( %(id_context)s, %(name)s, %(id_number)s, %(description)s, 0, %(time_created)s, %(time_created)s )".format(entete=entete)
        mark.execute(s, params={'id_context': id_context, 'name': name, 'id_number': id_number, 'description': description, 'time_created': time_created})
        logging.info("      |_ Creation de la cohorte '%s'" % (name))
    return get_id_cohort(mark, entete, id_context, name)


###########################################################
# Fonction permettant de creer une cohorte a partir d'un
# niveau de formation lie a un etablissement.
###########################################################
def create_formation_cohort(mark, entete, id_context_etab, formation_name, time_created):
    cohort_name = COHORT_NAME_FOR_FORMATION % (formation_name)
    cohort_description = COHORT_DESC_FOR_FORMATION % (formation_name)
    id_cohort = create_cohort(mark, entete, id_context_etab, cohort_name, cohort_name, cohort_description, time_created)
    return id_cohort


###########################################################
# Fonction permettant de supprimer tous les roles 
# d'utilisateur de Mahara
###########################################################
def delete_all_mahara_roles(mark, entete):
    s = "DELETE FROM {entete}role_assignments WHERE roleid = %(ID_ROLE_MAHARA)s AND contextid = %(ID_CONTEXT_SYSTEM)s".format(entete=entete)
    mark.execute(s, params={'ID_ROLE_MAHARA': ID_ROLE_MAHARA, 'ID_CONTEXT_SYSTEM': ID_CONTEXT_SYSTEM})


###########################################################
# Fonction permettant de supprimer les admins locaux
# d'un contexte en gardant uniquement les admins specifies.
###########################################################
def delete_moodle_local_admins(mark, entete, id_context_categorie, ids_not_admin):
    if len(ids_not_admin) == 0:
        return
    # Construction de la liste des ids admins a conserver
    ids_list, ids_list_params = array_to_safe_sql_list(ids_not_admin, 'ids_list')
    # Recuperation de l'id pour le role d'admin local
    id_role_admin_local = get_id_role_admin_local(mark, entete)
    # Suppression des admins non presents dans la liste
    s = "DELETE FROM {entete}role_assignments WHERE roleid = %(id_role_admin_local)s AND contextid = %(id_context_categorie)s AND userid IN ( {ids_list} )".format(entete=entete, ids_list=ids_list)
    mark.execute(s, params={'id_role_admin_local': id_role_admin_local, 'id_context_categorie': id_context_categorie, **ids_list_params})


###########################################################
# Fonction permettant de supprimer les admins locaux
# d'un contexte en gardant uniquement les admins specifies.
###########################################################
def delete_moodle_local_admin(mark, entete, id_context_categorie, userid):
    id_role_admin_local = get_id_role_admin_local(mark, entete)
    delete_moodle_assignment(mark, entete, id_context_categorie, userid, id_role_admin_local);


###########################################################
# Fonction permettant de supprimer un role à un utilisateur
# dans un contexte
###########################################################
def delete_moodle_assignment(mark, entete, id_context_category, userid, roleid):
    s = "DELETE FROM {entete}role_assignments WHERE contextid = %(id_context_category)s AND roleid = %(roleid)s AND userid = %(userid)s".format(entete=entete)
    mark.execute(s, params={'id_context_category': id_context_category, 'roleid': roleid, 'userid': userid})
    return mark.rowcount > 0


###########################################################
# Fonction permettant de supprimer un role sur differents
# contextes pour l'utilisateur specifie.
###########################################################
def delete_role_for_contexts(mark, entete, role_id, ids_contexts_by_courses, id_user):
    # Suppression des enrolments dans les cours
    for id_course, id_context in ids_contexts_by_courses.iteritems():
        # Recuperation de la methode d'enrolment
        id_enrol = get_id_enrol(mark, entete, ENROL_METHOD_MANUAL, role_id, id_course)
        if not id_enrol:
            continue
        # Suppression de l'enrolment associe
        id_user_enrolment = get_id_user_enrolment(mark, entete, id_enrol, id_user)
        if id_user_enrolment:
            s = "DELETE FROM {entete}user_enrolments WHERE id = %(id_user_enrolment)s}".format(entete=entete)
            mark.execute(s, params={'id_user_enrolment': id_user_enrolment})

    # Suppression des roles dans les contextes
    ids_list, ids_list_params = array_to_safe_sql_list(ids_contexts_by_courses.values(), 'ids_list')
    s = "DELETE FROM {entete}role_assignments WHERE roleid = %(role_id)s AND contextid IN ( {ids_list} ) AND userid = %(id_user)s".format(entete=entete, ids_list=ids_list)
    mark.execute(s, params={'role_id': role_id, 'id_user': id_user, **ids_list_params})


###########################################################
# Fonction permettant de supprimer des roles.
###########################################################
def delete_roles(mark, entete, ids_roles):
    # Construction de la liste des ids des roles concernes
    ids_list, ids_list_params = array_to_safe_sql_list(ids_roles, 'ids_list')
    s = "DELETE FROM {entete}role_assignments WHERE id IN ( {ids_list} )".format(entete=entete, ids_list=ids_list)
    mark.execute(s, params={**ids_list_params})


###########################################################
# Fonction permettant d'enlever un utilisateur d'une 
# ou plusieurs cohortes.
# Seules les inscriptions dans les cohortes passees en
# parametres sont conservees.
###########################################################
def disenroll_user_from_cohorts(mark, entete, ids_cohorts_to_keep, id_user):
    # Construction de la liste des ids des cohortes concernes
    ids_list, ids_list_params = array_to_safe_sql_list(ids_cohorts_to_keep, 'ids_list')
    s = "DELETE FROM {entete}cohort_members WHERE userid = %(id_user)s and cohortid NOT IN ( {ids_list} )".format(entete=entete, ids_list=ids_list)
    mark.execute(s, params={'id_user': id_user, **ids_list_params})


###########################################################
# Fonction permettant d'enlever un utilisateur d'une 
# cohorte.
###########################################################
def disenroll_user_from_cohort(mark, entete, id_cohort, id_user):
    s = "DELETE FROM {entete}cohort_members WHERE cohortid = %(id_cohort)s and userid = %(id_user)s".format(entete=entete)
    mark.execute(s, params={'id_cohort': id_cohort, 'id_user': id_user})


###########################################################
# Fonction permettant d'enroler un utilisateur dans un 
# cours
###########################################################
def enroll_user_in_course(mark, entete, role_id, id_course, id_user):
    id_enrol = get_id_enrol(mark, entete, ENROL_METHOD_MANUAL, role_id, id_course)
    if not id_enrol:
        # Ajout de la methode d'enrolment dans le cours
        s = "INSERT INTO {entete}enrol( enrol, courseid, roleid )" \
            " VALUES ( %(ENROL_METHOD_MANUAL)s, %(id_course)s, %(role_id)s )".format(entete=entete)
        mark.execute(s, params={'ENROL_METHOD_MANUAL': ENROL_METHOD_MANUAL, 'id_course': id_course, 'role_id': role_id})
        id_enrol = get_id_enrol_max(mark, entete)
    if id_enrol:
        # Enrolement de l'utilisateur dans le cours
        s = "INSERT IGNORE INTO {entete}user_enrolments( enrolid, userid )" \
            " VALUES ( %(id_enrol)s, %(id_user)s )".format(entete=entete)
        mark.execute(s, params={'id_enrol': id_enrol, 'id_user': id_user})


###########################################################
# Fonction permettant d'ajouter un utilisateur a une 
# cohorte.
###########################################################
def enroll_user_in_cohort(mark, entete, id_cohort, id_user, user_infos, time_added):
    s = "INSERT IGNORE INTO {entete}cohort_members( cohortid, userid, timeadded ) VALUES ( %(id_cohort)s, %(id_user)s, %(time_added)s )".format(entete=entete)
    mark.execute(s, params={'id_cohort': id_cohort, 'id_user': id_user, 'time_added': time_added})
    cohort_name = get_cohort_name(mark, entete, id_cohort)
    logging.info("      |_ Inscription de l'utilisateur (id = %s) dans la cohorte '%s'" % (str(id_user), cohort_name))


###########################################################
# Fonction permettant d'ajouter un utilisateur a une ou
# plusieurs cohorte(s) au sein d'un etablissement.
###########################################################
def enroll_user_in_cohorts(mark, entete, id_context_etab, ids_cohorts, id_user, user_infos, time_added):
    for id_cohort in ids_cohorts:
        enroll_user_in_cohort(mark, entete, id_cohort, id_user, user_infos, time_added)


###########################################################
# Fonction permettant de recuperer le nom d'une cohorte.
###########################################################
def get_cohort_name(mark, entete, id_cohort):
    s = "SELECT name FROM {entete}cohort WHERE id = %(id_cohort)s".format(entete=entete)
    mark.execute(s, params={'id_cohort': id_cohort})
    name = mark.fetchone()[0]
    logging.debug("Cohort : Name = %s" % name)
    return name


###########################################################
# Fonction permettant de recuperer la description d'une
# categorie.
###########################################################
def get_description_course_category(mark, entete, id_category):
    s = "SELECT description FROM {entete}course_categories WHERE id = %(id_category)s".format(entete=entete)
    mark.execute(s, params={'id_category': id_category})
    description = mark.fetchone()[0]
    return description


###########################################################
# Fonction permettant de recuperer les descriptions de
# categories.
###########################################################
def get_descriptions_course_categories_by_themes(mark, entete, themes):
    ids_list, ids_list_params = array_to_safe_sql_list(themes, 'ids_list')
    s = "SELECT description" \
        " FROM {entete}course_categories" \
        " WHERE theme IN ( {ids_list} )".format(entete=entete, ids_list=ids_list)
    mark.execute(s, params={**ids_list_params})
    result_set = mark.fetchall()
    if not result_set:
        return []
    descriptions = [result[0] for result in result_set]
    return descriptions


###########################################################
# Fonction permettant de recuperer l'id d'un bloc.
###########################################################
def get_id_block(mark, entete, parent_context_id):
    s = "SELECT id FROM {entete}block_instances WHERE parentcontextid = %(parent_context_id)s".format(entete=entete)
    mark.execute(s, params={'parent_context_id': parent_context_id})
    id_block = mark.fetchone()[0]
    return id_block


###########################################################
# Fonction permettant de recuperer l'id correspondant a la 
# categorie inter-etablissements. 
###########################################################
def get_id_categorie_inter_etabs(mark, entete, categorie_name):
    s = "SELECT id FROM {entete}course_categories WHERE name LIKE %(categorie_name)s".format(entete=entete)
    mark.execute(s, params={'categorie_name': categorie_name})
    ligne = mark.fetchone()
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id d'une cohorte
# par son nom et son contexte de rattachement.
###########################################################
def get_id_cohort(mark, entete, id_context, cohort_name):
    s = "SELECT id FROM {entete}cohort WHERE contextid = %(id_context)s AND name = %(cohort_name)s".format(entete=entete)
    mark.execute(s, params={'id_context': id_context, 'cohort_name': cohort_name})
    ligne = mark.fetchone()
    if ligne == None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id d'un contexte via 
# le niveau et l'id de l'instance associee.
###########################################################
def get_id_context_no_depth(mark, entete, context_level, instance_id):
    s = "SELECT id FROM {entete}context WHERE contextlevel = %(context_level)s and instanceid = %(instance_id)s".format(entete=entete)
    mark.execute(s, params={'context_level': context_level, 'instance_id': instance_id})
    ligne = mark.fetchone()
    if ligne is None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id d'un contexte via 
# le niveau, la profondeur et l'id de l'instance associee.
###########################################################
def get_id_context(mark, entete, context_level, depth, instance_id):
    s = "SELECT id FROM {entete}context WHERE contextlevel = %(context_level)s and depth = %(depth)s and instanceid = %(instance_id)s".format(entete=entete)
    mark.execute(s, params={'context_level': context_level, 'depth': depth, 'instance_id': instance_id})
    ligne = mark.fetchone()
    if ligne is None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id d'une contexte via 
# l'id d'un etablissement.
###########################################################
def get_id_context_categorie(mark, entete, id_etab_categorie):
    return get_id_context(mark, entete, NIVEAU_CTX_CATEGORIE, 2, id_etab_categorie)


###########################################################
# Fonction permettant de recuperer l'id du contexte 
# de la categorie inter-etablissements
###########################################################
def get_id_context_inter_etabs(mark, entete='mdl_'):
    s = "SELECT id FROM {entete}context " \
        "WHERE contextlevel = %(context_level)s AND instanceid = %(instanceid)s".format(entete=entete)
    mark.execute(s, params={'table': entete + 'context', 'context_level': NIVEAU_CTX_CATEGORIE,
                            'instanceid': ID_INSTANCE_INTER_ETABS})
    id_context_moodle = mark.fetchone()[0]
    return id_context_moodle


###########################################################
# Fonction permettant de recuperer l'id d'un cours
# a partir de son idnumber.
###########################################################
def get_id_course_by_id_number(mark, entete, id_number):
    s = "SELECT id FROM {entete}course WHERE idnumber = %(id)s".format(entete=entete)
    mark.execute(s, params={'id': id_number})
    ligne = mark.fetchone()
    if ligne is None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id d'une categorie
# a partir de son idnumber.
###########################################################
def get_id_course_category_by_id_number(mark, entete, id_number):
    s = "SELECT id FROM {entete}course_categories WHERE idnumber LIKE %%%(id)s%%".format(entete=entete)
    mark.execute(s, params={'id': id_number})
    ligne = mark.fetchone()
    if ligne is None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id d'une categorie
# a partir de son theme.
###########################################################
def get_id_course_category_by_theme(mark, entete, theme):
    s = "SELECT id FROM {entete}course_categories WHERE theme = %(theme)s".format(entete=entete)
    mark.execute(s, params={'theme': theme})
    ligne = mark.fetchone()
    if ligne is None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id d'un module de 
# cours.
###########################################################
def get_id_course_module(mark, entete, course):
    s = "SELECT id FROM {entete}course_modules WHERE course = %(course)s".format(entete=entete)
    mark.execute(s, params={'course': course})
    id_course_module = mark.fetchone()[0]
    return id_course_module


###########################################################
# Fonction permettant de recuperer un id
# dans la table permettant les enrolments
###########################################################
def get_id_enrol(mark, entete, enrol_method, role_id, id_course):
    s = "SELECT e.id FROM {entete}enrol e" \
        " WHERE e.enrol = %(enrol_method)s" \
        " AND e.courseid = %(id_course)s" \
        " AND e.roleid = %(role_id)s".format(entete=entete)
    mark.execute(s, params={'enrol_method': enrol_method, 'id_course': id_course, 'role_id': role_id})
    ligne = mark.fetchone()
    if ligne == None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id maximum present
# dans la table permettant les enrolments
###########################################################
def get_id_enrol_max(mark, entete):
    s = "SELECT id FROM {entete}enrol ORDER BY id DESC LIMIT 1".format(entete=entete)
    mark.execute(s)
    ligne = mark.fetchone()
    if ligne == None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id du contexte propre 
# a moodle.
###########################################################
def get_id_forum(mark, entete, course):
    s = "SELECT id FROM {entete}forum WHERE course = %(course)s".format(entete=entete)
    mark.execute(s, params={'course': course})
    id_forum = mark.fetchone()[0]
    return id_forum


###########################################################
# Fonction permettant de recuperer l'id du role admin local
# au sein de la BD moodle.
###########################################################
def get_id_role_admin_local(mark, entete):
    id_admin_local = get_id_role_by_shortname(mark, entete, SHORTNAME_ADMIN_LOCAL)
    if id_admin_local is None:
        logging.error("Le role '%s' n'est pas defini" % (SHORTNAME_ADMIN_LOCAL))
        sys.exit(2)
    return id_admin_local


###########################################################
# Fonction permettant de recuperer l'id d'un role 
# assignement au sein de la BD moodle.
###########################################################
def get_id_role_assignment(mark, entete, role_id, id_context, id_user):
    s = "SELECT id FROM {entete}role_assignments" \
        " WHERE roleid = %(role_id)s AND contextid = %(id_context)s AND userid = %(id_user)s".format(entete=entete)
    mark.execute(s, params={'role_id': role_id, 'id_context': id_context, 'id_user': id_user})
    ligne = mark.fetchone()
    if ligne is None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id du role extended
# teacher.
###########################################################
def get_id_role_extended_teacher(mark, entete):
    id_extended_teacher = get_id_role_by_shortname(mark, entete, SHORTNAME_EXTENDED_TEACHER)
    if id_extended_teacher is None:
        logging.error("Le role '%s' n'est pas defini" % (SHORTNAME_EXTENDED_TEACHER))
        sys.exit(2)
    return id_extended_teacher


###########################################################
# Fonction permettant de recuperer l'id du role advanced
# teacher.
###########################################################
def get_id_role_advanced_teacher(mark, entete):
    id_advanced_teacher = get_id_role_by_shortname(mark, entete, SHORTNAME_ADVANCED_TEACHER)
    if id_advanced_teacher is None:
        logging.error("Le role '%s' n'est pas defini" % (SHORTNAME_ADVANCED_TEACHER))
        sys.exit(2)
    return id_advanced_teacher


###########################################################
# Fonction permettant de recuperer l'id d'un role via son
# shortname
###########################################################
def get_id_role_by_shortname(mark, entete, short_name):
    s = "SELECT id FROM {entete}role WHERE shortname = %(short_name)s".format(entete=entete)
    mark.execute(s, params={'short_name': short_name})
    ligne = mark.fetchone()
    if ligne == None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id d'un user enrolment
###########################################################
def get_id_user_enrolment(mark, entete, id_enrol, id_user):
    s = "SELECT id" \
        " FROM {entete}user_enrolments " \
        " WHERE userid = %(id_user)s AND enrolid = %(id_enrol)s".format(entete=entete)
    mark.execute(s, params={'id_user': id_user, 'id_enrol': id_enrol})
    ligne = mark.fetchone()
    if ligne is None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id d'un info data via
# l'id-user et l'id_field
###########################################################
def get_id_user_info_data(mark, entete, id_user, id_field):
    s = "SELECT id" \
        " FROM {entete}user_info_data " \
        " WHERE userid = %(id_user)s AND fieldid = %(id_field)s".format(entete=entete)
    mark.execute(s, params={'id_user': id_user, 'id_field': id_field})
    ligne = mark.fetchone()
    if ligne is None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer l'id d'un info field via 
# son shortname.
###########################################################
def get_id_user_info_field_by_shortname(mark, entete, short_name):
    s = "SELECT id" \
        " FROM {entete}user_info_field" \
        " WHERE shortname = %(short_name)s".format(entete=entete)
    mark.execute(s, params={'short_name': short_name})
    ligne = mark.fetchone()
    if ligne is None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer un info field via son
# shortname.
###########################################################
def get_id_user_info_field_classe(mark, entete):
    return get_id_user_info_field_by_shortname(mark, entete, USER_INFO_FIELD_SHORTNAME_CLASSE)


###########################################################
# Fonction permettant de recuperer les ids des roles non
# autorises sur les forums, ainsi que les non des forums
# sur lesquels portent ces roles.
###########################################################
def get_ids_and_summaries_not_allowed_roles(mark, entete, id_user, allowed_forums_shortnames):
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
        .format(entete=entete, ids_list=ids_list)
    mark.execute(s, params={'id_user': id_user, **ids_list_params})
    result_set = mark.fetchall()
    if not result_set:
        return [], []
    # Recuperation des ids et themes non autorises
    ids = [result[0] for result in result_set]
    summaries = [result[1] for result in result_set]
    return ids, summaries


###########################################################
# Fonction permettant de recuperer les ids des roles qui
# ne sont pas autorises pour l'utilisateur.
###########################################################
def get_ids_and_themes_not_allowed_roles(mark, entete, id_user, allowed_themes):
    # Construction de la liste des themes
    ids_list, ids_list_params = array_to_safe_sql_list(allowed_themes, 'ids_list')
    # Recuperation des roles sur les etablissements qui ne devraient plus exister 
    # (quand le prof n'est plus rattache aux etablissements) 
    s = "SELECT mra.id, mcc.theme" \
        " FROM {entete}course_categories mcc, {entete}context mc, {entete}role_assignments mra" \
        " WHERE mcc.theme NOT IN ({ids_list}) AND mcc.theme IS NOT NULL" \
        " AND mcc.id = mc.instanceid " \
        " AND mc.contextlevel = %(NIVEAU_CTX_CATEGORIE)s AND mc.depth = %(PROFONDEUR_CTX_ETAB)s" \
        " AND mc.id = mra.contextid" \
        " AND mra.userid = %(id_user)s".format(entete=entete, ids_list=ids_list)
    mark.execute(s, params={**ids_list_params, 'NIVEAU_CTX_CATEGORIE': NIVEAU_CTX_CATEGORIE, 'PROFONDEUR_CTX_ETAB': PROFONDEUR_CTX_ETAB, 'id_user': id_user})
    result_set = mark.fetchall()
    if not result_set:
        return [], []
    # Recuperation des ids et themes non autorises
    ids = [result[0] for result in result_set]
    themes = [result[1] for result in result_set]
    return ids, themes


###########################################################
# Fonction permettant de recuperer le timestamp actuel.
###########################################################
def get_timestamp_now(mark):
    s = "SELECT UNIX_TIMESTAMP( now( ) ) - 3600*2"
    mark.execute(s)
    now = mark.fetchone()[0]
    return now


###########################################################
# Fonction permettant de recuperer l'id d'un 
# utilisateur moodle via son username.
###########################################################
def get_user_id(mark, entete, username):
    s = "SELECT id FROM {entete}user " \
        "WHERE username = %(username)s".format(entete=entete)
    mark.execute(s, params={'username': username.lower()})
    ligne = mark.fetchone()
    if ligne is None:
        return None
    return ligne[0]


###########################################################
# Fonction permettant de recuperer les ids des
# utilisateurs moodle via leurs usernames.
###########################################################
def get_users_ids(mark, entete, usernames):
    users_ids = []
    for username in usernames:
        user_id = get_user_id(mark, entete, username)
        users_ids.append(user_id)
    return users_ids


###########################################################
# Fonction permettant d'inserer un bloc.
###########################################################
def insert_moodle_block(mark, entete, block_name, parent_context_id, show_in_subcontexts, page_type_pattern,
                        sub_page_pattern, default_region, default_weight):
    s = "INSERT INTO {entete}block_instances ( blockname, parentcontextid, showinsubcontexts, pagetypepattern, subpagepattern, defaultregion, defaultweight ) " \
        " VALUES ( %(block_name)s, %(parent_context_id)s, %(show_in_subcontexts)s, %(page_type_pattern)s, %(sub_page_pattern)s, %(default_region)s, %(default_weight)s )".format(entete=entete)
    mark.execute(s, params={'block_name': block_name,
                            'parent_context_id': parent_context_id,
                            'show_in_subcontexts': show_in_subcontexts,
                            'page_type_pattern': page_type_pattern,
                            'sub_page_pattern': sub_page_pattern,
                            'default_region': default_region,
                            'default_weight': default_weight})


###########################################################
# Fonction permettant d'inserer un contexte.
###########################################################
def insert_moodle_context(mark, entete, context_level, depth, instance_id):
    s = "INSERT INTO {entete}context ( contextlevel, instanceid, depth )" \
        " VALUES ( %(context_level)s, %(instance_id)s,  %(depth)s )".format(entete=entete)
    mark.execute(s, params={'context_level': context_level, 'instance_id': instance_id, 'depth': depth})


###########################################################
# Fonction permettant d'inserer un cours.
###########################################################
def insert_moodle_course(mark, entete, id_category, full_name, id_number, short_name, summary, format, visible,
                         num_sections, start_date, time_created, time_modified):
    s = "INSERT INTO {entete}course ( category, fullname, idnumber, shortname, summary, format, visible, startdate, timecreated, timemodified ) " \
        " VALUES ( %(id_category)s, %(full_name)s, %(id_number)s, %(short_name)s, %(summary)s, %(format)s, %(visible)s, %(start_date)s, %(time_created)s, %(time_modified)s )".format(entete=entete)
    mark.execute(s, params={'id_category': id_category,
                            'full_name': full_name,
                            'id_number': id_number,
                            'short_name': short_name,
                            'summary': summary,
                            'format': format,
                            'visible': visible,
                            'start_date': start_date,
                            'time_created': time_created,
                            'time_modified': time_modified})


###########################################################
# Fonction permettant d'inserer une categorie.
###########################################################
def insert_moodle_course_category(mark, entete, name, id_number, description, theme):
    s = "INSERT INTO {entete}course_categories ( name, idnumber, description, parent, sortorder, coursecount, visible, depth,theme )" \
        " VALUES( %(name)s, %(id_number)s, %(description)s, 0, 999,0, 1, 1, %(theme)s )".format(entete=entete)
    mark.execute(s, params={'name': name, 'id_number': id_number, 'description': description, 'theme': theme})


###########################################################
# Fonction permettant d'inserer un module de cours.
###########################################################
def insert_moodle_course_module(mark, entete, course, module, instance, added):
    s = "INSERT INTO {entete}course_modules ( course, module, instance, added )" \
        " VALUES ( %(course)s , %(module)s, %(instance)s , %(added)s )".format(entete=entete)
    mark.execute(s, params={'course': course, 'module': module, 'instance': instance, 'added': added})


###########################################################
# Fonction permettant d'inserer une methode d'inscription
# a un cours.
###########################################################
def insert_moodle_enrol_capability(mark, entete, enrol, status, course_id, role_id):
    s = "INSERT INTO {entete}enrol( enrol, status, courseid, roleid )" \
        " VALUES( %(enrol)s, %(status)s, %(course_id)s, %(role_id)s )".format(entete=entete)
    mark.execute(s, params={'enrol': enrol, 'status': status, 'course_id': course_id, 'role_id': role_id})


###########################################################
# Fonction permettant d'inserer un forum.
###########################################################
def insert_moodle_forum(mark, entete, course, name, intro, intro_format, max_bytes, max_attachements, time_modified):
    s = "INSERT INTO {entete}forum ( course, name, intro, introformat, maxbytes, maxattachments, timemodified ) " \
        " VALUES ( %(course)s, %(name)s, %(intro)s, %(intro_format)s, %(max_bytes)s, %(max_attachements)s, %(time_modified)s )".format(entete=entete)
    mark.execute(s, params={'course': course,
                            'name': name,
                            'intro': intro,
                            'intro_format': intro_format,
                            'max_bytes': max_bytes,
                            'max_attachements': max_attachements,
                            'time_modified': time_modified})


###########################################################
# Fonction permettant de vérifier si un utilisateur est
# admin local pour un contexte donne.
###########################################################
def is_moodle_local_admin(mark, entete, id_context_categorie, id_user):
    id_role_admin_local = get_id_role_admin_local(mark, entete)
    sql = "SELECT id FROM {entete}role_assignments" \
          " WHERE roleid = %(id_role_admin_local)s" \
          " AND contextid = %(id_context_categorie)s" \
          " AND userid = %(id_user)s".format(entete=entete)
    sql = sql % (id_role_admin_local, id_context_categorie, id_user)
    params = {'id_role_admin_local': id_role_admin_local, 'id_context_categorie': id_context_categorie, 'id_user': id_user}
    logging.info(sql % params)
    mark.execute(sql, params=params)
    return mark.rowcount > 0


###########################################################
# Fonction permettant d'inserer un admin local pour un 
# contexte donne.
# Retour True si insertion réalisée, False le cas échéant
###########################################################
def insert_moodle_local_admin(mark, entete, id_context_categorie, id_user):
    if is_moodle_local_admin(mark, entete, id_context_categorie, id_user):
        return False
    id_role_admin_local = get_id_role_admin_local(mark, entete)
    s = "INSERT ignore INTO {entete}role_assignments( roleid, contextid, userid )" \
        " VALUES ( %(id_role_admin_local)s, %(id_context_categorie)s, %(id_user)s )".format(entete=entete)
    params = {'id_role_admin_local': id_role_admin_local, 'id_context_categorie': id_context_categorie, 'id_user': id_user}
    logging.info(s % params)
    mark.execute(s, params=params)
    return True


###########################################################
# Fonction permettant d'inserer une structure dans Moodle.
###########################################################
def insert_moodle_structure(mark, entete, grp, nom_structure, path, ou, siren, uai):
    # Recuperation du timestamp
    now = get_timestamp_now(mark)

    # Creation de la description pour la structure
    description = siren
    if grp:
        description = siren + "@" + nom_structure

    #########################
    # PARTIE CATEGORIE
    #########################
    # Insertion de la categorie correspondant a l'etablissement
    insert_moodle_course_category(mark, entete, ou, description, description, uai)
    id_categorie_etablissement = get_id_course_category_by_id_number(mark, entete, siren)

    # Mise a jour du path de la categorie
    path_etablissement = "/%d" % (id_categorie_etablissement)
    update_course_category_path(mark, entete, id_categorie_etablissement, path_etablissement)

    #########################
    # PARTIE CONTEXTE
    #########################
    # Insertion du contexte associe a la categorie de l'etablissement
    insert_moodle_context(mark, entete, NIVEAU_CTX_CATEGORIE, PROFONDEUR_CTX_ETAB, id_categorie_etablissement)
    id_contexte_etablissement = get_id_context(mark, entete, NIVEAU_CTX_CATEGORIE, PROFONDEUR_CTX_ETAB,
                                               id_categorie_etablissement)

    # Mise a jour du path de la categorie
    path_contexte_etablissement = "%s/%d" % (path, id_contexte_etablissement)
    update_context_path(mark, entete, id_contexte_etablissement, path_contexte_etablissement)

    #########################
    # PARTIE ZONE PRIVEE
    #########################
    # Insertion du cours pour le forum de discussion
    id_zone_privee = insert_zone_privee(mark, entete, id_categorie_etablissement, siren, ou, now)

    # Insertion du contexte associe
    id_contexte_zone_privee = insert_zone_privee_context(mark, entete, id_zone_privee)

    # Mise a jour du path du contexte
    path_contexte_zone_privee = "%s/%d" % (path_contexte_etablissement, id_contexte_zone_privee)
    update_context_path(mark, entete, id_contexte_zone_privee, path_contexte_zone_privee)

    #########################
    # PARTIE INSCRIPTIONS
    #########################
    # Ouverture du cours a l'inscription manuelle
    enrol = COURSE_ENROL_MANUAL
    status = COURSE_ENROL_ENROL
    role_id = ID_ROLE_ELEVE
    insert_moodle_enrol_capability(mark, entete, enrol, status, id_zone_privee, role_id)

    #########################
    # PARTIE FORUM
    #########################
    # Insertion du forum au sein de la zone privee
    course = id_zone_privee
    name = FORUM_NAME_ZONE_PRIVEE % ou.encode("utf-8")
    intro = FORUM_INTRO_ZONE_PRIVEE
    intro_format = FORUM_INTRO_FORMAT_ZONE_PRIVEE
    max_bytes = FORUM_MAX_BYTES_ZONE_PRIVEE
    max_attachements = FORUM_MAX_ATTACHEMENTS_ZONE_PRIVEE
    time_modified = now

    insert_moodle_forum(mark, entete, course, name, intro, intro_format, max_bytes, max_attachements, time_modified)
    id_forum = get_id_forum(mark, entete, course)

    #########################
    # PARTIE MODULE
    #########################
    # Insertion du module forum dans la zone privee
    course = id_zone_privee
    module = COURSE_MODULES_MODULE
    instance = id_forum
    added = now

    insert_moodle_course_module(mark, entete, course, module, instance, added)
    id_course_module = get_id_course_module(mark, entete, course)

    # Insertion du contexte pour le module de cours (forum)
    insert_moodle_context(mark, entete, NIVEAU_CTX_FORUM, PROFONDEUR_CTX_MODULE_ZONE_PRIVEE, id_course_module)
    id_contexte_module = get_id_context(mark, entete, NIVEAU_CTX_FORUM, PROFONDEUR_CTX_MODULE_ZONE_PRIVEE,
                                        id_course_module)

    # Mise a jour du path du contexte
    path_contexte_module = "%s/%d" % (path_contexte_zone_privee, id_contexte_module)
    update_context_path(mark, entete, id_contexte_module, path_contexte_module)

    #########################
    # PARTIE BLOC
    #########################
    # Insertion du bloc de recherche forum
    parent_context_id = id_contexte_zone_privee
    block_name = BLOCK_FORUM_SEARCH_NAME
    show_in_subcontexts = BLOCK_FORUM_SEARCH_SHOW_IN_SUB_CTX
    page_type_pattern = BLOCK_FORUM_SEARCH_PAGE_TYPE_PATTERN
    sub_page_pattern = BLOCK_FORUM_SEARCH_SUB_PAGE_PATTERN
    default_region = BLOCK_FORUM_SEARCH_DEFAULT_REGION
    default_weight = BLOCK_FORUM_SEARCH_DEFAULT_WEIGHT

    insert_moodle_block(mark, entete, block_name, parent_context_id, show_in_subcontexts, page_type_pattern,
                        sub_page_pattern, default_region, default_weight)
    id_block = get_id_block(mark, entete, parent_context_id)

    # Insertion du contexte pour le bloc
    insert_moodle_context(mark, entete, NIVEAU_CTX_BLOC, PROFONDEUR_CTX_BLOCK_ZONE_PRIVEE, id_block)
    id_contexte_bloc = get_id_context(mark, entete, NIVEAU_CTX_BLOC, PROFONDEUR_CTX_BLOCK_ZONE_PRIVEE, id_block)

    # Mise a jour du path du contexte
    path_contexte_bloc = "%s/%d" % (path_contexte_zone_privee, id_contexte_bloc)
    update_context_path(mark, entete, id_contexte_bloc, path_contexte_module)

    #########################
    # PARTIE LOGGING
    #########################
    logging.info('  |_ Insertion de %s %s' % (siren, ou.encode("utf-8")))


###########################################################
# Fonction permettant d'inserer un utilisateur dans Moodle.
###########################################################
def insert_moodle_user(mark, entete, username, first_name, last_name, email, mail_display, theme):
    user_id = get_user_id(mark, entete, username)
    username = username.lower()
    if user_id is None:
        s = "INSERT INTO {entete}user( auth, confirmed, username, firstname, lastname, email, maildisplay, city, country, lang, mnethostid, theme )" \
            " VALUES ( %(USER_AUTH)s, 1, %(username)s, %(first_name)s, %(last_name)s, %(email)s, %(mail_display)s, %(USER_CITY)s, %(USER_COUNTRY)s, %(USER_LANG)s, %(USER_MNET_HOST_ID)s, %(theme)s )".format(entete=entete)

        mark.execute(s, params={'USER_AUTH': USER_AUTH,
                                'username': username,
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': email,
                                'mail_display': mail_display,
                                'USER_CITY': USER_CITY,
                                'USER_COUNTRY': USER_COUNTRY,
                                'USER_LANG': USER_LANG,
                                'USER_MNET_HOST_ID': USER_MNET_HOST_ID,
                                'theme': theme})
        logging.info("      |_ Insertion de %s %s %s" % (username, first_name, last_name))


###########################################################
# Fonction permettant d'inserer un user info data.
###########################################################
def insert_moodle_user_info_data(mark, entete, id_user, id_field, data):
    s = "INSERT INTO {entete}user_info_data ( userid, fieldid, data )" \
        " VALUES ( %(id_user)s, %(id_field)s, %(data)s)".format(entete=entete)
    mark.execute(s, params={'id_user': id_user, 'id_field': id_field, 'data': data})


###########################################################
# Fonction permettant d'inserer un user info field.
###########################################################
def insert_moodle_user_info_field(mark, entete, short_name, name, data_type, id_category, param1, param2, locked,
                                  visible):
    s = "INSERT INTO {entete}user_info_field ( shortname, name, datatype, categoryid, param1, param2, locked, visible )" \
        " VALUES ( %(short_name)s, %(name)s, %(data_type)s, %(id_category)s, %(param1)s, %(param2)s, %(locked)s, %(visible)s )".format(entete=entete)
    mark.execute(s, params={'short_name': short_name,
                            'name': name,
                            'data_type': data_type,
                            'id_category': id_category,
                            'param1': param1,
                            'param2': param2,
                            'locked': locked,
                            'visible': visible})
    logging.info("      |_ Insertion du user info field %s - %s" % (name, short_name))


###########################################################
# Fonction permettant d'inserer le user info field utilise
# pour la classe.
###########################################################
def insert_moodle_user_info_field_classe(mark, entete):
    short_name = USER_INFO_FIELD_SHORTNAME_CLASSE
    name = USER_INFO_FIELD_NAME_CLASSE
    data_type = USER_INFO_FIELD_DATATYPE_CLASSE
    id_category = USER_INFO_FIELD_CATEGORY_ID_CLASSE
    param1 = USER_INFO_FIELD_PARAM1_CLASSE
    param2 = USER_INFO_FIELD_PARAM2_CLASSE
    locked = USER_INFO_FIELD_LOCKED_CLASSE
    visible = USER_INFO_FIELD_VISIBLE_CLASSE
    insert_moodle_user_info_field(mark, entete, short_name, name, data_type, id_category, param1, param2, locked,
                                  visible)


###########################################################
# Fonction permettant d'inserer le cours correspondant
# a la zone privee.
#
# Retour :
#   - L'identifiant de la zone privee creee
###########################################################
def insert_zone_privee(mark, entete, id_categorie_etablissement, siren, ou, time):
    full_name = COURSE_FULLNAME_ZONE_PRIVEE
    id_number = short_name = COURSE_SHORTNAME_ZONE_PRIVEE % siren
    summary = COURSE_SUMMARY_ZONE_PRIVEE % ou.encode("utf-8")
    format = COURSE_FORMAT_ZONE_PRIVEE
    visible = COURSE_VISIBLE_ZONE_PRIVEE
    num_sections = COURSE_NUM_SECTIONS_ZONE_PRIVEE
    start_date = time_created = time_modified = time
    insert_moodle_course(mark, entete, id_categorie_etablissement, full_name, id_number, short_name, summary, format,
                         visible, num_sections, start_date, time_created, time_modified)
    logging.info('    |_ Creation de la zone privee pour la structure %s' % siren)
    id_zone_privee = get_id_course_by_id_number(mark, entete, id_number)
    return id_zone_privee


###########################################################
# Fonction permettant d'inserer le contexte correspondant
# a la zone privee.
#
# Retour :
#   - L'identifiant du contexte cree
###########################################################
def insert_zone_privee_context(mark, entete, id_zone_privee):
    id_contexte_zone_privee = get_id_context(mark, entete, NIVEAU_CTX_COURS, PROFONDEUR_CTX_ZONE_PRIVEE, id_zone_privee)
    if id_contexte_zone_privee:
        return id_contexte_zone_privee

    id_contexte_zone_privee = get_id_context_no_depth(mark, entete, NIVEAU_CTX_COURS, id_zone_privee)
    if id_contexte_zone_privee:
        return id_contexte_zone_privee

    insert_moodle_context(mark, entete, NIVEAU_CTX_COURS, PROFONDEUR_CTX_ZONE_PRIVEE, id_zone_privee)
    id_contexte_zone_privee = get_id_context(mark, entete, NIVEAU_CTX_COURS, PROFONDEUR_CTX_ZONE_PRIVEE, id_zone_privee)
    return id_contexte_zone_privee


###########################################################
# Fonction permettant de purger des cohortes.
# Le dictionnaire fourni en parametre indique la liste
# des ids utilisateurs appartenant a une cohorte.
# Ce dictionnaire est indexe par id de cohortes.
###########################################################
def purge_cohorts(mark, entete, users_ids_by_cohorts_ids):
    for cohort_id, users_ids in users_ids_by_cohorts_ids.iteritems():
        ids_list, ids_list_params = array_to_safe_sql_list(users_ids, 'ids_list')
        s = "DELETE FROM {entete}cohort_members" \
            " WHERE cohortid = %(cohort_id)s" \
            " AND userid NOT IN ( {ids_list} )".format(entete=entete, ids_list=ids_list)
        mark.execute(s, params={'cohort_id': cohort_id, **ids_list_params})


###########################################################
# Fonction permettant de mettre a jour le path d'un
# contexte.
###########################################################
def update_context_path(mark, entete, id_context, new_path):
    s = "UPDATE {entete}context" \
        " SET path = %(new_path)s" \
        " WHERE id = %(id_context)s".format(entete=entete)
    mark.execute(s, params={'new_path': new_path, 'id_context': id_context})


###########################################################
# Fonction permettant de mettre a jour la description
# d'une categorie.
###########################################################
def update_course_category_description(mark, entete, id_category, new_description):
    s = "UPDATE {entete}course_categories" \
        " SET description = %(new_description)s" \
        " WHERE id = %(id_category)s".format(entete=entete)
    mark.execute(s, params={'new_description': new_description, 'id_category': id_category})


###########################################################
# Fonction permettant de mettre a jour le nom
# d'une categorie.
###########################################################
def update_course_category_name(mark, entete, id_category, new_name):
    s = "UPDATE {entete}course_categories" \
        " SET name = %(new_name)s" \
        " WHERE id = %(id_category)s".format(entete=entete)
    mark.execute(s, params={'new_name': new_name, 'id_category': id_category})


###########################################################
# Fonction permettant de mettre a jour le path d'une
# categorie.
###########################################################
def update_course_category_path(mark, entete, id_category, new_path):
    s = "UPDATE {entete}course_categories SET path = %(new_path)s WHERE id = %(id_category)s".format(entete=entete)
    mark.execute(s, params={'new_path': new_path, 'id_category': id_category})


###########################################################
# Fonction permettant de mettre a jour un utilisateur
###########################################################
def update_moodle_user(mark, entete, id_user, first_name, last_name, email, mail_display, theme):
    s = "UPDATE {entete}user SET auth = %(USER_AUTH)s, firstname = %(first_name)s, lastname = %(last_name)s, email = %(email)s, maildisplay = %(mail_display)s, city = %(USER_CITY)s, country = %(USER_COUNTRY)s, lang = %(USER_LANG)s, mnethostid = %(USER_MNET_HOST_ID)s, theme = %(theme)s" \
        " WHERE id = %(id_user)s".format(entete=entete)
    mark.execute(s, params={'USER_AUTH': USER_AUTH,
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
    logging.info("      |_ Mise a jour de %s %s ( id : %s )" % (first_name, last_name, id_user))


###########################################################
# Fonction permettant de mettre a jour le data d'un user
# info data.
###########################################################
def update_user_info_data(mark, entete, id_user, id_field, new_data):
    s = "UPDATE {entete}user_info_data SET data = %(new_data)s " \
        " WHERE userid = %(id_user)s AND fieldid = %(id_field)s".format(entete=entete)
    mark.execute(s, params={'new_data': new_data, 'id_user': id_user, 'id_field': id_field})


###########################################################
# Fonction pour récupére l'id du champ Domaine
###########################################################
def get_field_domaine(mark, entete):
    id_field_domaine = []
    sql = "SELECT id FROM {entete}user_info_field WHERE shortname = 'Domaine' AND name ='Domaine'".format(entete=entete)
    mark.execute(sql)
    row = mark.fetchall()

    # Si le champ n'existe pas, on le crée et on récupère l'id
    if not bool(row):
        id_field_domaine = 0
    else:
        id_field_domaine = row[0][0]

    return id_field_domaine


def is_enseignant_avance(mark, entete, id_user, id_role_enseignant_avance):
    if id_user != 0:
        sql = "Select id from {entete}role_assignments where userid = %(id_user)s and roleid = %(id_role_enseignant_avance)s".format(entete=entete)
        mark.execute(sql, params={'id_user': id_user, 'id_role_enseignant_avance': id_role_enseignant_avance})
        if mark.rowcount > 0:
            return True
        else:
            return False


###########################################################
# Fonction pour saisir le Domaine d'un utilisateur Moodle
###########################################################
def set_user_domain(mark, entete, id_user, id_field_domaine, user_domain):
    # pour un utilisateur qui est déjà dans la table "user_info_data" mais sur un autre domaine que le domaine "user_domain",
    # le script va essayer de créer une nouvelle ligne (INSERT) avec le nouveau domaine => erreur !
    # la requête doit donc être modifiée :
    # sql = "SELECT id FROM %suser_info_data WHERE userid = %s AND fieldid = %s AND data = '%s'"
    sql = "SELECT id FROM {entete}user_info_data " \
          "WHERE userid = %(id_user)s AND fieldid = %(id_field_domaine)s LIMIT 1" \
        .format(entete=entete)
    mark.execute(sql, params={'id_user': id_user, 'id_field_domaine': id_field_domaine})

    result = mark.fetchone()
    if result:
        sql = "REPLACE INTO {entete}user_info_data " \
              "(id, userid, fieldid, data) VALUES " \
              "(%(id)s, %(id_user)s, %(id_field_domaine)s, %(user_domain)s)" \
            .format(entete=entete)
        mark.execute(sql, params={'id': result[0],
                                  'id_user': id_user,
                                  'id_field_domaine': id_field_domaine,
                                  'user_domain': user_domain})
    else:
        sql = "INSERT INTO {entete}user_info_data " \
              "(userid, fieldid, data) VALUES " \
              "(%(id_user)s, %(id_field_domaine)s, %(user_domain)s)" \
            .format(entete=entete)
        mark.execute(sql, params={'id_user': id_user,
                                  'id_field_domaine': id_field_domaine,
                                  'user_domain': user_domain})
