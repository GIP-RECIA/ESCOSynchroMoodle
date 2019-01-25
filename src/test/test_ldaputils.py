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
