# coding: utf-8

from logging import getLogger

from synchromoodle.synchronizer import Synchronizer
from synchromoodle.timestamp import TimestampStore
from .arguments import default_args
from .config import Config, ActionConfig
from .dbutils import Database
from .ldaputils import Ldap


def default(config: Config, action: ActionConfig, arguments=default_args):
    """
    Execute la mise à jour de la base de données Moodle à partir des informations du LDAP.
    :param config: Configuration d'execution
    :param action: Configuration de l'action
    :param arguments: Arguments de ligne de commande
    """
    log = getLogger()

    db = Database(config.database, config.constantes)
    ldap = Ldap(config.ldap)
    try:
        db.connect()
        ldap.connect()

        synchronizer = Synchronizer(ldap, db, config, action, arguments)
        synchronizer.initialize()

        timestamp_store = TimestampStore(action.timestamp_store)

        log.info('Traitement des établissements')
        for uai in action.etablissements.listeEtab:
            etablissement_log = log.getChild('etablissement.%s' % uai)

            etablissement_log.info('Traitement de l\'établissement (uai=%s)' % uai)
            etablissement_context = synchronizer.handle_etablissement(uai, log=etablissement_log)

            etablissement_log.info('Traitement des élèves pour l\'établissement (uai=%s)' % uai)
            since_timestamp = timestamp_store.get_timestamp(uai)

            for eleve in ldap.search_eleve(since_timestamp, uai):
                utilisateur_log = etablissement_log.getChild("utilisateur.%s" % eleve.uid)
                utilisateur_log.info("Traitement de l'élève (uid=%s)" % eleve.uid)
                synchronizer.handle_eleve(etablissement_context, eleve, log=utilisateur_log)

            etablissement_log.info("Traitement du personnel enseignant pour l'établissement (uai=%s)" % uai)
            for enseignant in ldap.search_enseignant(since_timestamp=since_timestamp, uai=uai):
                utilisateur_log = etablissement_log.getChild("enseignant.%s" % enseignant.uid)
                utilisateur_log.info("Traitement de l'enseignant (uid=%s)" % enseignant.uid)
                synchronizer.handle_enseignant(etablissement_context, enseignant, log=utilisateur_log)

            # TODO: Merger cette fonction dans mise_a_jour_enseignant
            synchronizer.create_profs_etabs_cohorts(etablissement_context, since_timestamp)

            # TODO: Executer un commit de base de données sur chaque objet traité (établissement, enseignant, élève)
            db.connection.commit()

            timestamp_store.mark(uai)
            timestamp_store.write()

        log.info("Fin du traitement des établissements")
    finally:
        db.disconnect()
        ldap.disconnect()


def interetab(config: Config, action: ActionConfig, arguments=default_args):
    """
    Effectue la mise a jour de la BD Moodle via les infos issues du LDAP
    Cette mise a jour concerne les utilisateurs et administrateurs inter-etablissements
    :param config: Configuration globale
    :param action: Configuration de l'action
    :param arguments: Arguments de ligne de commande
    :return:
    """
    log = getLogger()

    db = Database(config.database, config.constantes)
    ldap = Ldap(config.ldap)
    try:
        db.connect()
        ldap.connect()

        synchronizer = Synchronizer(ldap, db, config, action, arguments)
        synchronizer.initialize()

        timestamp_store = TimestampStore(action.timestamp_store)

        log.info('Traitement des utilisateurs inter-établissements')
        personne_filter = {
            action.inter_etablissements.ldap_attribut_user: action.inter_etablissements.ldap_valeur_attribut_user
        }

        since_timestamp = timestamp_store.get_timestamp(action.inter_etablissements.cle_timestamp)

        for personne_ldap in ldap.search_personne(since_timestamp=since_timestamp, **personne_filter):
            utilisateur_log = log.getChild("utilisateur.%s" % personne_ldap.uid)
            utilisateur_log.info("Traitement de l'utilisateur (uid=%s)" % personne_ldap.uid)
            synchronizer.handle_user_interetab(personne_ldap, log=utilisateur_log)

        log.info('Mise à jour des cohortes de la categorie inter-établissements')

        # TODO: Cette variable ne semble plus alimentée
        utilisateurs_by_cohortes = {}

        for is_member_of, cohort_name in action.inter_etablissements.cohorts.items():
            synchronizer.mise_a_jour_cohorte_interetab(is_member_of, cohort_name, since_timestamp, log=log)

        db.connection.commit()

        timestamp_store.mark(action.inter_etablissements.cle_timestamp)
        timestamp_store.write()

        log.info("Fin du traitement des utilisateurs inter-établissements")
    finally:
        db.disconnect()
        ldap.disconnect()


