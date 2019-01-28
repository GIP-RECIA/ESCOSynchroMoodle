# coding: utf-8

from datetime import datetime

from synchromoodle import ldaputils

datetime_value = datetime(2019, 4, 9, 21, 42, 1)


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
           "(|)" \
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
