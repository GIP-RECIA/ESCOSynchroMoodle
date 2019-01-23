# coding: utf-8

import logging
import re
import sys

from synchromoodle.majutils import Synchronizer
from synchromoodle.timestamp import TimestampStore

logging.basicConfig(format='%(levelname)s:%(message)s', stream=sys.stdout, level=logging.INFO)

from .dbutils import Database
from .config import EtablissementsConfig, Config
from .ldaputils import Ldap


def estGrpEtab(rne: str, etablissements_config: EtablissementsConfig):
    """
    Indique si un établissement fait partie d'un regroupement d'établissement ou non
    :param rne: code de l'établissement
    :param etablissements_config: EtablissementsConfig
    :return: True si l'établissement fait partie d'un regroupement d'établissement
    """
    for regroupement in etablissements_config.etabRgp:
        if rne in regroupement.UaiRgp:
            return regroupement
    return False


######################################################################
# Fonction permettant de mettre a jour les droits d'un enseignant.
# Cette mise a jour consiste a :
#   - Supprimer les roles non autorises
#   - ajouter les roles
######################################################################
def mettre_a_jour_droits_enseignant(db, enseignant_infos, gereAdminLocal, id_enseignant, id_context_categorie,
                                    id_context_course_forum, uais_autorises):
    # Recuperation des themes autorises pour l'enseignant
    themes_autorises = [uai_autorise.lower() for uai_autorise in uais_autorises]
    logging.debug(
        "      |_ Etablissements autorises pour l'enseignant pour %s : %s" % (enseignant_infos, str(themes_autorises)))

    #########################
    # ZONES PRIVEES
    #########################
    # Recuperation des ids des roles et les themes non autorises
    ids_roles_non_autorises, ids_themes_non_autorises = db.get_ids_and_themes_not_allowed_roles(id_enseignant,
                                                                                                themes_autorises)

    # Suppression des roles non autorises
    if ids_roles_non_autorises:
        db.delete_roles(ids_roles_non_autorises)
        logging.info("      |_ Suppression des rôles d'enseignant pour %s dans les établissements %s" % (
            enseignant_infos, str(ids_themes_non_autorises)))
        logging.info("         Les seuls établissements autorisés pour cet enseignant sont %s" % str(themes_autorises))

    #########################
    # FORUMS
    #########################
    # Recuperation des SIREN des etablissements dans lequel l'enseignant travaille
    sirens = db.get_descriptions_course_categories_by_themes(themes_autorises)

    # Shortname des forums associes
    # Modification RECIA pour erreur d'encodage : "UnicodeEncodeError: 'ascii' codec can't encode character u'\xe9' in position 41: ordinal not in range(128)"
    # CD - 18/09/2015
    # Ancien code : shortnames_forums = [ ( "ZONE-PRIVEE-%s" % str( siren ) ) for siren in sirens ]
    shortnames_forums = [("ZONE-PRIVEE-%s" % str(siren.encode("utf-8"))) for siren in sirens]

    # Recuperation des roles sur les forums qui ne devraient plus exister
    ids_roles_non_autorises, forums_summaries = db.get_ids_and_summaries_not_allowed_roles(id_enseignant,
                                                                                           shortnames_forums)

    # Suppression des roles non autorises
    if ids_roles_non_autorises:
        # Suppression des roles
        db.delete_roles(ids_roles_non_autorises)
        logging.info("      |_ Suppression des rôles d'enseignant pour %s sur les forum '%s' " % (
            enseignant_infos, str(forums_summaries)))
        logging.info("         Les seuls établissements autorisés pour cet enseignant sont '%s'" % themes_autorises)


