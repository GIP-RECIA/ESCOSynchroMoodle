from synchromoodle.dbutils import Database
from synchromoodle.config import Config
from synchromoodle.webserviceutils import WebService
from argparse import Namespace

SECONDS_PER_DAY = 86400

def is_anonymized(db: Database, userid: int):
    """
    Teste si un utilisateur est anonymisé
    :param userid: L'id de l'utilisateur
    :returns: Un booléen à True si l'utilisateur est anonyme, False sinon
    """
    try:
        return db.get_user_data(db.get_user_id(userid))[10] == "Anonyme"
    #Cas ou l'utilisateur est supprimé de la BD
    except TypeError as e:
        return False

def is_deleted(db: Database, userid: int):
    """
    Teste si un utilisateur est supprimé de la base de données moodle
    :param userid: L'id de l'utilisateur
    :returns: Un booléen à True si l'utilisateur n'est plus dans la base de données, False sinon
    """
    return db.get_user_data(db.get_user_id(userid)) == None

def is_normal(db: Database, userid: int, name: str):
    """
    Teste si un utilisateur est présent dans la base de données moodle sans qu'un
    traitement ait été effectué dessus, autrement dit qu'il n'ait pas été
    supprimé ou anonymisé
    :param userid: L'id de l'utilisateur
    :param name: Le nom originel de l'utilisateur
    :returns: Un booléen à True si l'utilisateur n'a pas eu de traitement
    """
    try:
        return db.get_user_data(db.get_user_id(userid))[11] == name
    #Cas ou l'utilisateur est supprimé de la BD
    except TypeError as e:
        return False


def insert_eleves(db: Database, config: Config, arguments: Namespace, temp: dict[str, list[int]], webservice: WebService):
    """
    Insérère toutes les données nécéssaisres aux tests
    des élèves dans la base de données moodle
    """
    #Récupération du timestamp actuel
    now = db.get_timestamp_now()

    #Insertion des utilisateurs de test (élèves)
    eleveid_a = insert_fake_user(db, "F1700tsa", "test", "A", "test.A@netocentre.fr", 2, "0290009c")
    eleveid_b = insert_fake_user(db, "F1700tsb", "test", "B", "test.B@netocentre.fr", 2, "0290009c")
    eleveid_c = insert_fake_user(db, "F1700tsc", "test", "C", "test.C@netocentre.fr", 2, "0290009c")
    eleveid_d = insert_fake_user(db, "F1700tsd", "test", "D", "test.D@netocentre.fr", 2, "0290009c")
    eleveid_e = insert_fake_user(db, "F1700tse", "test", "E", "test.E@netocentre.fr", 2, "0290009c")
    eleveid_f = insert_fake_user(db, "F1700tsf", "test", "F", "test.F@netocentre.fr", 2, "0290009c")
    eleveid_g = insert_fake_user(db, "F1700tsg", "test", "G", "test.G@netocentre.fr", 2, "0290009c")
    eleveid_h = insert_fake_user(db, "F1700tsh", "test", "H", "test.H@netocentre.fr", 2, "0290009c")
    eleveid_i = insert_fake_user(db, "F1700tsi", "test", "I", "test.I@netocentre.fr", 2, "0290009c")
    eleveid_j = insert_fake_user(db, "F1700tsj", "test", "J", "test.J@netocentre.fr", 2, "0290009c")
    eleveid_k = insert_fake_user(db, "F1700tsk", "test", "K", "test.K@netocentre.fr", 2, "0290009c")
    eleveid_l = insert_fake_user(db, "F1700tsl", "test", "L", "test.L@netocentre.fr", 2, "0290009c")
    eleveid_m = insert_fake_user(db, "F1700tsm", "test", "M", "test.M@netocentre.fr", 2, "0290009c")
    temp["eleves"].extend([eleveid_a,eleveid_b,eleveid_c,eleveid_d,eleveid_e,eleveid_f,eleveid_g,eleveid_h,\
    eleveid_i,eleveid_j,eleveid_k,eleveid_l,eleveid_m])

    #Changement des dates de dernière connexions
    update_lastlogin_user(db, eleveid_a, now - config.delete.delay_delete_student * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_b, now - config.delete.delay_delete_student * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_c, now - config.delete.delay_delete_student * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_d, now - config.delete.delay_anonymize_student * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_e, now - config.delete.delay_force_delete * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_g, now - config.delete.delay_anonymize_student * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_h, now - config.delete.delay_force_delete * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_i, now - config.delete.delay_force_delete * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_j, now - config.delete.delay_anonymize_student * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, eleveid_k, now)
    update_lastlogin_user(db, eleveid_l, now)
    update_lastlogin_user(db, eleveid_m, now)

    #Mise à jour BD
    db.connection.commit()

    #Création d'un cours factice pour y inscire les éventuels utilisateurs
    course_test1_id = webservice.create_course("testnettoyage", "testnettoyage", 1)[0]["id"]
    temp["courses"].append(course_test1_id)

    #Inscription des utilisateurs aux cours factices
    webservice.enrol_user_to_course(config.constantes.id_role_eleve, eleveid_a, course_test1_id)
    webservice.enrol_user_to_course(config.constantes.id_role_eleve, eleveid_d, course_test1_id)
    webservice.enrol_user_to_course(config.constantes.id_role_eleve, eleveid_k, course_test1_id)
    webservice.enrol_user_to_course(config.constantes.id_role_eleve, eleveid_j, course_test1_id)

    #Création de fausses références dans des cours
    refid_b = insert_fake_course_reference_eleve(db, eleveid_b)
    refid_d = insert_fake_course_reference_eleve(db, eleveid_d)
    refid_h = insert_fake_course_reference_eleve(db, eleveid_h)
    refid_l = insert_fake_course_reference_eleve(db, eleveid_l)
    temp["references"].extend([refid_b,refid_d,refid_h,refid_l])


