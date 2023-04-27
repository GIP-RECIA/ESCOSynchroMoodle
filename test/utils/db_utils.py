# coding: utf-8
"""
Moduel permettant les intéractions nécéssaires à la base de données
moodle pour les tests
"""

import re
from pkgutil import get_data

import sqlparse
from cachetools import cached, Cache

from synchromoodle.dbutils import Database
from synchromoodle.config import Config

SECONDS_PER_DAY = 86400
ID_TEST_CATEGORY = 1
__statements_cache = Cache(maxsize=100)

def init(db: Database):
    """Initialise la base de données"""
    run_script('data/ddl.sql', db)


def reset(db: Database):
    """Réinitialise la base de données"""
    run_script('data/ddl.sql', db)


@cached(__statements_cache)
def _get_statements(path: str):
    script_data = str(get_data('test', path), 'utf8')
    cleaned_script_data = re.sub(r'/\*.+?\*/;\n', "", script_data, flags=re.MULTILINE)
    statements = sqlparse.split(cleaned_script_data)
    return statements


def run_script(script: str, db: Database, connect=True):
    """
    Permet de lancer un script sur la base de données moodle.

    :param script: Le chemin d'accès vers le fichier contenant le script .sql
    :param db: L'objet Database pour intéragir avec la bd
    :param connect: Si on est déjà connecté ou non à la base de données
    """
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

def insert_fake_user(db: Database, username: str, first_name: str, last_name: str,
                     email: str, mail_display: int, theme: str):
    """
    Fonction permettant d'insérer un utilisateur de test.

    :param db: L'objet Database pour intéragir avec la bd
    :param username: Le username de l'utilisateur factice
    :param first_name: Le prénom de l'utilisateur factice
    :param last_name: Le nom de l'utilisateur factice
    :param email: L'e-mail de l'utilisateur factice
    :param mail_display: Le mail display de l'utilisateur factice
    :param theme: Le theme de l'utilisateur factice
    :returns: L'id de l'utilisateur inséré
    """
    db.insert_moodle_user(username, first_name, last_name, email, mail_display, theme)
    return db.get_user_id(username)

def enrol_user_to_fake_course(db: Database, roleid: int, courseid: int, userid: int):
    """
    Fonction permettant d'inscrire un utilisateur à un cours factice.

    :param db: L'objet Database pour intéragir avec la bd
    :param roleid: L'id du rôle avec lequel on inscrit l'utilisateur au cours
    :param courseid: L'id du cours dans lequel on inscrit l'utilisateur
    :param userid: L'id de l'utilisateur à inscrire
    """
    #Inscription au cours
    db.enroll_user_in_course(roleid, courseid, userid)
    #Récupération du contexte du cours
    context_course_id = db.get_id_context_no_depth(db.constantes.niveau_ctx_cours, courseid)
    #Ajout du rôle désiré dans le contexte du cours
    db.add_role_to_user(roleid, context_course_id, userid)

def insert_fake_course(db: Database, id_category: int, full_name: str, id_number: str, short_name: str, summary: str,
 format_: str, visible: int, start_date: int, time_created: int, time_modified: int):
    """
    Fonction permattant de créer un cours factice.

    :param db: L'objet Database pour intéragir avec la bd
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
    :returns: L'id du faux cours inséré
    """
    #Insertion du cours
    db.insert_moodle_course(id_category, full_name, id_number, short_name, summary,
                            format_, visible, start_date, time_created, time_modified)
    id_course = db.mark.lastrowid
    #Insertion du contexte correspondant au cours
    db.insert_moodle_context(db.constantes.niveau_ctx_cours, 3, id_course)
    return id_course