def miseAJour(config: Config, purge_cohortes: bool):
    """
    Execute la mise à jour de la base de données Moodle à partir des informations du LDAP.

    :param config: Configuration d'execution
    :param purge_cohortes: True si la purge des cohortes doit etre effectuée
    """
    try:
        logging.info('============================================')
        logging.info('Synchronisation établissements : DEBUT')

        db = Database(config.database, config.constantes)

        ldap = Ldap(config.ldap)

        synchronizer = Synchronizer(ldap, db, config)

        # Récupération de la liste UAI-Domaine des établissements
        synchronizer.context.map_etab_domaine = ldap.get_domaines_etabs()

        # Ids des categories inter etablissements
        id_context_categorie_inter_etabs = db.get_id_context_inter_etabs()

        id_categorie_inter_cfa = db.get_id_categorie_inter_etabs(config.etablissements.inter_etab_categorie_name_cfa)
        id_context_categorie_inter_cfa = db.get_id_context_categorie(id_categorie_inter_cfa)

        # Recuperation des ids des roles admin local et extended teacher
        id_role_admin_local = db.get_id_role_admin_local()
        id_role_extended_teacher = db.get_id_role_extended_teacher()

        # Recuperation des ids du role d'utilisateur avancé
        id_role_advanced_teacher = db.get_id_role_advanced_teacher()

        # Recuperation du timestamp actuel
        maintenant_sql = db.get_timestamp_now()

        # Recuperation de l'id du user info field pour la classe
        synchronizer.context.id_user_info_field_classe = db.get_id_user_info_field_classe()
        if synchronizer.context.id_user_info_field_classe is None:
            db.insert_moodle_user_info_field_classe()
            synchronizer.context.id_user_info_field_classe = db.get_id_user_info_field_classe()

        # Recuperation de l'id du champ personnalisé Domaine
        synchronizer.context.id_field_domaine = db.get_field_domaine()

        ###################################################
        # On ne va traiter, dans la suite du programme, 
        # que les utilisateurs ayant subi
        # une modification depuis le dernier traitement 
        ###################################################
        # Recuperation des dates de traitement precedent par etablissement
        timestamp_store = TimestampStore(config.timestamp_store)

        ###################################################
        # Traitement etablissement par etablissement afin 
        # d'éviter la remontée de trop d'occurences du LDAP
        ###################################################
        for uai in config.etablissements.listeEtab:
            etablissement_context = synchronizer.mise_a_jour_etab(uai)

            ####################################
            # Mise a jour des eleves 
            ####################################
            logging.info('    |_ Mise à jour des eleves')

            # Date du dernier traitement effectue
            time_stamp = timestamp_store.get_timestamp(uai)
            if purge_cohortes:
                # Si la purge des cohortes a ete demandee
                # On recupere tous les eleves sans prendre en compte le timestamp
                time_stamp = None

            # Traitement des eleves
            for ldap_student in ldap.search_student(time_stamp, uai):
                synchronizer.mise_a_jour_eleve(etablissement_context, ldap_student)

            # Purge des cohortes des eleves
            if purge_cohortes:
                logging.info('    |_ Purge des cohortes des élèves')
                db.purge_cohorts(etablissement_context.eleves_by_cohortes)

            ####################################
            # Mise a jour des enseignants
            ####################################
            logging.info('    |_ Mise à jour du personnel enseignant')

            time_stamp = timestamp_store.get_timestamp(uai)

            # Traitement des enseignants
            for ldap_teacher in ldap.search_teacher(since_timestamp=time_stamp, uai=uai):
                enseignant_infos = "%s %s %s" % (ldap_teacher.uid, ldap_teacher.given_name, ldap_teacher.sn)

                if ldap_teacher.uai_courant and not etablissement_context.etablissement_regroupe:
                    etablissement_context.etablissement_theme = ldap_teacher.uai_courant.lower()

                if not ldap_teacher.mail:
                    ldap_teacher.mail = config.constantes.default_mail

                # Affichage du mail reserve aux membres de cours
                mail_display = config.constantes.default_mail_display
                if etablissement_context.ldap_structure.uai in config.etablissements.listeEtabSansMail:
                    # Desactivation de l'affichage du mail
                    mail_display = 0

                # Insertion de l'enseignant
                id_user = db.get_user_id(ldap_teacher.uid)
                if not id_user:
                    db.insert_moodle_user(ldap_teacher.uid, ldap_teacher.given_name, ldap_teacher.sn, ldap_teacher.mail,
                                          mail_display, etablissement_context.etablissement_theme)
                    id_user = db.get_user_id(ldap_teacher.uid)
                else:
                    db.update_moodle_user(id_user, ldap_teacher.given_name, ldap_teacher.sn, ldap_teacher.mail,
                                          mail_display,
                                          etablissement_context.etablissement_theme)

                # Mise ajour des droits sur les anciens etablissement
                if ldap_teacher.uais is not None and not etablissement_context.etablissement_regroupe:
                    # Recuperation des uais des etablissements dans lesquels l'enseignant est autorise
                    mettre_a_jour_droits_enseignant(db, enseignant_infos,
                                                    etablissement_context.gereAdminLocal,
                                                    etablissement_context.id_context_categorie,
                                                    etablissement_context.id_context_course_forum,
                                                    id_user,
                                                    ldap_teacher.uais)

                # Ajout du role de createur de cours au niveau de la categorie inter-etablissement Moodle
                db.add_role_to_user(config.constantes.id_role_createur_cours,
                                    id_context_categorie_inter_etabs,
                                    id_user)
                logging.info("        |_ Ajout du role de createur de cours dans la categorie inter-etablissements")

                # Si l'enseignant fait partie d'un CFA
                # Ajout du role createur de cours au niveau de la categorie inter-cfa
                if etablissement_context.ldap_structure.type == config.constantes.type_structure_cfa:
                    db.add_role_to_user(config.constantes.id_role_createur_cours,
                                        id_context_categorie_inter_cfa, id_user)
                    logging.info("        |_ Ajout du role de createur de cours dans la categorie inter-cfa")

                # ajout du role de createur de cours dans l'etablissement
                db.add_role_to_user(config.constantes.id_role_createur_cours, etablissement_context.id_context_categorie, id_user)

                # Ajouts des autres roles pour le personnel établissement
                if 'National_3' in ldap_teacher.profils or 'National_5' in ldap_teacher.profils or 'National_6' in ldap_teacher.profils or 'National_4' in ldap_teacher.profils:
                    # Ajout des roles sur le contexte forum
                    db.add_role_to_user(config.constantes.id_role_eleve, etablissement_context.id_context_course_forum, id_user)
                    # Inscription à la Zone Privée
                    db.enroll_user_in_course(config.constantes.id_role_eleve, etablissement_context.id_zone_privee, id_user)

                    if 'National_3' in ldap_teacher.profils or 'National_5' in ldap_teacher.profils or 'National_6' in ldap_teacher.profils:
                        if not etablissement_context.gereAdminLocal:
                            db.add_role_to_user(id_role_extended_teacher, etablissement_context.id_context_categorie, id_user)
                    elif 'National_4' in ldap_teacher.profils:
                        db.add_role_to_user(config.constantes.id_role_directeur, etablissement_context.id_context_categorie, id_user)

                # Ajout des droits d'administration locale pour l'etablissement
                if etablissement_context.gereAdminLocal:
                    for member in ldap_teacher.is_member_of:
                        # L'enseignant est il administrateur Moodle ?
                        adminMoodle = re.match(etablissement_context.regexpAdminMoodle, member, flags=re.IGNORECASE)
                        if adminMoodle:
                            insert = db.insert_moodle_local_admin(etablissement_context.id_context_categorie, id_user)
                            if insert:
                                logging.info("      |_ Insertion d'un admin  local %s %s %s" % (
                                    ldap_teacher.uid, ldap_teacher.given_name, ldap_teacher.sn))
                            # Si il est adminin local on en fait un utilisateur avancé par default
                            if not db.is_enseignant_avance(id_user, id_role_advanced_teacher):
                                db.add_role_to_user(id_role_advanced_teacher, 1, id_user)
                            break
                        else:
                            delete = db.delete_moodle_local_admin(id_context_categorie_inter_etabs, id_user)
                            if delete:
                                logging.info("      |_ Suppression d'un admin local %s %s %s" % (
                                    ldap_teacher.uid, ldap_teacher.given_name, ldap_teacher.sn))

                # Mise a jour du Domaine
                user_domain = config.constantes.default_domain
                if len(ldap_teacher.domaines) == 1:
                    user_domain = ldap_teacher.domaines[0]
                else:
                    if ldap_teacher.uai_courant and ldap_teacher.uai_courant in synchronizer.context.map_etab_domaine:
                        user_domain = synchronizer.context.map_etab_domaine[ldap_teacher.uai_courant][0]
                logging.debug("Insertion du Domaine")
                db.set_user_domain(id_user, synchronizer.context.id_field_domaine, user_domain)
        if purge_cohortes:
            # Si la purge des cohortes a ete demandee
            # On recupere tous les eleves sans prendre en compte le timestamp
            time_stamp = None
        # CREATION DES COHORTES DE PROFS
        db.create_profs_etabs_cohorts(etablissement_context.id_context_categorie, uai, maintenant_sql, time_stamp, ldap)

        db.connection.commit()

        timestamp_store.mark(uai)
        timestamp_store.write()

        logging.info('Synchronisation établissements : FIN')
        logging.info('============================================')
    except Exception as err:
        logging.exception("An exception has been thrown")
        # logging.exception("Something went bad during the connection:\n", err)
        sys.exit(2)

    db.disconnect()


