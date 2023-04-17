from synchromoodle.dbutils import Database
from synchromoodle.config import Config
from synchromoodle.webserviceutils import WebService
from argparse import Namespace

SECONDS_PER_DAY = 86400
ID_TEST_CATEGORY = 1

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

def is_course_deleted(db: Database, shortname: str):
    """
    Teste si un cours est supprimé de la base de données moodle
    :param shortname: Le nom du cours (pour pouvoir l'identifier)
    :returns: Un booléen à True si l'utilisateur n'est plus dans la base de données, False sinon
    """
    return get_course_count_by_shortname(db, shortname) == 0


def insert_eleves(db: Database, config: Config, arguments: Namespace, temp: dict[str, list[int]], webservice: WebService):
    """
    Insérère toutes les données nécéssaisres aux tests
    des élèves dans la base de données moodle
    """
    #Récupération du timestamp actuel
    now = db.get_timestamp_now()

    #Insertion des utilisateurs de test (élèves)
    eleveid_a = insert_fake_user(db, "F1700tsa", "testeleve", "A", "testeleve.A@netocentre.fr", 2, "0290009c")
    eleveid_b = insert_fake_user(db, "F1700tsb", "testeleve", "B", "testeleve.B@netocentre.fr", 2, "0290009c")
    eleveid_c = insert_fake_user(db, "F1700tsc", "testeleve", "C", "testeleve.C@netocentre.fr", 2, "0290009c")
    eleveid_d = insert_fake_user(db, "F1700tsd", "testeleve", "D", "testeleve.D@netocentre.fr", 2, "0290009c")
    eleveid_e = insert_fake_user(db, "F1700tse", "testeleve", "E", "testeleve.E@netocentre.fr", 2, "0290009c")
    eleveid_f = insert_fake_user(db, "F1700tsf", "testeleve", "F", "testeleve.F@netocentre.fr", 2, "0290009c")
    eleveid_g = insert_fake_user(db, "F1700tsg", "testeleve", "G", "testeleve.G@netocentre.fr", 2, "0290009c")
    eleveid_h = insert_fake_user(db, "F1700tsh", "testeleve", "H", "testeleve.H@netocentre.fr", 2, "0290009c")
    eleveid_i = insert_fake_user(db, "F1700tsi", "testeleve", "I", "testeleve.I@netocentre.fr", 2, "0290009c")
    eleveid_j = insert_fake_user(db, "F1700tsj", "testeleve", "J", "testeleve.J@netocentre.fr", 2, "0290009c")
    eleveid_k = insert_fake_user(db, "F1700tsk", "testeleve", "K", "testeleve.K@netocentre.fr", 2, "0290009c")
    eleveid_l = insert_fake_user(db, "F1700tsl", "testeleve", "L", "testeleve.L@netocentre.fr", 2, "0290009c")
    eleveid_m = insert_fake_user(db, "F1700tsm", "testeleve", "M", "testeleve.M@netocentre.fr", 2, "0290009c")
    temp["eleves"].extend([eleveid_a,eleveid_b,eleveid_c,eleveid_d,eleveid_e,eleveid_f,eleveid_g,eleveid_h,\
    eleveid_i,eleveid_j,eleveid_k,eleveid_l,eleveid_m])

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
    course_test_id = webservice.create_course("testnettoyage", "testnettoyage", 1)[0]["id"]
    temp["courses"].append(course_test_id)

    #Inscription des utilisateurs aux cours factices
    webservice.enrol_user_to_course(config.constantes.id_role_eleve, eleveid_a, course_test_id)
    webservice.enrol_user_to_course(config.constantes.id_role_eleve, eleveid_d, course_test_id)
    webservice.enrol_user_to_course(config.constantes.id_role_eleve, eleveid_k, course_test_id)
    webservice.enrol_user_to_course(config.constantes.id_role_eleve, eleveid_j, course_test_id)

    #Création de fausses références dans des cours
    refid_b = insert_fake_course_reference_eleve(db, eleveid_b)
    refid_d = insert_fake_course_reference_eleve(db, eleveid_d)
    refid_h = insert_fake_course_reference_eleve(db, eleveid_h)
    refid_l = insert_fake_course_reference_eleve(db, eleveid_l)
    temp["references"].extend([refid_b,refid_d,refid_h,refid_l])

    #Mise à jour BD
    db.connection.commit()


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
    courseA_testprof_id = webservice.create_course("testnettoyageA", "testnettoyageA", ID_TEST_CATEGORY)[0]["id"]
    courseB_testprof_id = webservice.create_course("testnettoyageB", "testnettoyageB", ID_TEST_CATEGORY)[0]["id"]
    courseE_testprof_id = webservice.create_course("testnettoyageE", "testnettoyageE", ID_TEST_CATEGORY)[0]["id"]
    courseF_testprof_id = webservice.create_course("testnettoyageF", "testnettoyageF", ID_TEST_CATEGORY)[0]["id"]
    courseI_testprof_id = webservice.create_course("testnettoyageI", "testnettoyageI", ID_TEST_CATEGORY)[0]["id"]
    courseJ_testprof_id = webservice.create_course("testnettoyageJ", "testnettoyageJ", ID_TEST_CATEGORY)[0]["id"]
    courseM_testprof_id = webservice.create_course("testnettoyageM", "testnettoyageM", ID_TEST_CATEGORY)[0]["id"]
    courseN_testprof_id = webservice.create_course("testnettoyageN", "testnettoyageN", ID_TEST_CATEGORY)[0]["id"]
    temp["courses"].extend([courseA_testprof_id,courseB_testprof_id,courseE_testprof_id,courseF_testprof_id,\
    courseI_testprof_id,courseJ_testprof_id,courseM_testprof_id,courseN_testprof_id])

    #Changement des dates de dernière modification des cours
    update_timemodified_course(db, courseJ_testprof_id, 0)
    update_timemodified_course(db, courseN_testprof_id, 0)

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

    #Mise à jour BD
    db.connection.commit()


