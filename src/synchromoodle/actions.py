# coding: utf-8

import logging
import sys

from synchromoodle.majutils import Synchronizer

from synchromoodle.timestamp import TimestampStore
from .config import Config
from .dbutils import Database
from .ldaputils import Ldap

logging.basicConfig(format='%(levelname)s:%(message)s', stream=sys.stdout, level=logging.INFO)


def default(config: Config, options):
    """
    Execute la mise à jour de la base de données Moodle à partir des informations du LDAP.
    :param config: Configuration d'execution
    :param options: True si la purge des cohortes doit etre effectuée
    """
    db = Database(config.database, config.constantes)
    ldap = Ldap(config.ldap)
    try:
        logging.info('============================================')
        logging.info('Synchronisation établissements : DEBUT')

        db.connect()
        ldap.connect()

        synchronizer = Synchronizer(ldap, db, config, options)
        synchronizer.load_context()

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

            logging.info('    |_ Mise à jour des eleves')
            since_timestamp = timestamp_store.get_timestamp(uai)

            # Si la purge des cohortes a ete demandee, on recupere tous les eleves sans prendre en compte le timestamp
            # du dernier traitement
            for ldap_student in ldap.search_student(since_timestamp if not options.purge_cohortes else None, uai):
                synchronizer.mise_a_jour_eleve(etablissement_context, ldap_student)

            if options.purge_cohortes:
                logging.info('    |_ Purge des cohortes des élèves')
                synchronizer.purge_eleve_cohorts(etablissement_context)

            logging.info('    |_ Mise à jour du personnel enseignant')
            for ldap_teacher in ldap.search_teacher(since_timestamp=since_timestamp, uai=uai):
                synchronizer.mise_a_jour_enseignant(etablissement_context, ldap_teacher)

            synchronizer.create_profs_etabs_cohorts(etablissement_context,
                                                    since_timestamp if not options.purge_cohortes else None)

            db.connection.commit()

            timestamp_store.mark(uai)
            timestamp_store.write()

        logging.info('Synchronisation établissements : FIN')
        logging.info('============================================')
    finally:
        db.disconnect()
        ldap.disconnect()


def interetab(config: Config, options):
    """
    Effectue la mise a jour de la BD Moodle via les infos issues du LDAP
    Cette mise a jour concerne les utilisateurs et administrateurs inter-etablissements
    :param config: Configuration d'execution
    :param options: 
    :return: 
    """
    db = Database(config.database, config.constantes)
    ldap = Ldap(config.ldap)
    try:
        logging.info("  |_ Traitement de l'inter-établissements")

        db.connect()
        ldap.connect()

        synchronizer = Synchronizer(ldap, db, config, options)
        synchronizer.load_context()

        ###################################################
        # Recuperation de la date de dernier traitement
        ###################################################
        timestamp_store = TimestampStore(config.timestamp_store)

        ###################################################
        # Mise a jour des utilisateurs inter-etabs
        ###################################################
        logging.info('    |_ Mise à jour des utilisateurs inter-etablissements')

        people_filter = {
            config.inter_etablissements.ldap_attribut_user: config.inter_etablissements.ldap_valeur_attribut_user}

        since_timestamp = timestamp_store.get_timestamp(config.inter_etablissements.cle_timestamp)

        # Traitement des eleves
        for ldap_people in ldap.search_people(since_timestamp=since_timestamp, **people_filter):
            synchronizer.mise_a_jour_user_interetab(ldap_people)

        ###################################################
        # Mise a jour des cohortes inter-etabs
        ###################################################
        logging.info('    |_ Mise à jour des cohortes de la categorie inter-etablissements')

        # Dictionnaires permettant de sauvegarder les eleves inscrits
        # dans les cohortes, pour une eventuelle purge
        utilisateurs_by_cohortes = {}

        # Mise a jour de chaque cohorte declaree
        for is_member_of, cohort_name in config.inter_etablissements.cohorts.items():
            synchronizer.mise_a_jour_cohorte_interetab(is_member_of, cohort_name, since_timestamp)

        # Purge des cohortes des eleves
        if options.purge_cohortes:
            logging.info('    |_ Purge des cohortes de la catégorie inter-établissements')
            db.purge_cohorts(utilisateurs_by_cohortes)

        db.connection.commit()
        db.disconnect()

        # Mise a jour de la date de dernier traitement
        timestamp_store.mark(config.inter_etablissements.cle_timestamp)
        timestamp_store.write()
    finally:
        db.disconnect()
        ldap.disconnect()


def inspecteurs(config: Config, options):
    """
    Effectue la mise a jour de la BD
    Moodle via les infos issues du LDAP
    Cette mise a jour concerne les inspecteurs
    :param config: Configuration d'execution
    """
    db = Database(config.database, config.constantes)
    ldap = Ldap(config.ldap)
    try:
        logging.info('============================================')
        logging.info('Synchronisation des inspecteurs : DEBUT')
        logging.info("  |_ Traitement des inspecteurs")

        db.connect()
        ldap.connect()

        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.load_context()

        ###################################################
        # Mise a jour des inspecteurs
        ###################################################
        logging.info('    |_ Mise à jour des inspecteurs')

        # TODO : gerer le time_stamp
        time_stamp = None

        people_filter = {
            config.inspecteurs_config.ldap_attribut_user: config.inspecteurs_config.ldap_valeur_attribut_user}

        # Traitement des inspecteurs
        for ldap_people in ldap.search_people(time_stamp, **people_filter):
            synchronizer.mise_a_jour_inspecteur(ldap_people)

        db.connection.commit()

        logging.info('Synchronisation des inspecteurs : FIN')
        logging.info('============================================')
    finally:
        db.disconnect()
        ldap.disconnect()