def insert_fake_course_reference_eleve(db: Database, userid: int):
    """
    Fonction permettant de donner une référence à un élève dans un cours.
    On ne se préoccupe pas des dépendances car ici la table de l'historique des notes
    peut de toute manière faire référence à des cours qui n'existent plus.

    :param db: L'objet Database pour intéragir avec la bd
    :param userid: L'id de l'utilisateur dont on veut créer les fausses références
    :returns: L'id de la fausse référence insérée
    """
    s = "INSERT INTO {entete}grade_grades_history (action, oldid, source, timemodified, loggeduser,"\
        " itemid, userid, rawgrade, rawgrademax, rawgrademin, rawscaleid, usermodified, finalgrade,"\
        " hidden, locked, locktime, exported, overridden, excluded, feedback, feedbackformat, information,"\
        " informationformat) VALUES (1, 0, 'mod/assign', 0, 0, 0, %(userid)s, 50, 100.00000, 0.00000, NULL,"\
        " NULL, NULL, 0, 0, 0, 0, 0, 0, NULL, 0, NULL, 0)".format(entete=db.entete)
    db.mark.execute(s, params={'userid': userid})
    return db.mark.lastrowid

def insert_fake_course_reference_enseignant(db: Database, loggeduser: int):
    """
    Fonction permettant de donner une référence à un enseignant dans un cours.
    On ne se préoccupe pas des dépendances car ici la table de l'historique des notes
    peut de toute manière faire référence à des cours qui n'existent plus.

    :param db: L'objet Database pour intéragir avec la bd
    :param loggeduser: L'id de l'utilisateur dont on veut créer les fausses références
    :returns: L'id de la fausse référence insérée
    """
    s = "INSERT INTO {entete}grade_grades_history (action, oldid, source, timemodified, loggeduser, itemid,"\
        " userid, rawgrade, rawgrademax, rawgrademin, rawscaleid, usermodified, finalgrade, hidden, locked,"\
        " locktime, exported, overridden, excluded, feedback, feedbackformat, information, informationformat)"\
        " VALUES (1, 0, 'mod/assign', 0, %(loggeduser)s, 0, 0, 50, 100.00000, 0.00000, NULL, NULL, NULL, 0,"\
        " 0, 0, 0, 0, 0, NULL, 0, NULL, 0)".format(entete=db.entete)
    db.mark.execute(s, params={'loggeduser': loggeduser})
    return db.mark.lastrowid

def update_lastlogin_user(db: Database, userid: int, lastlogin):
    """
    Fonction permettant de mettre a jour la date de dernière connexion d'un utilisateur.

    :param db: L'objet Database représentant la base de données moodle
    :param userid: L'id de l'utilisateur à modifier
    :param lastlogin: Le timestamp (en s) représentant la date de dernière connexion de l'utilisateur
    """
    s = f"UPDATE {db.entete}user SET lastlogin = %(lastlogin)s WHERE id = %(userid)s"
    db.mark.execute(s, params={'lastlogin': lastlogin, 'userid': userid})

def update_timemodified_course(db: Database, courseid: int, timemodified):
    """
    Fonction permettant de mettre a jour la date de dernière modification d'un cours.

    :param db: L'objet Database représentant la base de données moodle
    :param courseid: L'id du cours à modifier
    :param timemodified: Le timestamp (en s) représentant la date de dernière modification du cours
    """
    s = f"UPDATE {db.entete}course SET timemodified = %(timemodified)s WHERE id = %(courseid)s"
    db.mark.execute(s, params={'timemodified': timemodified, 'courseid': courseid})