def insert_courses(db: Database, config: Config, arguments: Namespace, temp: dict[str, list[int]], webservice: WebService):
    """
    Insérère toutes les données nécéssaisres aux tests
    des élèves dans la base de données moodle
    """
    #Récupération du timestamp actuel
    now = db.get_timestamp_now()

    #Création des cours de test
    course1_id = webservice.create_course("testnettoyage1", "testnettoyage1", ID_TEST_CATEGORY)[0]["id"]
    course2_id = webservice.create_course("testnettoyage2", "testnettoyage2", ID_TEST_CATEGORY)[0]["id"]
    course3_id = webservice.create_course("testnettoyage3", "testnettoyage3", ID_TEST_CATEGORY)[0]["id"]
    course4_id = webservice.create_course("testnettoyage4", "testnettoyage4", ID_TEST_CATEGORY)[0]["id"]
    course5_id = webservice.create_course("testnettoyage5", "testnettoyage5", ID_TEST_CATEGORY)[0]["id"]
    course6_id = webservice.create_course("testnettoyage6", "testnettoyage6", ID_TEST_CATEGORY)[0]["id"]
    temp["courses"].extend([course1_id,course2_id,course3_id,course4_id,course5_id,course6_id])

    #Création d'utilisateurs factices à inscire dans les cours pour pouvoir vérifier les traitements sur les cours
    profid_x = insert_fake_user(db, "F1700ttx", "testprof", "X", "testprof.X@netocentre.fr", 2, "0290009c")
    profid_y = insert_fake_user(db, "F1700tty", "testprof", "Y", "testprof.Y@netocentre.fr", 2, "0290009c")
    id_context_test_category = db.get_id_context_categorie(ID_TEST_CATEGORY)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_x)
    db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_test_category, profid_y)
    update_lastlogin_user(db, profid_x, now - (config.delete.delay_backup_course + 1) * SECONDS_PER_DAY)
    update_lastlogin_user(db, profid_y, now)
    temp["profs"].extend([profid_x, profid_y])

    #Mise à jour BD
    db.connection.commit()

    #Inscription des enseignants factices dans les différents cours
    webservice.enrol_user_to_course(config.constantes.id_role_proprietaire_cours, profid_x, course1_id)
    webservice.enrol_user_to_course(config.constantes.id_role_proprietaire_cours, profid_x, course2_id)
    webservice.enrol_user_to_course(config.constantes.id_role_enseignant, profid_x, course3_id)
    webservice.enrol_user_to_course(config.constantes.id_role_proprietaire_cours, profid_x, course4_id)
    webservice.enrol_user_to_course(config.constantes.id_role_proprietaire_cours, profid_x, course5_id)
    webservice.enrol_user_to_course(config.constantes.id_role_enseignant, profid_x, course6_id)
    webservice.enrol_user_to_course(config.constantes.id_role_proprietaire_cours, profid_y, course2_id)
    webservice.enrol_user_to_course(config.constantes.id_role_proprietaire_cours, profid_y, course3_id)
    webservice.enrol_user_to_course(config.constantes.id_role_proprietaire_cours, profid_y, course5_id)
    webservice.enrol_user_to_course(config.constantes.id_role_proprietaire_cours, profid_y, course6_id)

    #Changement des dates de dernière modification des cours
    update_timemodified_course(db, course1_id, now)
    update_timemodified_course(db, course2_id, now)
    update_timemodified_course(db, course3_id, now)
    update_timemodified_course(db, course4_id, now - (config.delete.delay_backup_course + 1) * SECONDS_PER_DAY)
    update_timemodified_course(db, course5_id, now - (config.delete.delay_backup_course + 1) * SECONDS_PER_DAY)
    update_timemodified_course(db, course6_id, now - (config.delete.delay_backup_course + 1) * SECONDS_PER_DAY)

    #Mise à jour BD
    db.connection.commit()