def insert_profs(db: Database, config: Config, arguments: Namespace, temp: dict[str, list[int]], webservice: WebService):
    """
    Insérère toutes les données nécéssaisres aux tests
    des profs dans la base de données moodle
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
    temp["profs"].extend([profid_a,profid_b,profid_c,profid_d,profid_e,profid_f,profid_g,profid_h,\
    profid_i,profid_j,profid_k,profid_l,profid_m,profid_n,profid_o,profid_p,profid_q])

    #Changement des dates de dernière connexions
    update_lastlogin_user(db, profid_a, now)
    update_lastlogin_user(db, profid_b, now)
    update_lastlogin_user(db, profid_c, now)
    update_lastlogin_user(db, profid_d, now)
    update_lastlogin_user(db, profid_e, now - config.delete.delay_anonymize_teacher * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, profid_f, now - config.delete.delay_anonymize_teacher * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, profid_g, now - config.delete.delay_anonymize_teacher * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, profid_h, now - config.delete.delay_anonymize_teacher * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, profid_i, now - config.delete.delay_backup_course * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, profid_j, now - config.delete.delay_backup_course * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, profid_k, now - config.delete.delay_backup_course * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, profid_l, now - config.delete.delay_backup_course * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, profid_m, now - config.delete.delay_delete_teacher * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, profid_n, now - config.delete.delay_delete_teacher * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, profid_o, now - config.delete.delay_delete_teacher * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, profid_p, now - config.delete.delay_delete_teacher * SECONDS_PER_DAY + 1)
    update_lastlogin_user(db, profid_p, now - config.delete.delay_force_delete * SECONDS_PER_DAY + 1)

    #Mise à jour BD
    db.connection.commit()

    #Création de cours factices pour y inscire les éventuels utilisateurs
    courseA_testprof_id = webservice.create_course("testnettoyageA", "testnettoyageA", 1)[0]["id"]
    courseB_testprof_id = webservice.create_course("testnettoyageB", "testnettoyageB", 1)[0]["id"]
    courseE_testprof_id = webservice.create_course("testnettoyageE", "testnettoyageE", 1)[0]["id"]
    courseF_testprof_id = webservice.create_course("testnettoyageF", "testnettoyageF", 1)[0]["id"]
    courseI_testprof_id = webservice.create_course("testnettoyageI", "testnettoyageI", 1)[0]["id"]
    courseJ_testprof_id = webservice.create_course("testnettoyageJ", "testnettoyageJ", 1)[0]["id"]
    courseM_testprof_id = webservice.create_course("testnettoyageM", "testnettoyageM", 1)[0]["id"]
    courseN_testprof_id = webservice.create_course("testnettoyageN", "testnettoyageN", 1)[0]["id"]
    temp["courses"].extend([courseA_testprof_id,courseB_testprof_id,courseE_testprof_id,courseF_testprof_id,\
    courseI_testprof_id,courseJ_testprof_id,courseM_testprof_id,courseN_testprof_id])

    #Inscription des utilisateurs aux cours factices
    #Inscriptions simples en tant qu'enseignant
    webservice.enrol_user_to_course(config.constantes.id_role_enseignant, profid_a, courseA_testprof_id)
    webservice.enrol_user_to_course(config.constantes.id_role_enseignant, profid_e, courseE_testprof_id)
    webservice.enrol_user_to_course(config.constantes.id_role_enseignant, profid_i, courseI_testprof_id)
    webservice.enrol_user_to_course(config.constantes.id_role_enseignant, profid_m, courseM_testprof_id)
    #Inscriptions en tant que propriétaire de cours
    webservice.enrol_user_to_course(config.constantes.id_role_proprietaire_cours, profid_b, courseB_testprof_id)
    webservice.enrol_user_to_course(config.constantes.id_role_proprietaire_cours, profid_f, courseF_testprof_id)
    webservice.enrol_user_to_course(config.constantes.id_role_proprietaire_cours, profid_j, courseJ_testprof_id)
    webservice.enrol_user_to_course(config.constantes.id_role_proprietaire_cours, profid_n, courseN_testprof_id)

    #Création de fausses références dans des cours
    refidprof_c = insert_fake_course_reference_enseignant(db, profid_c)
    refidprof_g = insert_fake_course_reference_enseignant(db, profid_g)
    refidprof_k = insert_fake_course_reference_enseignant(db, profid_k)
    refidprof_o = insert_fake_course_reference_enseignant(db, profid_o)
    temp["references"].extend([refidprof_c,refidprof_g,refidprof_k,refidprof_o])


def insert_fake_user(db: Database, username: str, first_name: str, last_name: str, email: str, mail_display: int, theme: str):
    """
    Fonction permettant d'insérer un utilisateur de test
    :returns: L'id de l'utilisateur inséré
    """
    db.insert_moodle_user(username, first_name, last_name, email, mail_display, theme)
    return db.get_user_id(username)

def remove_fake_user(db: Database, userid: int):
    """
    Fonction permettant de supprimer un utilisateur de test
    """
    s = "DELETE FROM {entete}user WHERE id = %(userid)s".format(entete=db.entete)
    db.mark.execute(s, params={'userid': userid})

def insert_fake_course_reference_eleve(db: Database, userid: int):
    """
    Fonction permettant de donner une référence à un utilisateur dans un cours
    On ne se préoccupe pas des dépendances car ici la table de l'historique des notes
    peut de toute manière faire référence à des cours qui n'éxistent plus
    """
    s = "INSERT INTO {entete}grade_grades_history (action, oldid, source, timemodified, loggeduser, itemid, userid, rawgrade, rawgrademax, rawgrademin, rawscaleid, usermodified, finalgrade, hidden, locked, locktime, exported, overridden, excluded, feedback, feedbackformat, information, informationformat) VALUES (1, 0, 'mod/assign', 0, 0, 0, %(userid)s, 50, 100.00000, 0.00000, NULL, NULL, NULL, 0, 0, 0, 0, 0, 0, NULL, 0, NULL, 0)".format(entete=db.entete)
    db.mark.execute(s, params={'userid': userid})
    return db.mark.lastrowid

def insert_fake_course_reference_enseignant(db: Database, userid: int):
    """
    Fonction permettant de donner une référence à un utilisateur dans un cours
    On ne se préoccupe pas des dépendances car ici la table de l'historique des notes
    peut de toute manière faire référence à des cours qui n'éxistent plus
    """
    s = "INSERT INTO {entete}grade_grades_history (action, oldid, source, timemodified, loggeduser, itemid, userid, rawgrade, rawgrademax, rawgrademin, rawscaleid, usermodified, finalgrade, hidden, locked, locktime, exported, overridden, excluded, feedback, feedbackformat, information, informationformat) VALUES (1, 0, 'mod/assign', 0, 0, 0, %(userid)s, 50, 100.00000, 0.00000, NULL, NULL, NULL, 0, 0, 0, 0, 0, 0, NULL, 0, NULL, 0)".format(entete=db.entete)
    db.mark.execute(s, params={'userid': userid})
    return db.mark.lastrowid

def remove_fake_course_reference(db: Database, id: str):
    """
    Fonction permettant de supprimer une référence de cours de test
    """
    s = "DELETE FROM {entete}grade_grades_history WHERE id =  %(id)s".format(entete=db.entete)
    db.mark.execute(s, params={'id': id})

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