def miseAJourInterEtabs(config: Config, purge_cohortes: bool):
    """
    Effectue la mise a jour de la BD Moodle via les infos issues du LDAP

    Cette mise a jour concerne les utilisateurs et administrateurs inter-etablissements

    :param config: Configuration d'execution
    :param purge_cohortes: 
    :return: 
    """
    try:
        logging.info("  |_ Traitement de l'inter-établissements")

        db = Database(config.database, config.constantes)

        ###################################################
        # Connexion a la BD Moodle et recuperation 
        # d'informations
        ###################################################

        # Recuperation du timestamp actuel
        maintenant_sql = db.get_timestamp_now()

        ###################################################
        # Connexion au LDAP
        ###################################################
        ldap = Ldap(config.ldap)

        ###################################################
        # Recuperation de la date de dernier traitement
        ###################################################
        timestamp_store = TimestampStore(config.timestamp_store)

        ###################################################
        # Mise a jour des utilisateurs inter-etabs
        ###################################################
        logging.info('    |_ Mise à jour des utilisateurs inter-etablissements')

        list_moodle_not_admin = []

        id_categorie_inter_etabs = db.get_id_categorie_inter_etabs(config.inter_etablissements.categorie_name)
        id_context_categorie_inter_etabs = db.get_id_context_categorie(id_categorie_inter_etabs)

        people_filter = {config.users.ldap_attribut_user: config.users.ldap_valeur_attribut_user}

        # Traitement des eleves
        for ldap_people in ldap.search_people(since_timestamp=timestamp_store.current_timestamp, **people_filter):
            if not ldap_people.mail:
                ldap_people.mail = config.constantes.default_mail

            # Creation de l'utilisateur
            id_user = db.get_user_id(ldap_people.uid)
            if not id_user:
                db.insert_moodle_user(ldap_people.uid, ldap_people.given_name, ldap_people.sn, ldap_people.mail,
                                      config.constantes.default_mail_display, config.constantes.default_moodle_theme)
                id_user = db.get_user_id(ldap_people.uid)
            else:
                db.update_moodle_user(id_user, ldap_people.given_name, ldap_people.sn, ldap_people.mail,
                                      config.constantes.default_mail_display, config.constantes.default_moodle_theme)

            # Ajout du role de createur de cours 
            db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_categorie_inter_etabs, id_user)

            # Attribution du role admin local si necessaire
            for member in ldap_people.is_member_of:
                admin = re.match(config.users.ldap_valeur_attribut_admin, member, flags=re.IGNORECASE)
                if admin:
                    insert = db.insert_moodle_local_admin(id_context_categorie_inter_etabs, id_user)
                    if insert:
                        logging.info(
                            "      |_ Insertion d'un admin local %s %s %s" % (
                                ldap_people.uid, ldap_people.given_name, ldap_people.sn))
                    break
                else:
                    delete = db.delete_moodle_local_admin(id_context_categorie_inter_etabs, id_user)
                    if delete:
                        logging.info("      |_ Suppression d'un admin local %s %s %s" % (
                            ldap_people.uid, ldap_people.given_name, ldap_people.sn))

        ###################################################
        # Mise a jour des cohortes inter-etabs
        ###################################################
        logging.info('    |_ Mise à jour des cohortes de la categorie inter-etablissements')

        # Si la purge des cohortes a ete demandee
        if purge_cohortes:
            # On ignore le time stamp afin de traiter tous les utilisateurs
            time_stamp = None

        # Dictionnaires permettant de sauvegarder les eleves inscrits
        # dans les cohortes, pour une eventuelle purge
        utilisateurs_by_cohortes = {}

        # Mise a jour de chaque cohorte declaree
        for is_member_of, cohort_name in config.inter_etablissements.cohorts.items():
            # Creation de la cohort si necessaire
            db.create_cohort(id_context_categorie_inter_etabs, cohort_name, cohort_name, cohort_name, maintenant_sql)
            id_cohort = db.get_id_cohort(id_context_categorie_inter_etabs, cohort_name)

            # Liste permettant de sauvegarder les utilisateurs de la cohorte
            utilisateurs_by_cohortes[id_cohort] = []

            # Recuperation des utilisateurs
            is_member_of_list = [is_member_of]

            # Ajout des utilisateurs dans la cohorte
            for ldap_people in ldap.search_people(since_timestamp=time_stamp, isMemberOf=is_member_of_list):
                people_infos = "%s %s %s" % (ldap_people.uid, ldap_people.given_name, ldap_people.sn)

                people_id = db.get_user_id(ldap_people.uid)
                if people_id:
                    db.enroll_user_in_cohort(id_cohort, people_id, people_infos, maintenant_sql)
                    # Mise a jour des utilisateurs de la cohorte
                    utilisateurs_by_cohortes[id_cohort].append(people_id)
                else:
                    message = "      |_ Impossible d'inserer l'utilisateur %s dans la cohorte %s, car il n'est pas connu dans Moodle"
                    message = message % (people_infos, cohort_name.decode("utf-8"))
                    logging.warning(message)

        # Purge des cohortes des eleves
        if purge_cohortes:
            logging.info('    |_ Purge des cohortes de la catégorie inter-établissements')
            db.purge_cohorts(utilisateurs_by_cohortes)

        db.connection.commit()
        db.disconnect()

        # Mise a jour de la date de dernier traitement
        timestamp_store.mark(config.inter_etablissements.cle_timestamp)
        timestamp_store.write()

    except Exception as err:
        logging.exception("An exception has been thrown");
        logging.exception("Something went bad during the connection:\n", err)
        sys.exit(2)


