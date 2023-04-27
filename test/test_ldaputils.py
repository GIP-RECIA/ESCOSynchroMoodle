# coding: utf-8
"""
Module pour les tests vis à vis de l'accès et de la récupération
de données depuis le ldap
"""

from datetime import datetime

import pytest
from ldap3 import Connection

from synchromoodle import ldaputils
from synchromoodle.config import Config
from synchromoodle.ldaputils import Ldap, StructureLdap, PersonneLdap, EleveLdap, EnseignantLdap
from test.utils import ldap_utils

datetime_value = datetime(2019, 4, 9, 21, 42, 1)


@pytest.fixture(scope='function')
def ldap(docker_config: Config):
    """
    Créé l'objet LDAP pour intéragir avec le LDAP dans le container docker.

    :param docker_config: La configuration avec les infos des containers dockers
    :returns: L'objet LDAP instancié
    """
    ldap = Ldap(docker_config.ldap)
    ldap_utils.reset(ldap)
    return ldap


def test_connection(ldap: Ldap):
    """
    Teste la connection au LDAP.

    :param ldap: L'objet ldap permettant d'intéragir avec le ldap dans le docker
    """
    ldap.connect()
    assert isinstance(ldap.connection, Connection)
    ldap.disconnect()
    assert ldap.connection is None


def test_structures(ldap: Ldap):
    """
    Teste si la liste des structures est remplie si on insère des données dans le ldap.

    :param ldap: L'objet ldap permettant d'intéragir avec le ldap dans le docker
    """
    ldap.connect()
    ldap_utils.run_ldif('data/default-structures.ldif', ldap)
    structures = ldap.search_structure()
    assert len(structures) == 2
    for structure in structures:
        assert isinstance(structure, StructureLdap)
        getted_structure = ldap.get_structure(structure.uai)
        assert isinstance(getted_structure, StructureLdap)
    ldap.disconnect()


def test_structures_empty(ldap: Ldap):
    """
    Teste si la liste des structures est vide si on n'insère pas de données dans le ldap.

    :param ldap: L'objet ldap permettant d'intéragir avec le ldap dans le docker
    """
    ldap.connect()
    structures = ldap.search_structure()
    assert len(structures) == 0
    ldap.disconnect()


def test_personnes(ldap: Ldap):
    """
    Teste si la liste des personnes est remplie si on insère des données dans le ldap.

    :param ldap: L'objet ldap permettant d'intéragir avec le ldap dans le docker
    """
    ldap.connect()
    ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
    personnes = ldap.search_personne()
    assert len(personnes) == 77
    for person in personnes:
        assert isinstance(person, PersonneLdap)
    ldap.disconnect()


def test_personnes_empty(ldap: Ldap):
    """
    Teste si la liste des personnes est vide si on n'insère pas de données dans le ldap.

    :param ldap: L'objet ldap permettant d'intéragir avec le ldap dans le docker
    """
    ldap.connect()
    personnes = ldap.search_personne()
    assert len(personnes) == 0
    ldap.disconnect()


def test_eleves(ldap: Ldap):
    """
    Teste si la liste des élèves est remplie si on insère des données dans le ldap.

    :param ldap: L'objet ldap permettant d'intéragir avec le ldap dans le docker
    """
    ldap.connect()
    ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
    eleves = ldap.search_eleve()
    assert len(eleves) > 0
    for student in eleves:
        assert isinstance(student, EleveLdap)
    ldap.disconnect()


def test_eleves_empty(ldap: Ldap):
    """
    Teste si la liste des élèves est vide si on n'insère pas de données dans le ldap.

    :param ldap: L'objet ldap permettant d'intéragir avec le ldap dans le docker
    """
    ldap.connect()
    eleves = ldap.search_eleve()
    assert len(eleves) == 0
    ldap.disconnect()


def test_teachers(ldap: Ldap):
    """
    Teste si la liste des enseignants est remplie si on insère des données dans le ldap.

    :param ldap: L'objet ldap permettant d'intéragir avec le ldap dans le docker
    """
    ldap.connect()
    ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
    enseignants = ldap.search_enseignant()
    assert len(enseignants) > 0
    for enseignant in enseignants:
        assert isinstance(enseignant, EnseignantLdap)
    ldap.disconnect()


def test_teachers_empty(ldap: Ldap):
    """
    Teste si la liste des enseignants est vide si on n'insère pas de données dans le ldap.

    :param ldap: L'objet ldap permettant d'intéragir avec le ldap dans le docker
    """
    ldap.connect()
    enseignants = ldap.search_enseignant()
    assert len(enseignants) == 0
    ldap.disconnect()


def test_get_filtre_eleves():
    """Teste si les filtres élèves sont corrects."""
    assert ldaputils._get_filtre_eleves() == \
           "(&(objectClass=ENTEleve))"
    assert ldaputils._get_filtre_eleves(uai="some-uai") == "(&(objectClass=ENTEleve)(ESCOUAI=some-uai))"
    assert ldaputils._get_filtre_eleves(since_timestamp=datetime_value) == \
        "(&(objectClass=ENTEleve)(modifyTimeStamp>=20190409214201Z))"
    assert ldaputils._get_filtre_eleves(since_timestamp=datetime_value, uai="other-uai") == \
        "(&(objectClass=ENTEleve)(ESCOUAI=other-uai)(modifyTimeStamp>=20190409214201Z))"


def test_get_filtre_etablissement():
    """Teste si les filtres établissements sont corrects."""
    assert ldaputils._get_filtre_etablissement("0290009C") == "(&(ObjectClass=ENTEtablissement)" \
                                                              "(!(ENTStructureSiren=0000000000000A))" \
                                                              "(ENTStructureUAI=0290009C))"
    assert ldaputils._get_filtre_etablissement() == "(&(ObjectClass=ENTEtablissement)" \
                                                    "(!(ENTStructureSiren=0000000000000A)))"


def test_get_filtre_personnes():
    """Teste si les filtres personnes sont corrects."""
    assert ldaputils._get_filtre_personnes(datetime_value) == \
           "(&(|(objectClass=ENTPerson))(!(uid=ADM00000))" \
           "(modifyTimeStamp>=20190409214201Z))"
    assert ldaputils._get_filtre_personnes(datetime_value, foo="bar", hello=["world", "dude"]) in \
        ["(&(|(objectClass=ENTPerson))"
         "(!(uid=ADM00000))"
         "(|(foo=bar)(hello=world)(hello=dude))"
         "(modifyTimeStamp>=20190409214201Z))",
         "(&(|(objectClass=ENTPerson))"
         "(!(uid=ADM00000))"
         "(|(hello=world)(hello=dude)(foo=bar))"
         "(modifyTimeStamp>=20190409214201Z))"]


def test_get_filtre_enseignants():
    """Teste si les filtres enseignants sont corrects."""
    assert ldaputils.get_filtre_enseignants() == "(&(objectClass=ENTAuxEnseignant)" \
                                                 "(!(uid=ADM00000)))"
    assert ldaputils.get_filtre_enseignants(datetime_value, "UAI00000", True) == \
        "(&" \
        "(|(objectClass=ENTAuxEnseignant)" \
        "(objectClass=ENTAuxNonEnsEtab)" \
        "(objectClass=ENTAuxNonEnsCollLoc)" \
        ")" \
        "(!(uid=ADM00000))" \
        "(ESCOUAI=UAI00000)" \
        "(modifyTimeStamp>=20190409214201Z))"
