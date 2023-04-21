# coding: utf-8
"""
Actions
"""

from logging import getLogger

from synchromoodle.synchronizer import Synchronizer
from synchromoodle.timestamp import TimestampStore
from .arguments import DEFAULT_ARGS
from .config import Config, ActionConfig
from .dbutils import Database
from .ldaputils import Ldap


def default(config: Config, action: ActionConfig, arguments=DEFAULT_ARGS):
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

            etablissement_log.debug("Construction du dictionnaire d'association classe -> niveau formation")
            synchronizer.construct_classe_to_niv_formation(etablissement_context, ldap.search_eleve(None, uai))

            for eleve in ldap.search_eleve(since_timestamp, uai):
                utilisateur_log = etablissement_log.getChild("utilisateur.%s" % eleve.uid)
                utilisateur_log.info("Traitement de l'élève (uid=%s)" % eleve.uid)
                synchronizer.handle_eleve(etablissement_context, eleve, log=utilisateur_log)

            etablissement_log.info("Traitement du personnel enseignant pour l'établissement (uai=%s)" % uai)
            for enseignant in ldap.search_enseignant(since_timestamp=since_timestamp, uai=uai):
                utilisateur_log = etablissement_log.getChild("enseignant.%s" % enseignant.uid)
                utilisateur_log.info("Traitement de l'enseignant (uid=%s)" % enseignant.uid)
                synchronizer.handle_enseignant(etablissement_context, enseignant, log=utilisateur_log)

            db.connection.commit()

            timestamp_store.mark(uai)
            timestamp_store.write()

        log.info("Fin du traitement des établissements")
    finally:
        db.disconnect()
        ldap.disconnect()


def interetab(config: Config, action: ActionConfig, arguments=DEFAULT_ARGS):
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

        for is_member_of, cohort_name in action.inter_etablissements.cohorts.items():
            synchronizer.mise_a_jour_cohorte_interetab(is_member_of, cohort_name, since_timestamp, log=log)

        db.connection.commit()

        timestamp_store.mark(action.inter_etablissements.cle_timestamp)
        timestamp_store.write()

        log.info("Fin du traitement des utilisateurs inter-établissements")
    finally:
        db.disconnect()
        ldap.disconnect()


def inspecteurs(config: Config, action: ActionConfig, arguments=DEFAULT_ARGS):
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