def miseAJourInspecteurs(config: Config):
    """
    Effectue la mise a jour de la BD

    Moodle via les infos issues du LDAP

    Cette mise a jour concerne les inspecteurs

    :param config: Configuration d'execution
    """
    try:
        logging.info('============================================')
        logging.info('Synchronisation des inspecteurs : DEBUT')
        logging.info("  |_ Traitement des inspecteurs")

        ###################################################
        # Connexion a la BD Moodle et recuperation 
        # d'informations
        ###################################################
        db = Database(config.database, config.constantes)

        ###################################################
        # Connexion au LDAP
        ###################################################
        ldap = Ldap(config.ldap)

        ###################################################
        # Mise a jour des inspecteurs
        ###################################################
        logging.info('    |_ Mise à jour des inspecteurs')

        # Recuperation de l'id du champ personnalisé Domaine
        id_field_domaine = db.get_field_domaine()

        # Récupération de la liste UAI-Domaine des établissements
        map_etab_domaine = ldap.get_domaines_etabs()

        # TODO : gerer le time_stamp
        time_stamp = None

        # Recuperation de l'id du contexte correspondant à la categorie inter_etabs
        id_context_categorie_inter_etabs = db.get_id_context_inter_etabs()

        people_filter = {config.users.ldap_attribut_user: config.users.ldap_valeur_attribut_user}

        # Traitement des inspecteurs
        for ldap_people in ldap.search_people(time_stamp, **people_filter):
            if not ldap_people.mail:
                ldap_people.mail = config.constantes.default_mail

            # Creation de l'utilisateur
            db.insert_moodle_user(ldap_people.uid, ldap_people.given_name, ldap_people.sn, ldap_people.mail,
                                  config.constantes.default_mail_display, config.constantes.default_moodle_theme)
            id_user = db.get_user_id(ldap_people.uid)
            if not id_user:
                db.insert_moodle_user(ldap_people.uid, ldap_people.given_name, ldap_people.sn, ldap_people.mail,
                                      config.constantes.default_mail_display, config.constantes.default_moodle_theme)
                id_user = db.get_user_id(ldap_people.uid)
            else:
                db.update_moodle_user(id_user, ldap_people.given_name, ldap_people.sn, ldap_people.mail,
                                      config.constantes.default_mail_display, config.constantes.default_moodle_theme)

            # Ajout du role de createur de cours au niveau de la categorie inter-etablissement Moodle
            db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_categorie_inter_etabs, id_user)
            logging.info("        |_ Ajout du role de createur de cours dans la categorie inter-etablissements")

            # if 'ESCOUAICourant' in ldap_entry_infos:
            # people_structure_uai  = ldap_entry_infos['ESCOUAICourant'][0].lower()

            # Recuperation de l'id du contexte correspondant à l'etablissement de l'inspecteur
            # id_etab_categorie = get_id_course_category_by_theme( mark, entete, people_structure_uai )

            # if id_etab_categorie is not None : 
            # id_context_categorie  = get_id_context_categorie( mark, entete, id_etab_categorie )
            # Ajout du role de createur de cours dans l'etablissement
            # add_role_to_user( mark, entete, ID_ROLE_CREATEUR_COURS, id_context_categorie, id_user )
            # logging.info( "        |_ Ajout du role de createur de cours dans l'etablissement de l'inspecteur" )

            # Ajout du role de personnel de direction dans l'etablissement
            # add_role_to_user( mark, entete, ID_ROLE_INSPECTEUR, id_context_categorie, id_user )
            # logging.info( "        |_ Ajout du role de personnel de direction dans l'établissement de l'inspecteur" )

            # Mise a jour du Domaine
            user_domain = config.constantes.default_domain
            if len(ldap_people.domaines) == 1:
                user_domain = ldap_people.domaines[0]
            else:
                if ldap_people.uai_courant and ldap_people.uai_courant in map_etab_domaine:
                    user_domain = map_etab_domaine[ldap_people.uai_courant][0]
            logging.debug("Insertion du Domaine")
            db.set_user_domain(id_user, id_field_domaine, user_domain)

        db.connection.commit()

        logging.info('Synchronisation des inspecteurs : FIN')
        logging.info('============================================')

    except Exception as err:
        logging.exception("An exception has been thrown")
        # logging.exception("Something went bad during the connection:\n", err)
        sys.exit(2)

    db.disconnect()