def inspecteurs(config: Config, action: ActionConfig, arguments=default_args):
    """
    Effectue la mise a jour de la BD
    Moodle via les infos issues du LDAP
    Cette mise a jour concerne les inspecteurs
    :param config: Configuration globale
    :param action: Configuration de l'action
    :param arguments: Arguments de ligne de commande
    """
    log = getLogger()

    db = Database(config.database, config.constantes)
    ldap = Ldap(config.ldap)
    try:
        db.connect()
        ldap.connect()

        synchronizer = Synchronizer(ldap, db, config, action, arguments)
        synchronizer.initialize()

        log.info('Traitement des inspecteurs')
        timestamp_store = TimestampStore(action.timestamp_store)

        personne_filter = {
            action.inspecteurs.ldap_attribut_user: action.inspecteurs.ldap_valeur_attribut_user
        }

        # Traitement des inspecteurs
        for personne_ldap in ldap.search_personne(timestamp_store.get_timestamp(action.inspecteurs.cle_timestamp),
                                                  **personne_filter):
            utilisateur_log = log.getChild("utilisateur.%s" % personne_ldap.uid)
            utilisateur_log.info("Traitement de l'inspecteur (uid=%s)" % personne_ldap.uid)
            synchronizer.handle_inspecteur(personne_ldap)

        db.connection.commit()

        # Mise a jour de la date de dernier traitement
        timestamp_store.mark(action.inspecteurs.cle_timestamp)
        timestamp_store.write()

        log.info('Fin du traitement des inspecteurs')
    finally:
        db.disconnect()
        ldap.disconnect()


def nettoyage(config: Config, action: ActionConfig, arguments=default_args):
    """
    Effectue une purge des cohortes dans la base de données par rapport
    au contenu du LDAP et supprime les cohortes inutiles (vides)
    :param config: Configuration globale
    :param action: Configuration de l'action
    :param arguments: Arguments de ligne de commande
    :return:
    """
    log = getLogger()

    db = Database(config.database, config.constantes)
    ldap = Ldap(config.ldap)
    try:
        db.connect()
        ldap.connect()

        synchronizer = Synchronizer(ldap, db, config, action, arguments)
        synchronizer.initialize()

        log.info("Début de l'action de nettoyage")
        for uai in config.etablissements.listeEtab:
            etablissement_log = log.getChild('etablissement.%s' % uai)

            etablissement_log.info('Nettoyage de l\'établissement (uai=%s)' % uai)
            etablissement_context = synchronizer.handle_etablissement(uai, log=etablissement_log)

            eleves_by_cohorts_db, eleves_by_cohorts_ldap = synchronizer. \
                get_users_by_cohorts_comparators(etablissement_context)

            eleves_lvformation_by_cohorts_db, eleves_lvformation_by_cohorts_ldap = synchronizer. \
                get_users_by_cohorts_comparators(etablissement_context, r'(Élèves du Niveau de formation )(.*)$')

            profs_by_cohorts_db, profs_by_cohorts_ldap = synchronizer. \
                get_users_by_cohorts_comparators(etablissement_context, r'(Profs de la Classe )(.*)$')

            synchronizer.purge_cohorts(eleves_by_cohorts_db, eleves_by_cohorts_ldap)
            synchronizer.purge_cohorts(eleves_lvformation_by_cohorts_db, eleves_lvformation_by_cohorts_ldap,
                                       'Élèves du Niveau de formation %s')
            synchronizer.purge_cohorts(profs_by_cohorts_db, profs_by_cohorts_ldap,
                                       'Profs de la Classe %s')
            log.info("Suppression des cohortes vides (sans utilisateurs)")
            db.delete_empty_cohorts()

        log.info("Fin d'action de nettoyage")
    finally:
        db.disconnect()
        ldap.disconnect()
