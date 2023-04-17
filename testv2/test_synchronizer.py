"""
Module de tests de la synchronisation, le principe est le suivant :
- Insertion de données de test dans la base de données moodle (donc pas présentes dans le LDAP)
- Lancement du script de synchronisation
- Vérification des modifications/suppressions sur les données qui avaient été insérées
Les fonctions de test suivent la convention de nommage définie ci-dessous :
test_[type utilisateur]_[comportement attendu]_[délai de connexion]_[cas testé]
"""

import pytest
from test_utils import *
from logging import getLogger
from synchromoodle.dbutils import Database
from synchromoodle import actions
from argparse import ArgumentParser,Namespace
from synchromoodle.config import ConfigLoader,Config
from synchromoodle.webserviceutils import WebService

@pytest.fixture(scope="module", name="temp")
def temp():
    """
    Dictionnaire utilisé pour tracker toutes les objets de tests
    qui ont été insérés dans la base de données
    """
    temp = {"eleves":[],"courses":[],"references":[], "profs":[]}
    return temp

@pytest.fixture(scope="module", name="arguments")
def arguments():
    """
    Permet de charger les arguments (nom du fichier de config)
    """
    parser = ArgumentParser(description="Scrit de synchronisation de moodle depuis l'annuaire LDAP.")
    parser.add_argument("-c", "--config", action="append", dest="config", default=[],
                        help="Chemin vers un fichier de configuration. Lorsque cette option est utilisée plusieurs "
                             "fois, les fichiers de configuration sont alors fusionnés.")
    #Simule un argument sur la ligne de commande pour pour lancer avec le bon fichier de config
    arguments = parser.parse_args(["--config", "config/nettoyage.yml"])
    return arguments

@pytest.fixture(scope="module", name="config")
def config(arguments):
    """
    Permet de charger la config
    """
    config_loader = ConfigLoader()
    config = config_loader.load(['config.yml', 'config.yaml'], True)
    config = config_loader.update(config, arguments.config)

    log = getLogger()

    try:
        config.validate()
    except ValueError as e:
        log.error(e)
        exit(1)

    return config

@pytest.fixture(scope="module", name="webservice")
def webservice(config: Config, arguments):
    """
    Fixture permettant d'utiliser l'objet webservice
    """
    webservice = WebService(config.webservice)
    return webservice

@pytest.fixture(scope="module", name="db")
def db(config: Config, arguments: Namespace, temp: dict[str, list[int]], webservice: WebService):
    """
    Fixture permettant d'utiliser la bd
    """
    #Exécution avant tous les tests
    db = Database(config.database, config.constantes)
    db.connect()
    yield db

    #Exécution après tous les tests : remise à l'état avant les tests de la BD

    #Suppression des cours de test
    webservice.delete_courses(temp["courses"])

    #Suppression des références de test
    for refid in temp["references"]:
        remove_fake_course_reference(db, refid)

    #Suppression des utilisateurs de test
    for userid in temp["eleves"]:
        remove_fake_user(db, userid)
    for userid in temp["profs"]:
        remove_fake_user(db, userid)

    db.connection.commit()
    db.disconnect()


@pytest.fixture(scope="module", autouse=True)
def inserts(db: Database, config: Config, arguments: Namespace, temp: dict[str, list[int]], webservice: WebService):
    """
    Remplit la base de données avec les données nécéssaires pour les tests
    Cette fonction va s'éxécuter une fois avant tous les tests
    """

    #Insertion des élèves
    insert_eleves(db, config, arguments, temp, webservice)

    #Insertion des profs
    insert_profs(db, config, arguments, temp, webservice)

    #Mise à jour BD avant de faire les tests
    db.connection.commit()


@pytest.fixture(scope="module", autouse=True)
def run_script(config: Config, arguments: Namespace):
    """
    Fonction permettant de lancer le script
    """
    for action in config.actions:
        action_func = getattr(actions, action.type)
        action_func(config, action, arguments)



#--- TEST ELEVES ---#

def test_eleve_anon_delete_delay_enrolled(db):
    """
    Elève qui ne s'est pas connecté depuis le délai pour être supprimé
    mais qui est inscrit à des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tsa"))[10] == "Anonyme"

def test_eleve_anon_delete_delay_references(db):
    """
    Elève qui ne s'est pas connecté depuis le délai pour être supprimé
    mais qui a des références dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tsb"))[10] == "Anonyme"

def test_eleve_delete_delete_delay_no_references_and_enrollements(db):
    """
    Elève qui ne s'est pas connecté depuis le délai pour être supprimé
    et qui n'a ni références ni inscriptions
    """
    assert db.get_user_data(db.get_user_id("F1700tsc")) == None

def test_eleve_anon_anon_delay_references(db):
    """
    Elève qui ne s'est pas connecté depuis le délai pour être anonymisé
    mais qui a des références dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tsd"))[10] == "Anonyme"

def test_eleve_delete_force_delay_enrolled(db):
    """
    Elève qui ne s'est pas connecté depuis le délai pour être supprimé de force
    mais qui a des inscriptions dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tse")) == None

def test_eleve_delete_never_used(db):
    """
    Elève qui n'a jamais utilisé moodle
    """
    assert db.get_user_data(db.get_user_id("F1700tsf")) == None

def test_eleve_nothing_anon_delay_no_references_and_enrollements(db):
    """
    Elève qui ne s'est pas connecté depuis le délai pour être anonymisé
    mais qui n'a pas de références ou d'inscriptions dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tsg"))[11] == "G"

def test_eleve_delete_force_delay_references(db):
    """
    Elève qui ne s'est pas connecté depuis le délai pour être supprimé de force
    mais qui a des références dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tsh")) == None