def nettoyage(config: Config, action: ActionConfig, arguments=DEFAULT_ARGS):
    """
    Effectue une purge des cohortes dans la base de données par rapport
    au contenu du LDAP et supprime les cohortes inutiles (vides)
    Anonymisation/suppression des utilisateurs inutiles
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

        synchronizer.handle_dane(config.constantes.uai_dane)

        # Nettoyage par anonymisation/suppression des utilisateurs inutiles et des cours
        log.info("Début de la procédure d'anonymisation/suppression des utilisateurs/cours inutiles")
        ldap_users = ldap.search_personne()
        db_valid_users = db.get_all_valid_users()
        synchronizer.anonymize_or_delete_users(ldap_users, db_valid_users)

        db.connection.commit()

        cohort_elv_lycee_en_ldap = []
        cohort_ens_lycee_en_ldap = []
        cohort_dir_lycee_en_ldap = []
        cohorts_elv_dep_clg_ldap = {}
        cohorts_ens_dep_clg_ldap = {}
        cohorts_dir_dep_clg_ldap = {}

        for departement in config.constantes.departements:
            cohorts_elv_dep_clg_ldap[departement] = []
            cohorts_ens_dep_clg_ldap[departement] = []
            cohorts_dir_dep_clg_ldap[departement] = []

        log.info("Début de l'action de nettoyage")
        # Purge des cohortes pour n'y conserver que les utilisateurs qui doivent encore être dedans
        #  (correspond à la purge de l'ancien script)
        for uai in action.etablissements.listeEtab:
            etablissement_log = log.getChild('etablissement.%s' % uai)

            etablissement_log.info("Nettoyage de l'établissement (uai=%s)" % uai)
            etablissement_context = synchronizer.handle_etablissement(uai, log=etablissement_log, readonly=True)
            departement = etablissement_context.departement

            if config.delete.purge_cohorts:

                eleves_by_cohorts_db, eleves_by_cohorts_ldap = synchronizer.\
                    get_users_by_cohorts_comparators_eleves_classes(etablissement_context, r'(Élèves de la Classe )(.*)$',
                                                     'Élèves de la Classe %')

                eleves_lvformation_by_cohorts_db, eleves_lvformation_by_cohorts_ldap = synchronizer.\
                    get_users_by_cohorts_comparators_eleves_niveau(etablissement_context, r'(Élèves du Niveau de formation )(.*)$',
                                                     'Élèves du Niveau de formation %')

                profs_classe_by_cohorts_db, profs_classe_by_cohorts_ldap = synchronizer.\
                    get_users_by_cohorts_comparators_profs_classes(etablissement_context, r'(Profs de la Classe )(.*)$',
                                                     'Profs de la Classe %')

                profs_etab_by_cohorts_db, profs_etab_by_cohorts_ldap = synchronizer.\
                    get_users_by_cohorts_comparators_profs_etab(etablissement_context, r"(Profs de l'établissement )(.*)$",
                                                     "Profs de l'établissement %")

                profs_niveau_by_cohorts_db, profs_niveau_by_cohorts_ldap = synchronizer.\
                    get_users_by_cohorts_comparators_profs_niveau(etablissement_context, r"(Profs du niveau de formation )(.*)$",
                                                     "Profs du niveau de formation %")

                if etablissement_context.college and departement in config.constantes.departements:
                    cohorts_elv_dep_clg_ldap[departement].append(ldap.search_eleve_uid(uai=uai))
                    cohorts_ens_dep_clg_ldap[departement].append(ldap.search_enseignant_uid(uai=uai, tous=True))
                    cohorts_dir_dep_clg_ldap[departement].append(ldap.search_personnel_direction_uid(uai=uai))

                if etablissement_context.lycee and etablissement_context.etablissement_en:
                    cohort_elv_lycee_en_ldap.append(ldap.search_eleve_uid(uai=uai))
                    cohort_ens_lycee_en_ldap.append(ldap.search_enseignant_uid(uai=uai, tous=True))
                    cohort_dir_lycee_en_ldap.append(ldap.search_personnel_direction_uid(uai=uai))

                #Sert à purger les élèves qui ne sont plus présents dans l'annuaire LDAP des cohortes
                log.info("Purge des cohortes Elèves de la Classe")
                synchronizer.purge_cohorts(eleves_by_cohorts_db, eleves_by_cohorts_ldap,
                                           "Élèves de la Classe %s")

                log.info("Purge des cohortes Elèves du Niveau de formation")
                synchronizer.purge_cohorts(eleves_lvformation_by_cohorts_db, eleves_lvformation_by_cohorts_ldap,
                                           'Élèves du Niveau de formation %s')

                log.info("Purge des cohortes Profs de la Classe")
                synchronizer.purge_cohorts(profs_classe_by_cohorts_db, profs_classe_by_cohorts_ldap,
                                           'Profs de la Classe %s')

                log.info("Purge des cohortes Profs de l'établissement")
                synchronizer.purge_cohorts(profs_etab_by_cohorts_db, profs_etab_by_cohorts_ldap,
                                           "Profs de l'établissement %s")

                log.info("Purge des cohortes Profs du niveau de formation")
                synchronizer.purge_cohorts(profs_niveau_by_cohorts_db, profs_niveau_by_cohorts_ldap,
                                           "Profs du niveau de formation %s")

                # On commit pour chaque étab afin de libérer rapidement le lock
                db.connection.commit()

                # TODO lvillanne mettre en place le système de nettoyage des cohortes dane
                # TODO lvillanne ceci est un exemple pour un type de cohorte dane
                #  voir pour rendre la fonction paramétrable pour els 3 cohortes lycee puis pour faire le même genre de chose pour les colleges
                log.info("Purge de la cohorte dane élèves des lycées de l'éducation national")
                synchronizer.purge_cohort_dane_elv_lycee_en(cohort_elv_lycee_en_ldap)

        if config.delete.purge_cohorts:
            log.info("Suppression des cohortes vides (sans utilisateur)")
            synchronizer.delete_empty_cohorts()

        log.info("Fin de l'action de nettoyage")
    finally:
        db.disconnect()
        ldap.disconnect()
