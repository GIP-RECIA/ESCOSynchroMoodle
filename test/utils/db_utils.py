# coding: utf-8

import re
from pkgutil import get_data

import sqlparse
from cachetools import cached, Cache

from synchromoodle.dbutils import Database
from synchromoodle.config import Config
from synchromoodle.webserviceutils import WebService

SECONDS_PER_DAY = 86400
ID_TEST_CATEGORY = 1
__statements_cache = Cache(maxsize=100)

def init(db: Database):
    run_script('data/ddl.sql', db)


def reset(db: Database):
    run_script('data/ddl.sql', db)


@cached(__statements_cache)
def _get_statements(path: str):
    script_data = str(get_data('test', path), 'utf8')
    cleaned_script_data = re.sub(r'/\*.+?\*/;\n', "", script_data, flags=re.MULTILINE)
    statements = sqlparse.split(cleaned_script_data)
    return statements


def run_script(script: str, db: Database, connect=True):
    if connect:
        db.connect()
    try:
        statements = _get_statements(script)
        for statement in statements:
            db.mark.execute(statement)
            while db.mark.nextset():
                pass
        db.connection.commit()
    finally:
        if connect:
            db.disconnect()

def insert_fake_user(db: Database, username: str, first_name: str, last_name: str, email: str, mail_display: int, theme: str):
    """
    Fonction permettant d'insérer un utilisateur de test
    :returns: L'id de l'utilisateur inséré
    """
    db.insert_moodle_user(username, first_name, last_name, email, mail_display, theme)
    return db.get_user_id(username)

def insert_fake_course_reference_eleve(db: Database, userid: int):
    """
    Fonction permettant de donner une référence à un élève dans un cours
    On ne se préoccupe pas des dépendances car ici la table de l'historique des notes
    peut de toute manière faire référence à des cours qui n'éxistent plus
    """
    s = "INSERT INTO {entete}grade_grades_history (action, oldid, source, timemodified, loggeduser, itemid, userid, rawgrade, rawgrademax, rawgrademin, rawscaleid, usermodified, finalgrade, hidden, locked, locktime, exported, overridden, excluded, feedback, feedbackformat, information, informationformat) VALUES (1, 0, 'mod/assign', 0, 0, 0, %(userid)s, 50, 100.00000, 0.00000, NULL, NULL, NULL, 0, 0, 0, 0, 0, 0, NULL, 0, NULL, 0)".format(entete=db.entete)
    db.mark.execute(s, params={'userid': userid})
    return db.mark.lastrowid

def update_lastlogin_user(db, userid: int, lastlogin):
    """
    Fonction permettant de mettre a jour la date de dernière connexion d'un utilisateur
    :param db: L'objet Database représentant la base de données moodle
    :param userid: L'id de l'utilisateur à modifier
    :param lastlogin: Le timestamp (en s) représentant la date de dernière connexion de l'utilisateur
    :return:
    """
    s = "UPDATE {entete}user SET lastlogin = %(lastlogin)s WHERE id = %(userid)s".format(entete=db.entete)
    db.mark.execute(s, params={'lastlogin': lastlogin, 'userid': userid})

def insert_eleves(db: Database, config: Config, webservice: WebService):
    """
    Insérère toutes les données nécéssaisres aux tests
    des élèves dans la base de données moodle
    """
    #Récupération du timestamp actuel
    now = db.get_timestamp_now()

    #Insertion des utilisateurs de test (élèves)
    eleveid_a = insert_fake_user(db, "F1700tsa", "testeleve", "A", "testeleve.A@netocentre.fr", 2, "0290009c")
    eleveid_b = insert_fake_user(db, "F1700tsb", "testeleve", "B", "testeleve.B@netocentre.fr", 2, "0290009c")
    eleveid_c = insert_fake_user(db, "F1700tsc", "testeleve", "C", "testeleve.C@netocentre.fr", 2, "0290009c")
    eleveid_d = insert_fake_user(db, "F1700tsd", "testeleve", "D", "testeleve.D@netocentre.fr", 2, "0290009c")
    eleveid_e = insert_fake_user(db, "F1700tse", "testeleve", "E", "testeleve.E@netocentre.fr", 2, "0290009c")
    eleveid_f = insert_fake_user(db, "F1700tsf", "testeleve", "F", "testeleve.F@netocentre.fr", 2, "0290009c")
    eleveid_g = insert_fake_user(db, "F1700tsg", "testeleve", "G", "testeleve.G@netocentre.fr", 2, "0290009c")
    eleveid_h = insert_fake_user(db, "F1700tsh", "testeleve", "H", "testeleve.H@netocentre.fr", 2, "0290009c")
    eleveid_i = insert_fake_user(db, "F1700tsi", "testeleve", "I", "testeleve.I@netocentre.fr", 2, "0290009c")
    eleveid_j = insert_fake_user(db, "F1700tsj", "testeleve", "J", "testeleve.J@netocentre.fr", 2, "0290009c")
    eleveid_k = insert_fake_user(db, "F1700tsk", "testeleve", "K", "testeleve.K@netocentre.fr", 2, "0290009c")
    eleveid_l = insert_fake_user(db, "F1700tsl", "testeleve", "L", "testeleve.L@netocentre.fr", 2, "0290009c")
    eleveid_m = insert_fake_user(db, "F1700tsm", "testeleve", "M", "testeleve.M@netocentre.fr", 2, "0290009c")

    #Changement des dates de dernière connexions
    update_lastlogin_user(db, eleveid_a, now - (config.delete.delay_delete_student + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, eleveid_b, now - (config.delete.delay_delete_student + 1)* SECONDS_PER_DAY)
    update_lastlogin_user(db, eleveid_c, now - (config.delete.delay_delete_student + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, eleveid_d, now - (config.delete.delay_anonymize_student + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, eleveid_e, now - (config.delete.delay_force_delete + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, eleveid_g, now - (config.delete.delay_anonymize_student + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, eleveid_h, now - (config.delete.delay_force_delete + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, eleveid_i, now - (config.delete.delay_force_delete + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, eleveid_j, now - (config.delete.delay_anonymize_student + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, eleveid_k, now)
    update_lastlogin_user(db, eleveid_l, now)
    update_lastlogin_user(db, eleveid_m, now)

    #Mise à jour BD
    db.connection.commit()

    #Création d'un cours factice pour y inscire les éventuels utilisateurs
    db.insert_moodle_course(1, "testnettoyage", 0, "testnettoyage", "", "", 1, 0, 0, 0)
    course_test_id = db.mark.lastrowid

    #Inscription des utilisateurs aux cours factices
    db.enroll_user_in_course(config.constantes.id_role_eleve, course_test_id, eleveid_a)
    db.enroll_user_in_course(config.constantes.id_role_eleve, course_test_id, eleveid_e)
    db.enroll_user_in_course(config.constantes.id_role_eleve, course_test_id, eleveid_k)
    db.enroll_user_in_course(config.constantes.id_role_eleve, course_test_id, eleveid_j)

    #Création de fausses références dans des cours
    refid_b = insert_fake_course_reference_eleve(db, eleveid_b)
    refid_d = insert_fake_course_reference_eleve(db, eleveid_d)
    refid_h = insert_fake_course_reference_eleve(db, eleveid_h)
    refid_l = insert_fake_course_reference_eleve(db, eleveid_l)

    #Mise à jour BD
    db.connection.commit()