def test_eleve_delete_force_delay_no_references_and_enrollements(db):
    """
    Elève qui ne s'est pas connecté depuis le délai pour être supprimé de force
    et qui n'a ni références ni inscriptions
    """
    assert db.get_user_data(db.get_user_id("F1700tsi")) == None

def test_eleve_anon_anon_delay_enrolled(db):
    """
    Elève qui ne s'est pas connecté depuis le délai pour être anonymisé
    mais qui est inscrit à des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tsj"))[10] == "Anonyme"

def test_eleve_nothing_no_delay_enrolled(db):
    """
    Elève qui s'est connecté avant les délais
    et qui est inscrit à des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tsk"))[11] == "K"

def test_eleve_nothing_no_delay_references(db):
    """
    Elève qui s'est connecté avant les délais
    et qui a des références dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tsl"))[11] == "L"

def test_eleve_nothing_no_delay_no_references_and_enrollements(db):
    """
    Elève qui s'est connecté avant les délais
    mais qui n'est ni inscrit à des cours ni possède de références
    """
    assert db.get_user_data(db.get_user_id("F1700tsm"))[11] == "M"


#--- TEST ENSEIGNANTS ---#

#Pas de délai
def test_enseignant_nothing_no_delay_enrolled(db):
    """
    Enseignant qui s'est connecté avant les délais et
    qui est inscrit à des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tta"))[11] == "A"

def test_enseignant_nothing_no_delay_owner(db):
    """
    Enseignant qui s'est connecté avant les délais et
    qui possède un cours
    """
    assert db.get_user_data(db.get_user_id("F1700ttb"))[11] == "B"

def test_enseignant_nothing_no_delay_references(db):
    """
    Enseignant qui s'est connecté avant les délais et
    qui possède des références dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700ttc"))[11] == "C"

def test_enseignant_nothing_no_delay_no_references_and_enrollements(db):
    """
    Enseignant qui s'est connecté avant les délais
    mais qui n'a pas de références ni d'inscriptions
    """
    assert db.get_user_data(db.get_user_id("F1700ttd"))[11] == "D"

#Délais d'anonymisation
def test_enseignant_anon_anon_delay_enrolled(db):
    """
    Enseignant qui ne s'est pas connecté depuis le délai pour être anonymisé
    et qui est inscrit à des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tte"))[10] == "Anonyme"

def test_enseignant_anon_anon_delay_owner(db):
    """
    Enseignant qui ne s'est pas connecté depuis le délai pour être anonymisé
    et qui possède un cours
    """
    assert db.get_user_data(db.get_user_id("F1700ttf"))[10] == "Anonyme"

def test_enseignant_anon_anon_delay_references(db):
    """
    Enseignant qui ne s'est pas connecté depuis le délai pour être anonymisé
    et qui possède des références dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700ttg"))[10] == "Anonyme"

def test_enseignant_anon_anon_delay_no_references_and_enrollements(db):
    """
    Enseignant qui ne s'est pas connecté depuis le délai pour être anonymisé
    mais qui n'a pas de références ni d'inscriptions
    """
    assert db.get_user_data(db.get_user_id("F1700tth"))[11] == "H"

#Délais de backup de cours
# TODO: Tester les traitements sur les cours
def test_enseignant_anon_backup_delay_enrolled(db):
    """
    Enseignant qui ne s'est pas connecté depuis le délai pour faire
    un backup de ses cours et qui est inscrit à des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tti"))[10] == "Anonyme"

def test_enseignant_anon_backup_delay_owner(db):
    """
    Enseignant qui ne s'est pas connecté depuis le délai pour faire
    un backup de ses cours et qui est possède un cours
    """
    assert db.get_user_data(db.get_user_id("F1700ttj"))[10] == "Anonyme"

def test_enseignant_anon_backup_delay_references(db):
    """
    Enseignant qui ne s'est pas connecté depuis le délai pour faire
    un backup de ses cours et qui possède des références dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700ttk"))[10] == "Anonyme"

def test_enseignant_anon_backup_delay_no_references_and_enrollements(db):
    """
    Enseignant qui ne s'est pas connecté depuis le délai pour faire un backup
    de ses cours mais qui n'a pas de références ni d'inscriptions
    """
    assert db.get_user_data(db.get_user_id("F1700ttl"))[11] == "H"

#Délais de suppression
def test_enseignant_anon_delete_delay_enrolled(db):
    """
    Enseignant qui ne s'est pas connecté depuis le délai pour être supprimé
    et qui est inscrit à des cours
    """
    assert db.get_user_data(db.get_user_id("F1700ttm"))[10] == "Anonyme"

def test_enseignant_anon_delete_delay_owner(db):
    """
    Enseignant qui ne s'est pas connecté depuis le délai pour être supprimé
    et qui possède un cours
    """
    assert db.get_user_data(db.get_user_id("F1700ttn"))[10] == "Anonyme"

def test_enseignant_anon_delete_delay_references(db):
    """
    Enseignant qui ne s'est pas connecté depuis le délai pour être supprimé
    et qui possède des références dans des cours
    """
    assert db.get_user_data(db.get_user_id("F1700tto"))[10] == "Anonyme"

def test_enseignant_delete_delete_delay_no_references_and_enrollements(db):
    """
    Enseignant qui ne s'est pas connecté depuis le délai pour être supprimé
    mais qui n'a pas de références ni d'inscriptions
    """
    assert db.get_user_data(db.get_user_id("F1700ttp")) == None

def test_enseignant_delete_never_used(db):
    """
    Enseignant qui n'a jamais utilisé moodle
    """
    assert db.get_user_data(db.get_user_id("F1700tsq")) == None
