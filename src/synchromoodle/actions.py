# coding: utf-8

import logging
import sys

from synchromoodle.synchronizer import Synchronizer
from synchromoodle.timestamp import TimestampStore
from .arguments import default_args
from .config import Config
from .dbutils import Database
from .ldaputils import Ldap

logging.basicConfig(format='%(levelname)s:%(message)s', stream=sys.stdout, level=logging.INFO)


def default(config: Config, arguments=default_args):
    """
    Execute la mise à jour de la base de données Moodle à partir des informations du LDAP.
    :param config: Configuration d'execution
    :param arguments: Arguments de ligne de commande
    """
    db = Database(config.database, config.constantes)
    ldap = Ldap(config.ldap)
    try:
        logging.info('============================================')
        logging.info('Synchronisation établissements : DEBUT')

        db.connect()
        ldap.connect()

        synchronizer = Synchronizer(ldap, db, config, arguments)
        synchronizer.initialize()

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
            etablissement_context = synchronizer.handle_etablissement(uai)

            logging.info('    |_ Mise à jour des eleves')
            since_timestamp = timestamp_store.get_timestamp(uai)

            # Si la purge des cohortes a ete demandee, on recupere tous les eleves sans prendre en compte le timestamp
            # du dernier traitement
            for eleve in ldap.search_eleve(since_timestamp if not arguments.purge_cohortes else None, uai):
                synchronizer.handle_eleve(etablissement_context, eleve)

            if arguments.purge_cohortes:
                logging.info('    |_ Purge des cohortes des élèves')
                synchronizer.purge_eleve_cohorts(etablissement_context)

            logging.info('    |_ Mise à jour du personnel enseignant')
            for enseignant in ldap.search_enseignant(since_timestamp=since_timestamp, uai=uai):
                synchronizer.handle_enseignant(etablissement_context, enseignant)

            # TODO: Merger cette fonction dans mise_a_jour_enseignant
            synchronizer.create_profs_etabs_cohorts(etablissement_context,
                                                    since_timestamp if not arguments.purge_cohortes else None)

            db.connection.commit()

            timestamp_store.mark(uai)
            timestamp_store.write()

        logging.info('Synchronisation établissements : FIN')
        logging.info('============================================')
    finally:
        db.disconnect()
        ldap.disconnect()


def interetab(config: Config, arguments=default_args):
    """
    Effectue la mise a jour de la BD Moodle via les infos issues du LDAP
    Cette mise a jour concerne les utilisateurs et administrateurs inter-etablissements
    :param config: Configuration d'execution
    :param arguments: Arguments de ligne de commande
    :return:
    """
    db = Database(config.database, config.constantes)
    ldap = Ldap(config.ldap)
    try:
        logging.info("  |_ Traitement de l'inter-établissements")

        db.connect()
        ldap.connect()

        synchronizer = Synchronizer(ldap, db, config, arguments)
        synchronizer.initialize()

        ###################################################
        # Recuperation de la date de dernier traitement
        ###################################################
        timestamp_store = TimestampStore(config.timestamp_store)

        ###################################################
        # Mise a jour des utilisateurs inter-etabs
        ###################################################
        logging.info('    |_ Mise à jour des utilisateurs inter-etablissements')

        personne_filter = {
            config.inter_etablissements.ldap_attribut_user: config.inter_etablissements.ldap_valeur_attribut_user
        }

        since_timestamp = timestamp_store.get_timestamp(config.inter_etablissements.cle_timestamp)

        # Traitement des eleves
        for personne_ldap in ldap.search_personne(since_timestamp=since_timestamp, **personne_filter):
            synchronizer.handle_user_interetab(personne_ldap)

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
        if arguments.purge_cohortes:
            logging.info('    |_ Purge des cohortes de la catégorie inter-établissements')
            db.purge_cohorts(utilisateurs_by_cohortes)

        db.connection.commit()

        # Mise a jour de la date de dernier traitement
        timestamp_store.mark(config.inter_etablissements.cle_timestamp)
        timestamp_store.write()
    finally:
        db.disconnect()
        ldap.disconnect()


def inspecteurs(config: Config, arguments=default_args):
    """
    Effectue la mise a jour de la BD
    Moodle via les infos issues du LDAP
    Cette mise a jour concerne les inspecteurs
    :param config: Configuration d'execution
    :param arguments: Arguments de ligne de commande
    """
    db = Database(config.database, config.constantes)
    ldap = Ldap(config.ldap)
    try:
        logging.info('============================================')
        logging.info('Synchronisation des inspecteurs : DEBUT')
        logging.info("  |_ Traitement des inspecteurs")

        db.connect()
        ldap.connect()

        synchronizer = Synchronizer(ldap, db, config, arguments)
        synchronizer.initialize()

        ###################################################
        # Mise a jour des inspecteurs
        ###################################################
        logging.info('    |_ Mise à jour des inspecteurs')

        timestamp_store = TimestampStore(config.timestamp_store)

        personne_filter = {
            config.inspecteurs.ldap_attribut_user: config.inspecteurs.ldap_valeur_attribut_user
        }

        # Traitement des inspecteurs
        for personne_ldap in ldap.search_personne(timestamp_store.get_timestamp(config.inspecteurs.cle_timestamp),
                                                  **personne_filter):
            synchronizer.handle_inspecteur(personne_ldap)

        db.connection.commit()

        # Mise a jour de la date de dernier traitement
        timestamp_store.mark(config.inspecteurs.cle_timestamp)
        timestamp_store.write()

        logging.info('Synchronisation des inspecteurs : FIN')
        logging.info('============================================')
    finally:
        db.disconnect()
        ldap.disconnect()