def get_course_count_by_shortname(db: Database, shortname: str):
    """
    Récupère les informations sur un cours donné
    :param shortname: Le nom court du cours recherché
    :return:
    """
    s = "SELECT count(*) FROM {entete}course WHERE shortname = %(shortname)s".format(entete=db.entete)
    db.mark.execute(s, params={'shortname': shortname})
    ligne = db.safe_fetchone()
    return ligne[0]

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
    Fonction permettant de donner une référence à un élève dans un cours
    On ne se préoccupe pas des dépendances car ici la table de l'historique des notes
    peut de toute manière faire référence à des cours qui n'éxistent plus
    """
    s = "INSERT INTO {entete}grade_grades_history (action, oldid, source, timemodified, loggeduser, itemid, userid, rawgrade, rawgrademax, rawgrademin, rawscaleid, usermodified, finalgrade, hidden, locked, locktime, exported, overridden, excluded, feedback, feedbackformat, information, informationformat) VALUES (1, 0, 'mod/assign', 0, 0, 0, %(userid)s, 50, 100.00000, 0.00000, NULL, NULL, NULL, 0, 0, 0, 0, 0, 0, NULL, 0, NULL, 0)".format(entete=db.entete)
    db.mark.execute(s, params={'userid': userid})
    return db.mark.lastrowid

def insert_fake_course_reference_enseignant(db: Database, loggeduser: int):
    """
    Fonction permettant de donner une référence à un enseignant dans un cours
    On ne se préoccupe pas des dépendances car ici la table de l'historique des notes
    peut de toute manière faire référence à des cours qui n'éxistent plus
    """
    s = "INSERT INTO {entete}grade_grades_history (action, oldid, source, timemodified, loggeduser, itemid, userid, rawgrade, rawgrademax, rawgrademin, rawscaleid, usermodified, finalgrade, hidden, locked, locktime, exported, overridden, excluded, feedback, feedbackformat, information, informationformat) VALUES (1, 0, 'mod/assign', 0, %(loggeduser)s, 0, 0, 50, 100.00000, 0.00000, NULL, NULL, NULL, 0, 0, 0, 0, 0, 0, NULL, 0, NULL, 0)".format(entete=db.entete)
    db.mark.execute(s, params={'loggeduser': loggeduser})
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

def update_timemodified_course(db, courseid: int, timemodified):
    """
    Fonction permettant de mettre a jour la date de dernière modification d'un cours
    :param db: L'objet Database représentant la base de données moodle
    :param courseid: L'id du cours à modifier
    :param timemodified: Le timestamp (en s) représentant la date de dernière modification du cours
    :return:
    """
    s = "UPDATE {entete}course SET timemodified = %(timemodified)s WHERE id = %(courseid)s".format(entete=db.entete)
    db.mark.execute(s, params={'timemodified': timemodified, 'courseid': courseid})