######################################################################
# Fonction permettant d'effectuer la mise a jour de la BD
# Moodle via les infos issues du LDAP
#
# Cette mise a jour concerne les utilisateurs de Mahara
#
# Parametres:
# -----------
#  - host     : hote hebergeant la BD moodle
#  - user     : utilisateur pour la connexion a la BD moodle
#  - password : mot de passe pour la connexion a la BD moodle
#  - nomBD    : nom de la BD moodle
#
#  - ldapServer   : hote hebergeant le serveur LDAP
#  - ldapUserName : utilisateur pour la connexion au LDAP
#  - ldapPassword : mot de passe pour la connexion au serveur LDAP
#
#  - personnesDN  : nom absolu pour acceder aux personnes dans le LDAP
#
#  - entete : entete des noms de table dans la BD moodle
#
#  - ldap_attribut_user : attribut LDAP utilise pour savoir si un utilisateur
#                         est un utilisateur de Mahara
#
#  - ldap_valeur_attribut_user : valeur de l'attribut LDAP permettant de savoir
#                                si un utilisateur est un utilisateur de Mahara
#  - purge            : booleen indiquant si la purge des utilisateurs
#                       doit etre effectuee, ou non
######################################################################
def miseAJourMahara(config: Config, purge):
    """
    Fonction permettant d'effectuer la mise a jour de la BD Moodle via les infos issues du LDAP.

    Cette mise a jour concerne les utilisateurs de Mahara.

    :param config: Configuration d'execution
    :param purge: True si la purge des utilisateurs doit être effectuée
    """
    try:
        logging.info('============================================')
        logging.info('Synchronisation des utilisateurs Mahara : DEBUT')
        logging.info("  |_ Traitement des utilisateurs Mahara")

        ###################################################
        # Connexion a la BD Moodle et recuperation 
        # d'informations
        ###################################################
        db = Database(config.database, config.constantes)

        ###################################################
        # Connexion au LDAP
        ###################################################
        ldap = Ldap(config.ldap)

        ###################################################
        # Recuperation de la date de dernier traitement
        ###################################################
        timestamp_store = TimestampStore(config.timestamp_store)

        ###################################################
        # Purge des utilisateurs de Mahara
        ###################################################
        # Si la purge a ete demandee
        if purge:
            # On ignore le time stamp afin de traiter tous les utilisateurs
            time_stamp = None
            # On enleve les roles aux utilisateurs de Mahara
            db.delete_all_mahara_roles()

        ###################################################
        # Mise a jour des utilisateurs
        ###################################################
        logging.info('    |_ Mise à jour des utilisateurs Mahara')

        people_filter = {config.users.ldap_attribut_user: config.users.ldap_valeur_attribut_user}

        # Traitement des inscpecteurs
        for ldap_people in ldap.search_people(since_timestamp=timestamp_store.current_timestamp, **people_filter):
            #  Recuperation des informations
            people_infos = "%s %s %s" % (ldap_people.uid, ldap_people.given_name, ldap_people.sn)

            # Recuperation de l'utilisateur en bd
            people_id = db.get_user_id(ldap_people.uid)

            # Si l'utilisateur n'est pas present dans Moodle
            if not people_id:
                message = "      |_ Impossible de donner les droits sur Mahara a %s, car il n'est pas connu dans Moodle"
                message = message % people_infos
                logging.warning(message)
                continue

            # Si l'utilisateur est present dans Moodle
            message = "      |_ Ajout du droit utilisateur de Mahara a %s"
            message = message % people_infos
            logging.info(message)
            db.add_role_mahara_to_user(people_id)

        db.connection.commit()

        # Mise a jour de la date de dernier traitement
        timestamp_store.mark(config.mahara.cle_timestamp)
        timestamp_store.write()

        logging.info('Synchronisation des utilisateurs Mahara : FIN')
        logging.info('============================================')

    except Exception as err:
        logging.exception("An exception has been thrown");
        logging.exception("Something went bad during the connection:\n", err)
        sys.exit(2)

    db.disconnect()
