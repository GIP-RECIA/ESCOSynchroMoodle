"""
Module de tests de la synchronisation, le principe est le suivant :
- Insertion de données de test dans la base de données moodle (donc pas présentes dans le LDAP)
- Lancement du script de synchronisation
- Vérification des modifications/suppressions sur les données qui avaient été insérées
"""

import pytest
from logging import getLogger
from synchromoodle.dbutils import Database
from synchromoodle import actions
from synchromoodle.arguments import parse_args
from synchromoodle.config import ConfigLoader
from synchromoodle.webserviceutils import WebService

SECONDS_PER_DAY = 86400

def insert_fake_user(db: Database, username: str, first_name: str, last_name: str, email: str, mail_display: int, theme: str):
    """
    Fonction permettant d'insérer un utilisateur de test
    """
    db.insert_moodle_user(username, first_name, last_name, email, mail_display, theme)

def insert_fake_course_reference(db: Database, userid: int):
    """
    Fonction permettant de donner une référence à un utilisateur dans un cours
    On ne se préoccupe pas des dépendances car ici la table de l'historique des notes
    peut de toute manière faire référence à des cours qui n'éxistent plus
    """
    s = "INSERT INTO {entete}grade_grades_history (action, oldid, source, timemodified, loggeduser, itemid, userid, rawgrade, rawgrademax, rawgrademin, rawscaleid, usermodified, finalgrade, hidden, locked, locktime, exported, overridden, excluded, feedback, feedbackformat, information, informationformat) VALUES (1, 0, 'mod/assign', 0, 0, 0, %(userid)s, 50, 100.00000, 0.00000, NULL, NULL, NULL, 0, 0, 0, 0, 0, 0, NULL, 0, NULL, 0)".format(entete=db.entete)
    db.mark.execute(s, params={'userid': userid})

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

@pytest.fixture(scope="module", name="db")
def db():
    arguments = parse_args()

    config_loader = ConfigLoader()
    config = config_loader.load(['config.yml', 'config.yaml'], True)
    config = config_loader.update(config, arguments.config)

    log = getLogger()

    try:
        config.validate()
    except ValueError as e:
        log.error(e)
        exit(1)
    db = Database(config.database, config.constantes)
    db.connect()
    return db

@pytest.fixture(scope="module", autouse=True)
def inserts(db: Database):
    """
    Remplit la base de données avec les données nécéssaires pour les tests
    """

    arguments = parse_args()

    config_loader = ConfigLoader()
    config = config_loader.load(['config.yml', 'config.yaml'], True)
    config = config_loader.update(config, arguments.config)

    log = getLogger()

    try:
        config.validate()
    except ValueError as e:
        log.error(e)
        exit(1)

    webservice = WebService(config.webservice)
    now = db.get_timestamp_now()

    #Insertion des utilisateurs de test
    insert_fake_user(db, "F1700tsa", "test", "A", "test.A@netocentre.fr", 2, "0290009c")
    insert_fake_user(db, "F1700tsb", "test", "B", "test.B@netocentre.fr", 2, "0290009c")
    insert_fake_user(db, "F1700tsc", "test", "C", "test.C@netocentre.fr", 2, "0290009c")
    insert_fake_user(db, "F1700tsd", "test", "D", "test.D@netocentre.fr", 2, "0290009c")
    insert_fake_user(db, "F1700tse", "test", "E", "test.E@netocentre.fr", 2, "0290009c")
    insert_fake_user(db, "F1700tsf", "test", "F", "test.F@netocentre.fr", 2, "0290009c")
    insert_fake_user(db, "F1700tsg", "test", "G", "test.G@netocentre.fr", 2, "0290009c")

    #Récupération des id
    eleveid_a = db.get_user_id("F1700tsa")
    eleveid_b = db.get_user_id("F1700tsb")
    eleveid_c = db.get_user_id("F1700tsc")
    eleveid_d = db.get_user_id("F1700tsd")
    eleveid_e = db.get_user_id("F1700tse")
    eleveid_f = db.get_user_id("F1700tsf")
    eleveid_g = db.get_user_id("F1700tsg")

    #Changement des dates de dernière connexions
    update_lastlogin_user(db, eleveid_a, now - config.delete.delay_delete_student * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_b, now - config.delete.delay_delete_student * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_c, now - config.delete.delay_delete_student * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_d, now - config.delete.delay_anonymize_student * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_e, now - config.delete.delay_force_delete * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_g, now - config.delete.delay_anonymize_student * SECONDS_PER_DAY + 1)
    db.connection.commit()

    #Création d'un cours factice pour y inscire les éventuels utilisateurs
    course_test1_id = webservice.create_course("testnettoyage", "testnettoyage", 1)[0]["id"]

    #Inscription des utilisateurs aux cours factices
    webservice.enrol_user_to_course(config.constantes.id_role_eleve, db.get_user_id("F1700tsa"), course_test1_id)
    webservice.enrol_user_to_course(config.constantes.id_role_eleve, db.get_user_id("F1700tsd"), course_test1_id)

    #Création de fausses références dans des cours
    insert_fake_course_reference(db, eleveid_b)
    insert_fake_course_reference(db, eleveid_d)

    db.connection.commit()

@pytest.fixture(scope="module", autouse=True)
def run_script():
    """
    Fonction permettant de lancer le script
    """

    arguments = parse_args()

    config_loader = ConfigLoader()
    config = config_loader.load(['config.yml', 'config.yaml'], True)
    config = config_loader.update(config, arguments.config)

    log = getLogger()

    try:
        config.validate()
    except ValueError as e:
        log.error(e)
        exit(1)

    for action in config.actions:
        action_func = getattr(actions, action.type)
        action_func(config, action, arguments)


def test_eleve_anon_delete_delay_enrolled(db):
    """
    Utilisateur qui ne s'est pas connecté depuis le délai pour être supprimé
    mais qui est inscrit à des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tsa"))[10] == "Anonyme"

def test_eleve_anon_delete_delay_references(db):
    """
    Utilisateur qui ne s'est pas connecté depuis le délai pour être supprimé
    mais qui a des références dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tsb"))[10] == "Anonyme"

def test_eleve_delete_delete_delay_no_references_and_enrollements(db):
    """
    Utilisateur qui ne s'est pas connecté depuis le délai pour être supprimé
    et qui n'a ni références ni inscriptions
    """
    assert db.get_user_data(db.get_user_id("F1700tsc")) == None

def test_eleve_anon_anon_delay_references(db):
    """
    Utilisateur qui ne s'est pas connecté depuis le délai pour être anonymisé
    mais qui a des références dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tsd"))[10] == "Anonyme"

def test_eleve_delete_force_delay_enrolled(db):
    """
    Utilisateur qui ne s'est pas connecté depuis le délai pour être supprimé de force
    mais qui a des inscriptions dans ces cours
    """
    assert db.get_user_data(db.get_user_id("F1700tse")) == None

def test_eleve_delete_never_used(db):
    """
    Utilisateur qui n'a jamais utilisé moodle
    """
    assert db.get_user_data(db.get_user_id("F1700tsf")) == None

def test_eleve_nothing_anon_delay_no_references_and_enrollements(db):
    """
    Utilisateur qui ne s'est pas connecté depuis le délai pour être anonymisé
    mais qui n'a pas de références ou d'inscriptions dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tsg"))[11] == "G"