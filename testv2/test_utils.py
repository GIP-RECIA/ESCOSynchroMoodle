from synchromoodle.dbutils import Database

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

def insert_fake_course_reference(db: Database, userid: int):
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