def insert_eleves(db: Database, config: Config):
    """
    Insérère toutes les données nécéssaisres aux tests des élèves dans la base de données moodle.

    :param db: L'objet Database représentant la base de données moodle
    :param config: La configuration générale de type Config
    """
    #Récupération du timestamp actuel
    now = db.get_timestamp_now()

    #Insertion des utilisateurs de test (élèves)
    eleveid_a = insert_fake_user(db, "F1700tsa", "testeleve", "A", "testeleve.A@netocentre.fr", 2, "0290009c")
    eleveid_b = insert_fake_user(db, "F1700tsb", "testeleve", "B", "testeleve.B@netocentre.fr", 2, "0290009c")
    eleveid_c = insert_fake_user(db, "F1700tsc", "testeleve", "C", "testeleve.C@netocentre.fr", 2, "0290009c")
    eleveid_d = insert_fake_user(db, "F1700tsd", "testeleve", "D", "testeleve.D@netocentre.fr", 2, "0290009c")
    eleveid_e = insert_fake_user(db, "F1700tse", "testeleve", "E", "testeleve.E@netocentre.fr", 2, "0290009c")
    eleveid_g = insert_fake_user(db, "F1700tsg", "testeleve", "G", "testeleve.G@netocentre.fr", 2, "0290009c")
    eleveid_h = insert_fake_user(db, "F1700tsh", "testeleve", "H", "testeleve.H@netocentre.fr", 2, "0290009c")
    eleveid_i = insert_fake_user(db, "F1700tsi", "testeleve", "I", "testeleve.I@netocentre.fr", 2, "0290009c")
    eleveid_j = insert_fake_user(db, "F1700tsj", "testeleve", "J", "testeleve.J@netocentre.fr", 2, "0290009c")
    eleveid_k = insert_fake_user(db, "F1700tsk", "testeleve", "K", "testeleve.K@netocentre.fr", 2, "0290009c")
    eleveid_l = insert_fake_user(db, "F1700tsl", "testeleve", "L", "testeleve.L@netocentre.fr", 2, "0290009c")
    eleveid_m = insert_fake_user(db, "F1700tsm", "testeleve", "M", "testeleve.M@netocentre.fr", 2, "0290009c")
    insert_fake_user(db, "F1700tsf", "testeleve", "F", "testeleve.F@netocentre.fr", 2, "0290009c")

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
    db.insert_moodle_course(ID_TEST_CATEGORY, "testnettoyage", 0, "testnettoyage", "", "", 1, 0, 0, 0)
    course_test_id = db.mark.lastrowid

    #Inscription des utilisateurs aux cours factices
    db.enroll_user_in_course(config.constantes.id_role_eleve, course_test_id, eleveid_a)
    db.enroll_user_in_course(config.constantes.id_role_eleve, course_test_id, eleveid_e)
    db.enroll_user_in_course(config.constantes.id_role_eleve, course_test_id, eleveid_k)
    db.enroll_user_in_course(config.constantes.id_role_eleve, course_test_id, eleveid_j)

    #Création de fausses références dans des cours
    insert_fake_course_reference_eleve(db, eleveid_b)
    insert_fake_course_reference_eleve(db, eleveid_d)
    insert_fake_course_reference_eleve(db, eleveid_h)
    insert_fake_course_reference_eleve(db, eleveid_l)

    #Mise à jour BD
    db.connection.commit()


