from synchromoodle import ldaputils


def test_get_filtre_eleves():
    assert ldaputils._get_filtre_eleves() == \
        "(&(objectClass=ENTEleve))"
    assert ldaputils._get_filtre_eleves(uai="some-uai") == \
        "(&(objectClass=ENTEleve)(ESCOUAI=some-uai))"
    assert ldaputils._get_filtre_eleves(since_timestamp="12345646") == \
        "(&(objectClass=ENTEleve)(modifyTimeStamp>=12345646))"
    assert ldaputils._get_filtre_eleves(since_timestamp="6432354", uai="other-uai") == \
        "(&(objectClass=ENTEleve)(ESCOUAI=other-uai)(modifyTimeStamp>=6432354))"


def test_get_filtre_etablissement():
    assert ldaputils._get_filtre_etablissement("0290009C") == "(&(ObjectClass=ENTEtablissement)" \
                                                              "(!(ENTStructureSiren=0000000000000A))" \
                                                              "(ENTStructureUAI=0290009C))"
    assert ldaputils._get_filtre_etablissement() == "(&(ObjectClass=ENTEtablissement)" \
                                                    "(!(ENTStructureSiren=0000000000000A)))"


def test_get_filtre_personnes():
    assert ldaputils._get_filtre_personnes(1548429409) == \
           "(&(|(objectClass=ENTPerson))(!(uid=ADM00000))" \
           "(|)" \
           "(modifyTimeStamp>=1548429409))"
    assert ldaputils._get_filtre_personnes(1548429445, foo="bar", hello=["world", "dude"]) == \
        "(&(|(objectClass=ENTPerson))" \
        "(!(uid=ADM00000))" \
        "(|(foo=bar)(hello=world)(hello=dude))" \
        "(modifyTimeStamp>=1548429445))"


def test_get_filtre_enseignants():
    assert ldaputils.get_filtre_enseignants() == "(&(objectClass=ENTAuxEnseignant)" \
                                                 "(!(uid=ADM00000)))"
    assert ldaputils.get_filtre_enseignants(1548429445, "UAI00000", True) == "(&" \
                                                                             "(|(objectClass=ENTDirecteur)" \
                                                                             "(objectClass=ENTAuxEnseignant)" \
                                                                             "(objectClass=ENTAuxNonEnsEtab)" \
                                                                             "(objectClass=ENTAuxNonEnsCollLoc)" \
                                                                             ")" \
                                                                             "(!(uid=ADM00000))" \
                                                                             "(ESCOUAI=UAI00000)" \
                                                                             "(modifyTimeStamp>=1548429445))"
