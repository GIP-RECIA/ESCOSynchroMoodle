# coding: utf-8

from datetime import datetime

import pytest
from ldap3 import Connection

from synchromoodle import ldaputils
from synchromoodle.config import Config
from synchromoodle.ldaputils import Ldap, StructureLdap, PeopleLdap, StudentLdap, TeacherLdap
from test.utils import ldap_utils

datetime_value = datetime(2019, 4, 9, 21, 42, 1)


@pytest.fixture(scope='function')
def ldap(docker_config: Config):
    ldap = Ldap(docker_config.ldap)
    ldap_utils.reset(ldap)
    return ldap


def test_connection(ldap: Ldap):
    ldap.connect()
    assert isinstance(ldap.connection, Connection)
    ldap.disconnect()
    assert ldap.connection is None


def test_structures(ldap: Ldap):
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
    ldap.connect()
    structures = ldap.search_structure()
    assert len(structures) == 0
    ldap.disconnect()


def test_people(ldap: Ldap):
    ldap.connect()
    ldap_utils.run_ldif('data/default-people-short.ldif', ldap)
    people = ldap.search_people()
    assert len(people) == 74
    for person in people:
        assert isinstance(person, PeopleLdap)
    ldap.disconnect()


def test_people_empty(ldap: Ldap):
    ldap.connect()
    people = ldap.search_people()
    assert len(people) == 0
    ldap.disconnect()


def test_students(ldap: Ldap):
    ldap.connect()
    ldap_utils.run_ldif('data/default-people-short.ldif', ldap)
    students = ldap.search_student()
    assert len(students) > 0
    for student in students:
        assert isinstance(student, StudentLdap)
    ldap.disconnect()


def test_students_empty(ldap: Ldap):
    ldap.connect()
    students = ldap.search_student()
    assert len(students) == 0
    ldap.disconnect()


def test_teachers(ldap: Ldap):
    ldap.connect()
    ldap_utils.run_ldif('data/default-people-short.ldif', ldap)
    teachers = ldap.search_teacher()
    assert len(teachers) > 0
    for teacher in teachers:
        assert isinstance(teacher, TeacherLdap)
    ldap.disconnect()


def test_teachers_empty(ldap: Ldap):
    ldap.connect()
    teachers = ldap.search_teacher()
    assert len(teachers) == 0
    ldap.disconnect()


def test_get_filtre_eleves():
    assert ldaputils._get_filtre_eleves() == \
           "(&(objectClass=ENTEleve))"
    assert ldaputils._get_filtre_eleves(uai="some-uai") == "(&(objectClass=ENTEleve)(ESCOUAI=some-uai))"
    assert ldaputils._get_filtre_eleves(since_timestamp=datetime_value) == \
        "(&(objectClass=ENTEleve)(modifyTimeStamp>=2019-04-09T21:42:01))"
    assert ldaputils._get_filtre_eleves(since_timestamp=datetime_value, uai="other-uai") == \
        "(&(objectClass=ENTEleve)(ESCOUAI=other-uai)(modifyTimeStamp>=2019-04-09T21:42:01))"


def test_get_filtre_etablissement():
    assert ldaputils._get_filtre_etablissement("0290009C") == "(&(ObjectClass=ENTEtablissement)" \
                                                              "(!(ENTStructureSiren=0000000000000A))" \
                                                              "(ENTStructureUAI=0290009C))"
    assert ldaputils._get_filtre_etablissement() == "(&(ObjectClass=ENTEtablissement)" \
                                                    "(!(ENTStructureSiren=0000000000000A)))"


def test_get_filtre_personnes():
    assert ldaputils._get_filtre_personnes(datetime_value) == \
           "(&(|(objectClass=ENTPerson))(!(uid=ADM00000))" \
           "(modifyTimeStamp>=2019-04-09T21:42:01))"
    assert ldaputils._get_filtre_personnes(datetime_value, foo="bar", hello=["world", "dude"]) in \
        ["(&(|(objectClass=ENTPerson))"
         "(!(uid=ADM00000))"
         "(|(foo=bar)(hello=world)(hello=dude))"
         "(modifyTimeStamp>=2019-04-09T21:42:01))",
         "(&(|(objectClass=ENTPerson))"
         "(!(uid=ADM00000))"
         "(|(hello=world)(hello=dude)(foo=bar))"
         "(modifyTimeStamp>=2019-04-09T21:42:01))"]


def test_get_filtre_enseignants():
    assert ldaputils.get_filtre_enseignants() == "(&(objectClass=ENTAuxEnseignant)" \
                                                 "(!(uid=ADM00000)))"
    assert ldaputils.get_filtre_enseignants(datetime_value, "UAI00000", True) == \
        "(&" \
        "(|(objectClass=ENTDirecteur)" \
        "(objectClass=ENTAuxEnseignant)" \
        "(objectClass=ENTAuxNonEnsEtab)" \
        "(objectClass=ENTAuxNonEnsCollLoc)" \
        ")" \
        "(!(uid=ADM00000))" \
        "(ESCOUAI=UAI00000)" \
        "(modifyTimeStamp>=2019-04-09T21:42:01))"