def insert_enseignants(db: Database, config: Config):
    """
    Insérère toutes les données nécéssaisres aux tests des enseignants dans la base de données moodle.

    :param db: L'objet Database représentant la base de données moodle
    :param config: La configuration générale de type Config
    """
    #Récupération du timestamp actuel
    now = db.get_timestamp_now()

    #Insertion des utilisateurs de test (profs)
    profid_a = insert_fake_user(db, "F1700tta", "testprof", "A", "testprof.A@netocentre.fr", 2, "0290009c")
    profid_b = insert_fake_user(db, "F1700ttb", "testprof", "B", "testprof.B@netocentre.fr", 2, "0290009c")
    profid_c = insert_fake_user(db, "F1700ttc", "testprof", "C", "testprof.C@netocentre.fr", 2, "0290009c")
    profid_d = insert_fake_user(db, "F1700ttd", "testprof", "D", "testprof.D@netocentre.fr", 2, "0290009c")
    profid_e = insert_fake_user(db, "F1700tte", "testprof", "E", "testprof.E@netocentre.fr", 2, "0290009c")
    profid_f = insert_fake_user(db, "F1700ttf", "testprof", "F", "testprof.F@netocentre.fr", 2, "0290009c")
    profid_g = insert_fake_user(db, "F1700ttg", "testprof", "G", "testprof.G@netocentre.fr", 2, "0290009c")
    profid_h = insert_fake_user(db, "F1700tth", "testprof", "H", "testprof.H@netocentre.fr", 2, "0290009c")
    profid_i = insert_fake_user(db, "F1700tti", "testprof", "I", "testprof.I@netocentre.fr", 2, "0290009c")
    profid_j = insert_fake_user(db, "F1700ttj", "testprof", "J", "testprof.J@netocentre.fr", 2, "0290009c")
    profid_k = insert_fake_user(db, "F1700ttk", "testprof", "K", "testprof.K@netocentre.fr", 2, "0290009c")
    profid_l = insert_fake_user(db, "F1700ttl", "testprof", "L", "testprof.L@netocentre.fr", 2, "0290009c")
    profid_m = insert_fake_user(db, "F1700ttm", "testprof", "M", "testprof.M@netocentre.fr", 2, "0290009c")
    profid_n = insert_fake_user(db, "F1700ttn", "testprof", "N", "testprof.N@netocentre.fr", 2, "0290009c")
    profid_o = insert_fake_user(db, "F1700tto", "testprof", "O", "testprof.O@netocentre.fr", 2, "0290009c")
    profid_p = insert_fake_user(db, "F1700ttp", "testprof", "P", "testprof.P@netocentre.fr", 2, "0290009c")
    profid_q = insert_fake_user(db, "F1700ttq", "testprof", "Q", "testprof.Q@netocentre.fr", 2, "0290009c")

    #Donner le rôle créateur de cours aux enseignants créés afin de les identifier comme des enseignants
    id_context_test_category = db.get_id_context_categorie(ID_TEST_CATEGORY)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_a)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_b)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_c)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_d)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_e)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_f)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_g)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_h)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_i)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_j)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_k)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_l)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_m)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_n)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_o)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_p)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_q)

    #Changement des dates de dernière connexions
    update_lastlogin_user(db, profid_a, now)
    update_lastlogin_user(db, profid_b, now)
    update_lastlogin_user(db, profid_c, now)
    update_lastlogin_user(db, profid_d, now)
    update_lastlogin_user(db, profid_e, now - (config.delete.delay_anonymize_teacher + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_f, now - (config.delete.delay_anonymize_teacher + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_g, now - (config.delete.delay_anonymize_teacher + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_h, now - (config.delete.delay_anonymize_teacher + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_i, now - (config.delete.delay_backup_course + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_j, now - (config.delete.delay_backup_course + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_k, now - (config.delete.delay_backup_course + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_l, now - (config.delete.delay_backup_course + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_m, now - (config.delete.delay_delete_teacher + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_n, now - (config.delete.delay_delete_teacher + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_o, now - (config.delete.delay_delete_teacher + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_p, now - (config.delete.delay_delete_teacher + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_p, now - (config.delete.delay_force_delete + 1) * SECONDS_PER_DAY)

    #Mise à jour BD
    db.connection.commit()

    #Création de cours factices pour y inscire les éventuels utilisateurs
    course_a_testprof_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyageA",
                                             0, "testnettoyageA", "", "", 1, 0, 0, 0)
    course_b_testprof_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyageB",
                                             0, "testnettoyageB", "", "", 1, 0, 0, 0)
    course_e_testprof_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyageE",
                                             0, "testnettoyageE", "", "", 1, 0, 0, 0)
    course_f_testprof_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyageF",
                                             0, "testnettoyageF", "", "", 1, 0, 0, 0)
    course_i_testprof_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyageI",
                                             0, "testnettoyageI", "", "", 1, 0, 0, 0)
    course_j_testprof_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyageJ",
                                             0, "testnettoyageJ", "", "", 1, 0, 0, 0)
    course_m_testprof_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyageM",
                                             0, "testnettoyageM", "", "", 1, 0, 0, 0)
    course_n_testprof_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyageN",
                                             0, "testnettoyageN", "", "", 1, 0, 0, 0)

    #Changement des dates de dernière modification des cours
    update_timemodified_course(db, course_j_testprof_id, 0)
    update_timemodified_course(db, course_n_testprof_id, 0)

    #Inscription des utilisateurs aux cours factices
    #Inscriptions simples hors enseignant
    enrol_user_to_fake_course(db, config.constantes.id_role_eleve, course_a_testprof_id, profid_a)
    enrol_user_to_fake_course(db, config.constantes.id_role_eleve, course_e_testprof_id, profid_e)
    enrol_user_to_fake_course(db, config.constantes.id_role_eleve, course_i_testprof_id, profid_i)
    enrol_user_to_fake_course(db, config.constantes.id_role_eleve, course_m_testprof_id, profid_m)

    #Inscriptions en tant que propriétaire de cours
    enrol_user_to_fake_course(db, config.constantes.id_role_proprietaire_cours, course_b_testprof_id, profid_b)
    enrol_user_to_fake_course(db, config.constantes.id_role_proprietaire_cours, course_f_testprof_id, profid_f)
    enrol_user_to_fake_course(db, config.constantes.id_role_proprietaire_cours, course_j_testprof_id, profid_j)
    enrol_user_to_fake_course(db, config.constantes.id_role_proprietaire_cours, course_n_testprof_id, profid_n)

    #Création de fausses références dans des cours
    insert_fake_course_reference_enseignant(db, profid_c)
    insert_fake_course_reference_enseignant(db, profid_g)
    insert_fake_course_reference_enseignant(db, profid_k)
    insert_fake_course_reference_enseignant(db, profid_o)

    #Mise à jour BD
    db.connection.commit()


def insert_courses(db: Database, config: Config):
    """
    Insérère toutes les données nécéssaisres aux tests des cours dans la base de données moodle.

    :param db: L'objet Database représentant la base de données moodle
    :param config: La configuration générale de type Config
    """
    #Récupération du timestamp actuel
    now = db.get_timestamp_now()

    #Création des cours de test
    course1_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyage1", 0, "testnettoyage1", "", "", 1, 0, 0, 0)
    course2_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyage2", 0, "testnettoyage2", "", "", 1, 0, 0, 0)
    course3_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyage3", 0, "testnettoyage3", "", "", 1, 0, 0, 0)
    course4_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyage4", 0, "testnettoyage4", "", "", 1, 0, 0, 0)
    course5_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyage5", 0, "testnettoyage5", "", "", 1, 0, 0, 0)
    course6_id = insert_fake_course(db, ID_TEST_CATEGORY, "testnettoyage6", 0, "testnettoyage6", "", "", 1, 0, 0, 0)

    #Création d'utilisateurs factices à inscire dans les cours pour pouvoir vérifier les traitements sur les cours
    profid_x = insert_fake_user(db, "F1700ttx", "testprof", "X", "testprof.X@netocentre.fr", 2, "0290009c")
    profid_y = insert_fake_user(db, "F1700tty", "testprof", "Y", "testprof.Y@netocentre.fr", 2, "0290009c")
    id_context_test_category = db.get_id_context_categorie(ID_TEST_CATEGORY)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_x)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_y)
    update_lastlogin_user(db, profid_x, now - (config.delete.delay_backup_course + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_y, now)

    #Mise à jour BD
    db.connection.commit()

    #Inscription des enseignants factices dans les différents cours
    enrol_user_to_fake_course(db, config.constantes.id_role_proprietaire_cours, course1_id, profid_x)
    enrol_user_to_fake_course(db, config.constantes.id_role_proprietaire_cours, course2_id, profid_x)
    enrol_user_to_fake_course(db, config.constantes.id_role_enseignant, course3_id, profid_x)
    enrol_user_to_fake_course(db, config.constantes.id_role_proprietaire_cours, course4_id, profid_x)
    enrol_user_to_fake_course(db, config.constantes.id_role_proprietaire_cours, course5_id, profid_x)
    enrol_user_to_fake_course(db, config.constantes.id_role_enseignant, course6_id, profid_x)
    enrol_user_to_fake_course(db, config.constantes.id_role_proprietaire_cours, course2_id, profid_y)
    enrol_user_to_fake_course(db, config.constantes.id_role_proprietaire_cours, course3_id, profid_y)
    enrol_user_to_fake_course(db, config.constantes.id_role_proprietaire_cours, course5_id, profid_y)
    enrol_user_to_fake_course(db, config.constantes.id_role_proprietaire_cours, course6_id, profid_y)

    #Changement des dates de dernière modification des cours
    update_timemodified_course(db, course1_id, now)
    update_timemodified_course(db, course2_id, now)
    update_timemodified_course(db, course3_id, now)
    update_timemodified_course(db, course4_id, now - (config.delete.delay_backup_course + 1) * SECONDS_PER_DAY)
    update_timemodified_course(db, course5_id, now - (config.delete.delay_backup_course + 1) * SECONDS_PER_DAY)
    update_timemodified_course(db, course6_id, now - (config.delete.delay_backup_course + 1) * SECONDS_PER_DAY)

    #Mise à jour BD
    db.connection.commit()
