# coding: utf-8

import logging
import re
import sys

from synchromoodle.timestamp import TimestampStore

logging.basicConfig(format='%(levelname)s:%(message)s', stream=sys.stdout, level=logging.INFO)

from .utilsDB import *
from .config import EtablissementsConfig, Config
from .ldaputils import Ldap


def estGrpEtab(rne: str, etablissements_config: EtablissementsConfig):
    """
    Indique si un établissement fait partie d'un regroupement d'établissement ou non
    :param rne: code de l'établissement
    :param config.etablissements: configuration
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
    ids_roles_non_autorises, forums_summaries = db.get_ids_and_summaries_not_allowed_roles(id_enseignant, shortnames_forums)

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

        db = Database(config.database)

        ldap = Ldap(config.ldap)

        # Récupération de la liste UAI-Domaine des établissements
        map_etab_domaine = ldap.get_domaines_etabs()

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
        id_user_info_field_classe = db.get_id_user_info_field_classe()
        if id_user_info_field_classe is None:
            db.insert_moodle_user_info_field_classe()
            id_user_info_field_classe = db.get_id_user_info_field_classe()

        # Recuperation de l'id du champ personnalisé Domaine
        id_field_domaine = db.get_field_domaine()

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

            logging.info("  |_ Traitement de l'établissement %s" % uai)

            gereAdminLocal = uai not in config.etablissements.listeEtabSansAdmin
            etablissement_regroupe = estGrpEtab(uai, config.etablissements)

            # Regex pour savoir si l'utilisateur est administrateur moodle
            regexpAdminMoodle = config.users.prefixAdminMoodleLocal + ".*_%s$" % uai

            # Regex pour savoir si l'utilisateur est administrateur local
            regexpAdminLocal = config.users.prefixAdminLocal + ".*_%s$" % uai

            ####################################
            # Mise a jour de l'etablissement 
            ####################################
            # On met a jour l'etablissement meme si celui-ci
            # n'a pas ete modifie depuis la derniere synchro
            # car des infos doivent etre recuperees dans Moodle 
            # dans tous les cas
            ldap_structures = ldap.search_structure(uai)

            for ldap_structure in ldap_structures:
                etablissement_path = "/1"

                # Si l'etablissement fait partie d'un groupement
                if etablissement_regroupe:
                    etablissement_ou = etablissement_regroupe["nom"]
                    ldap_structure.uai = etablissement_regroupe["uais"][0]
                else:
                    etablissement_ou = ldap_structure.nom

                # Recuperation du bon theme
                etablissement_theme = ldap_structure.uai.lower()

                # Creation de la structure si elle n'existe pas encore
                id_etab_categorie = db.get_id_course_category_by_theme(etablissement_theme)
                if id_etab_categorie is None:
                    db.insert_moodle_structure(etablissement_regroupe, ldap_structure.nom,
                                            etablissement_path,
                                            etablissement_ou, ldap_structure.siren, etablissement_theme)
                    id_etab_categorie = db.get_id_course_category_by_id_number(ldap_structure.siren)

                # Mise a jour de la description dans la cas d'un groupement d'etablissement
                if etablissement_regroupe:
                    description = db.get_description_course_category(id_etab_categorie)
                    if description.find(ldap_structure.siren) == -1:
                        description = "%s$%s@%s" % (description, ldap_structure.siren, ldap_structure.nom)
                        db.update_course_category_description(id_etab_categorie, description)
                        db.update_course_category_name(id_etab_categorie, etablissement_ou)

                # Recuperation de l'id du contexte correspondant à l'etablissement
                id_context_categorie = db.get_id_context_categorie(id_etab_categorie)
                id_zone_privee = db.get_id_course_by_id_number("ZONE-PRIVEE-" + ldap_structure.siren)

                # Recreation de la zone privee si celle-ci n'existe plus
                if id_zone_privee is None:
                    id_zone_privee = db.insert_zone_privee(id_etab_categorie, ldap_structure.siren,
                                                        etablissement_ou, maintenant_sql)

                id_context_course_forum = db.get_id_context(NIVEAU_CTX_COURS, 3, id_zone_privee)
                if id_context_course_forum is None:
                    id_context_course_forum = db.insert_zone_privee_context(id_zone_privee)

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

            # Recuperation du filtre ldap et recherche des eleves

            # Dictionnaires permettant de sauvegarder les eleves inscrits
            # dans les cohortes, pour une eventuelle purge
            eleves_by_cohortes = {}

            # Traitement des eleves
            for ldap_student in ldap.search_student(time_stamp, uai):
                #  Recuperation des informations

                eleve_infos = "%s %s %s" % (ldap_student.uid, ldap_student.given_name, ldap_student.sn)

                # Recuperation du mail
                mail_display = config.constantes.default_mail_display
                if not ldap_student.mail:
                    ldap_student.mail = config.constantes.default_mail

                # Insertion de l'eleve
                eleve_id = db.get_user_id(ldap_student.uid)
                if not eleve_id:
                    db.insert_moodle_user(ldap_student.uid, ldap_student.given_name,
                                       ldap_student.given_name, ldap_student.mail,
                                       mail_display,
                                       etablissement_theme)
                    eleve_id = db.get_user_id(ldap_student.uid)
                else:
                    db.update_moodle_user(eleve_id, ldap_student.given_name,
                                       ldap_student.given_name, ldap_student.mail,
                                       mail_display,
                                       etablissement_theme)

                # Ajout du role d'utilisateur avec droits limites
                # Pour les eleves de college
                if ldap_structure.type == config.constantes.type_structure_clg:
                    db.add_role_to_user(config.constantes.id_role_utilisateur_limite,
                                     config.constantes.id_instance_moodle,
                                     eleve_id)
                    logging.info(
                        "      |_ Ajout du role d'utilisateur avec des droits limites à l'utilisateur %s %s %s (id = %s)" % (
                            ldap_student.given_name, ldap_student.sn, ldap_student.uid, str(eleve_id)))

                # Inscription dans les cohortes associees aux classes
                eleve_cohorts = []
                if ldap_student.classes:
                    ids_classes_cohorts = db.create_classes_cohorts(id_context_categorie, ldap_student.classes,
                                                                 maintenant_sql)
                    db.enroll_user_in_cohorts(id_context_categorie, ids_classes_cohorts,
                                           eleve_id,
                                           eleve_infos, maintenant_sql)
                    eleve_cohorts.extend(ids_classes_cohorts)

                # Inscription dans la cohorte associee au niveau de formation
                if ldap_student.niveau_formation:
                    id_formation_cohort = db.create_formation_cohort(id_context_categorie, ldap_student.niveau_formation, maintenant_sql)
                    db.enroll_user_in_cohort(id_formation_cohort, eleve_id, eleve_infos, maintenant_sql)
                    eleve_cohorts.append(id_formation_cohort)

                # Desinscription des anciennes cohortes
                db.disenroll_user_from_cohorts(eleve_cohorts, eleve_id)

                # Mise a jour des dictionnaires concernant les cohortes
                for cohort_id in eleve_cohorts:
                    # Si la cohorte est deja connue
                    if cohort_id in eleves_by_cohortes:
                        eleves_by_cohortes[cohort_id].append(eleve_id)
                    # Si la cohorte n'a pas encore ete rencontree
                    else:
                        eleves_by_cohortes[cohort_id] = [eleve_id]

                # Mise a jour de la classe
                id_user_info_data = db.get_id_user_info_data(eleve_id, id_user_info_field_classe)
                if id_user_info_data is not None:
                    db.update_user_info_data(eleve_id, id_user_info_field_classe, ldap_student.classe)
                    logging.debug("Mise à jour user_info_data")
                else:
                    db.insert_moodle_user_info_data(eleve_id, id_user_info_field_classe, ldap_student.classe)
                    logging.debug("Insertion user_info_data")

                # Mise a jour du Domaine
                user_domain = config.constantes.default_domain
                if len(ldap_student.domaines) == 1:
                    user_domain = ldap_student.domaines[0]
                else:
                    if ldap_student.uai_courant and ldap_student.uai_courant in map_etab_domaine:
                        user_domain = map_etab_domaine[ldap_student.uai_courant][0]
                logging.debug("Insertion du Domaine")
                db.set_user_domain(eleve_id, id_field_domaine, user_domain)

            # Purge des cohortes des eleves
            if purge_cohortes:
                logging.info('    |_ Purge des cohortes des élèves')
                db.purge_cohorts(eleves_by_cohortes)

            ####################################
            # Mise a jour des enseignants
            ####################################
            logging.info('    |_ Mise à jour du personnel enseignant')

            time_stamp = timestamp_store.get_timestamp(uai)

            # Traitement des enseignants
            for ldap_teacher in ldap.search_teacher(since_timestamp=time_stamp, uai=uai):
                enseignant_infos = "%s %s %s" % (ldap_teacher.uid, ldap_teacher.given_name, ldap_teacher.sn)

                if ldap_teacher.uai_courant and not etablissement_regroupe:
                    etablissement_theme = ldap_teacher.uai_courant.lower()

                if not ldap_teacher.mail:
                    ldap_teacher.mail = config.constantes.default_mail

                # Affichage du mail reserve aux membres de cours
                mail_display = config.constantes.default_mail_display
                if ldap_structure.uai in config.etablissements.listeEtabSansMail:
                    # Desactivation de l'affichage du mail
                    mail_display = 0

                # Insertion de l'enseignant
                id_user = db.get_user_id(ldap_teacher.uid)
                if not id_user:
                    db.insert_moodle_user(ldap_teacher.uid, ldap_teacher.given_name, ldap_teacher.sn, ldap_teacher.mail,
                                       mail_display, etablissement_theme)
                    id_user = db.get_user_id(ldap_teacher.uid)
                else:
                    db.update_moodle_user(id_user, ldap_teacher.given_name, ldap_teacher.sn, ldap_teacher.mail, mail_display,
                                       etablissement_theme)

                # Mise ajour des droits sur les anciens etablissement
                if ldap_teacher.uais is not None and not etablissement_regroupe:
                    # Recuperation des uais des etablissements dans lesquels l'enseignant est autorise
                    mettre_a_jour_droits_enseignant(db, enseignant_infos, gereAdminLocal,
                                                    id_context_categorie, id_context_course_forum, id_user,
                                                    ldap_teacher.uais)

                # Ajout du role de createur de cours au niveau de la categorie inter-etablissement Moodle
                db.add_role_to_user(config.constantes.id_role_createur_cours,
                                 id_context_categorie_inter_etabs,
                                 id_user)
                logging.info("        |_ Ajout du role de createur de cours dans la categorie inter-etablissements")

                # Si l'enseignant fait partie d'un CFA
                # Ajout du role createur de cours au niveau de la categorie inter-cfa
                if ldap_structure.type == config.constantes.type_structure_cfa:
                    db.add_role_to_user(config.constantes.id_role_createur_cours,
                                     id_context_categorie_inter_cfa, id_user)
                    logging.info("        |_ Ajout du role de createur de cours dans la categorie inter-cfa")

                # ajout du role de createur de cours dans l'etablissement
                db.add_role_to_user(config.constantes.id_role_createur_cours, id_context_categorie, id_user)

                # Ajouts des autres roles pour le personnel établissement
                if 'National_3' in ldap_teacher.profils or 'National_5' in ldap_teacher.profils or 'National_6' in ldap_teacher.profils or 'National_4' in ldap_teacher.profils:
                    # Ajout des roles sur le contexte forum
                    db.add_role_to_user(ID_ROLE_ELEVE, id_context_course_forum, id_user)
                    # Inscription à la Zone Privée
                    db.enroll_user_in_course(ID_ROLE_ELEVE, id_zone_privee, id_user)

                    if 'National_3' in ldap_teacher.profils or 'National_5' in ldap_teacher.profils or 'National_6' in ldap_teacher.profils:
                        if not gereAdminLocal:
                            db.add_role_to_user(id_role_extended_teacher, id_context_categorie, id_user)
                    elif 'National_4' in ldap_teacher.profils:
                        db.add_role_to_user(config.constantes.id_role_directeur, id_context_categorie, id_user)

                # Ajout des droits d'administration locale pour l'etablissement
                if gereAdminLocal:
                    for member in ldap_teacher.is_member_of:
                        # L'enseignant est il administrateur Moodle ?
                        adminMoodle = re.match(regexpAdminMoodle, member, flags=re.IGNORECASE)
                        if adminMoodle:
                            insert = db.insert_moodle_local_admin(id_context_categorie, id_user)
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
                    if ldap_teacher.uai_courant and ldap_teacher.uai_courant in map_etab_domaine:
                        user_domain = map_etab_domaine[ldap_teacher.uai_courant][0]
                logging.debug("Insertion du Domaine")
                db.set_user_domain(id_user, id_field_domaine, user_domain)
        if purge_cohortes:
            # Si la purge des cohortes a ete demandee
            # On recupere tous les eleves sans prendre en compte le timestamp
            time_stamp = None
        # CREATION DES COHORTES DE PROFS
        db.create_profs_etabs_cohorts(id_context_categorie, uai,maintenant_sql, time_stamp, ldap)

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

        db = Database(config.database)

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
        db = Database(config.database)

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
        db = Database(config.database)

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
