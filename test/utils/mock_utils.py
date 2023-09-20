"""
Module permettant de retourner les valeurs de test
pour les fonctions mockées
"""

def fake_get_courses_user_enrolled_test_eleves(userid: int):
    """
    Retourne les cours auxquels est inscrit l'utilisateur passé en paramètre.

    :param userid: L'id de l'élève
    :return: La liste des ids des cours
    """
    return_values = {492286:[37000],492287:[],492288:[],492289:[],492290:[37000],492291:[],\
    492292:[],492293:[],492294:[],492295:[37000],492296:[37000],492297:[],492298:[]}
    return return_values[userid]

def fake_get_courses_user_enrolled_test_enseignants(userid: int):
    """
    Retourne les cours auxquels est inscrit l'utilisateur passé en paramètre.

    :param userid: L'id de l'enseignant
    :return: La liste des ids des cours
    """
    return_values = {492216:[37000],492217:[37001],492220:[37002],492221:[37003],\
    492224:[37004],492225:[37005],492228:[37006],492229:[37007]}
    if userid not in return_values:
        return []
    return return_values[userid]

def fake_get_courses_user_enrolled_test_cours(notused):
    """
    Retourne les cours auxquels sont inscrits les utilisateurs pour les test des cours

    :return: La liste des ids des cours
    """
    return [37000,37001,37002,37003,37004,37005]

def fake_get_last_course_access_test_cours(courseid: int):
    """
    Retourne la date de dernier accès pour les tests des cours
    :param courseid: L'id du cours
    :return: La date de dernier accès
    """
    print(courseid)
    return_values = {37003: 0, 37005: 0, 37007: 0}
    return return_values[courseid]
