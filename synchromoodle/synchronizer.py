# coding: utf-8
"""
Synchronizer
"""

import datetime
import re
import shutil
from logging import getLogger
from typing import Dict, List
from enum import Enum

from synchromoodle.config import EtablissementsConfig, Config, ActionConfig
from synchromoodle.dbutils import Database, PROFONDEUR_CTX_ETAB, COURSE_MODULES_MODULE, \
    PROFONDEUR_CTX_MODULE_ZONE_PRIVEE, \
    PROFONDEUR_CTX_BLOCK_ZONE_PRIVEE
from synchromoodle.ldaputils import Ldap, EleveLdap, EnseignantLdap, PersonneLdap
from synchromoodle.ldaputils import StructureLdap

#######################################
# FORUM
#######################################
# Nom du forum pour la zone privee
# Le (%s) est reserve a l'organisation unit de l'etablissement
from synchromoodle.webserviceutils import WebService

FORUM_NAME_ZONE_PRIVEE = "Forum réservé au personnel éducatif de l'établissement %s"

# Format d'intro. pour le forum de la zone privee
FORUM_INTRO_FORMAT_ZONE_PRIVEE = 1

# Introduction pour le forum de la zone privee
FORUM_INTRO_ZONE_PRIVEE = "<p></p>"

# Max attachements pour le forum de la zone privee
FORUM_MAX_ATTACHEMENTS_ZONE_PRIVEE = 2

# Max bytes pour le forum de la zone privee
FORUM_MAX_BYTES_ZONE_PRIVEE = 512000

#######################################
# BLOCKS
#######################################
# Default region pour le bloc de recherche sur le forum de la zone privee
BLOCK_FORUM_SEARCH_DEFAULT_REGION = "side-pre"

# Default weight pour le bloc de recherche sur le forum de la zone privee
BLOCK_FORUM_SEARCH_DEFAULT_WEIGHT = 2

# Nom pour le bloc de recherche sur le forum de la zone privee
BLOCK_FORUM_SEARCH_NAME = "searches_forums"

# Page type pattern pour le bloc de recherche sur le forum de la zone privee
BLOCK_FORUM_SEARCH_PAGE_TYPE_PATTERN = "course-view-*"

# Show in sub context option pour le bloc de recherche sur le forum de la zone privee
BLOCK_FORUM_SEARCH_SHOW_IN_SUB_CTX = 0

# Sub page pattern pour le bloc de recherche sur le forum de la zone privee
BLOCK_FORUM_SEARCH_SUB_PAGE_PATTERN = ""

SECONDS_PER_DAY = 86400

def est_grp_etab(uai: str, etablissements_config: EtablissementsConfig):
    """
    Indique si un établissement fait partie d'un regroupement d'établissement ou non.

    :param uai: code de l'établissement
    :param etablissements_config: EtablissementsConfig
    :return: True si l'établissement fait partie d'un regroupement d'établissement
    """
    for regroupement in etablissements_config.etab_rgp:
        if uai in regroupement.uais:
            return regroupement
    return False


class SyncContext:
    """
    Contexte global de synchronisation
    """

    def __init__(self):
        self.timestamp_now_sql = None
        self.map_etab_domaine = None  # type: Dict[str, List[str]]
        self.id_context_categorie_inter_etabs = None  # type: int
        self.id_context_categorie_inter_cfa = None  # type: int
        self.id_role_extended_teacher = None  # type: int
        self.id_role_advanced_teacher = None  # type: int
        self.id_field_classe = None  # type: int
        self.id_field_domaine = None  # type: int

class EtablissementContext:
    """
    Contexte de synchronisation d'établissement
    """

    def __init__(self, uai: str):
        self.uai = uai  # type: str
        self.id_context_categorie = None
        self.id_context_course_forum = None
        self.etablissement_regroupe = None
        self.structure_ldap = None  # type: StructureLdap
        self.gere_admin_local = None  # type: bool
        self.regexp_admin_moodle = None  # type: str
        self.regexp_admin_local = None  # type: str
        self.id_zone_privee = None  # type: int
        self.etablissement_theme = None  # type: str
        self.eleves_by_cohortes = {}
        self.enseignants_by_cohortes = {}
        self.classe_to_niv_formation = {}
        self.departement = None  # type: str
        self.college = None  # type: bool
        self.lycee = None  # type: bool
        self.etablissement_en = None # type: bool

class UserType(Enum):
    """
    Enumération représentant les différents types de cohortes pour la dane
    """
    ELEVE = 1
    ENSEIGNANT = 2
    PERSONNEL_DE_DIRECTION = 3

class Synchronizer:
    """
    Synchronise les objets métiers entre l'annuaire LDAP et le Moodle.
    """

    def __init__(self, ldap: Ldap, db: Database, config: Config, action_config: ActionConfig = None):
        self.__webservice = WebService(config.webservice)  # type: WebService
        self.__ldap = ldap  # type: Ldap
        self.__db = db  # type: Database
        self.__config = config  # type: Config
        self.__action_config = action_config if action_config \
            else next(iter(config.actions), ActionConfig())  # type: ActionConfig
        self.context = None  # type: SyncContext
        self.context_dane = None  # type: SyncContext
        self.ids_cohorts_dane_lycee_en = {} #type: dict
        self.ids_cohorts_dane_dep_clg = {} #type: dict

    def initialize(self):
        """
        Initialise la synchronisation
        """
        self.context = SyncContext()

        # Recuperation du timestamp actuel
        self.context.timestamp_now_sql = self.__db.get_timestamp_now()

        # Récupération de la liste UAI-Domaine des établissements
        self.context.map_etab_domaine = self.__ldap.get_domaines_etabs()

        # Ids des categories inter etablissements
        id_categorie_inter_etabs = self.__db.get_id_categorie(
            self.__action_config.etablissements.inter_etab_categorie_name)
        self.context.id_context_categorie_inter_etabs = self.__db.get_id_context_categorie(id_categorie_inter_etabs)

        id_categorie_inter_cfa = self.__db.get_id_categorie(
            self.__action_config.etablissements.inter_etab_categorie_name_cfa)
        self.context.id_context_categorie_inter_cfa = self.__db.get_id_context_categorie(id_categorie_inter_cfa)

        # Recuperation des ids des roles
        self.context.id_role_extended_teacher = self.__db.get_id_role_by_shortname('extendedteacher')
        self.context.id_role_advanced_teacher = self.__db.get_id_role_by_shortname('advancedteacher')

        # Recuperation de l'id du user info field pour la classe
        self.context.id_field_classe = self.__db.get_id_user_info_field_by_shortname('classe')

        # Recuperation de l'id du champ personnalisé Domaine
        self.context.id_field_domaine = self.__db.get_id_user_info_field_by_shortname('Domaine')

    def handle_doublons(self, log=getLogger()):
        """
        Supprime les doublons de cohortes.

        :param log: Le logger
        """

        #Récupère les doublons
        cohorts_doublons = self.__db.get_doublons_cohorts()

        #Pour toutes les cohortes en doublon, regarde s'il y'en a une qui est vide
        for (name, contextid) in cohorts_doublons:
            log.info("Doublon trouvé sur la cohorte %s dans le contexte %d", name, contextid)
            trouve = 0
            cohorts_doublons_ids = self.__db.get_all_cohorts_id_from_name(contextid, name)
            for id_cohort, in cohorts_doublons_ids:
                #Il faut qu'il reste au moins une cohorte à la fin
                if trouve < len(cohorts_doublons_ids)-1:
                    if len(self.__db.get_cohort_members_list(id_cohort)) == 0:
                        log.info("Suppression de la cohorte %d dans le contexte %d car"
                                 " elle ne contient pas d'utilisateurs", id_cohort, contextid)
                        self.__webservice.delete_cohorts([id_cohort])
                        trouve += 1
            #Si on a pas trouvé de cohorte vide alors on en supprime au hasard parmi les cohortes
            if trouve == 0:
                for id_cohort, in cohorts_doublons_ids[1:len(cohorts_doublons_ids)]:
                    self.__webservice.delete_cohorts([id_cohort])
                    log.info("Suppression de la cohorte %d dans le contexte %d car"
                             " toutes les cohortes en doublon ont des utilisateurs", id_cohort, contextid)



    def handle_dane(self, uai_dane: str, log=getLogger(), etabonly=False, readonly=False) -> EtablissementContext:
        """
        Synchronise la dane.

        :param uai_dane: Le code établissement de la dane
        :param log: Le logger
        :param etabonly: Si True, synchronise seulement l'établissement et pas ses utilisateurs
        :param readonly: Si True, pas d'insertions/modifications dans la bd
        :return: Le contexte de l'établissement synchronisé
        """
        # Récupération des informations de la dane pour les cohortes de la dane
        context = EtablissementContext(uai_dane)
        log.debug("Recherche de la structure dane dans l'annuaire")
        structure_ldap = self.__ldap.search_dane(uai_dane)
        if structure_ldap:
            log.debug("La structure dane a été trouvée")
            etablissement_path = "/1"

            # Recuperation du bon theme
            context.etablissement_theme = structure_ldap.uai.lower()

            # Creation de la structure si elle n'existe pas encore
            id_dane_categorie = self.__db.get_id_course_category_by_theme(context.etablissement_theme)
            if id_dane_categorie is None and not readonly:
                log.info("Création de la structure dane")
                self.insert_moodle_structure(False, structure_ldap.nom,
                                                etablissement_path, structure_ldap.nom,
                                                structure_ldap.siren, context.etablissement_theme)

            #Récupération de l'id de la catégorie de la structure dane
            id_dane_categorie = self.__db.get_id_course_category_by_id_number(structure_ldap.siren)

            #Récupération de l'id du contexte dane
            context.id_context_categorie = self.__db.get_id_context_categorie(id_dane_categorie)

            #Cas ou on est en pas en readonly = on peut créer les cohortes si besoin
            if not readonly:
                #Cas ou on est pas en etabonly = on va syncrhoniser les utilisateurs de la dane
                if not etabonly:

                    #Filtres pour récupérer les utilisateurs de la dane
                    dane_filter_user = {self.__config.dane.dane_attribut: self.__config.dane.dane_user}
                    dane_filter_medic = {self.__config.dane.dane_attribut: self.__config.dane.dane_user_medic}

                    #Récupération des utilisateurs de la dane
                    user_dane_list = self.__ldap.search_personne(since_timestamp=None, **dane_filter_user)
                    user_medic_dane_list = self.__ldap.search_personne(since_timestamp=None, **dane_filter_medic)

                    #Création des utilisateurs de la dane
                    log.info("Création des utilisateurs de la dane")
                    for personne_ldap in user_dane_list:
                        if not personne_ldap.mail:
                            personne_ldap.mail = self.__config.constantes.default_mail
                        id_user = self.__db.get_user_id(personne_ldap.uid)
                        if not id_user:
                            log.info("Création de l'utilisateur: %s", personne_ldap)
                            self.__db.insert_moodle_user(personne_ldap.uid, personne_ldap.given_name, personne_ldap.sn,
                                                         personne_ldap.mail,
                                                         self.__config.constantes.default_mail_display,
                                                         self.__config.constantes.default_moodle_theme)
                            id_user = self.__db.get_user_id(personne_ldap.uid)
                        else:
                            log.info("Mise à jour de l'utilisateur: %s", personne_ldap)
                            self.__db.update_moodle_user(id_user, personne_ldap.given_name, personne_ldap.sn, personne_ldap.mail,
                                                         self.__config.constantes.default_mail_display,
                                                         self.__config.constantes.default_moodle_theme)
                        self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                                   context.id_context_categorie, id_user)

                    #Création des utilisateurs médico-sociaux de la dane
                    log.info("Création des utilisateurs médico-sociaux de la dane")
                    for personne_ldap in user_medic_dane_list:
                        if not personne_ldap.mail:
                            personne_ldap.mail = self.__config.constantes.default_mail
                        id_user = self.__db.get_user_id(personne_ldap.uid)
                        if not id_user:
                            log.info("Création de l'utilisateur: %s", personne_ldap)
                            self.__db.insert_moodle_user(personne_ldap.uid, personne_ldap.given_name, personne_ldap.sn,
                                                         personne_ldap.mail,
                                                         self.__config.constantes.default_mail_display,
                                                         self.__config.constantes.default_moodle_theme)
                            id_user = self.__db.get_user_id(personne_ldap.uid)
                        else:
                            log.info("Mise à jour de l'utilisateur: %s", personne_ldap)
                            self.__db.update_moodle_user(id_user, personne_ldap.given_name, personne_ldap.sn, personne_ldap.mail,
                                                         self.__config.constantes.default_mail_display,
                                                         self.__config.constantes.default_moodle_theme)
                        self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                                   context.id_context_categorie, id_user)
                        #Création et inscription dans une cohorte spécifique pour les utilisateurs médico-sociaux
                        log.info("Création de la cohorte des utilisateurs médico-sociaux de la dane")
                        id_medic_cohort = self.get_or_create_cohort(context.id_context_categorie, self.__config.dane.cohort_medic_dane_name,
                                                                    self.__config.dane.cohort_medic_dane_name, self.__config.dane.cohort_medic_dane_name,
                                                                    self.context.timestamp_now_sql, log)
                        log.info("Inscription de l'utilisateur %s dans la cohorte des utilisateurs médico-sociaux de la dane",
                                 personne_ldap)
                        self.__db.enroll_user_in_cohort(id_medic_cohort, id_user, self.context.timestamp_now_sql)

                # Récupération des identifiants de 3 cohortes pour les lycées de l'enseignement national
                log.info("Création des cohortes dane pour les lycées de l'enseignement national")
                for user_type in UserType:
                    self.ids_cohorts_dane_lycee_en[user_type] = \
                        self.get_or_create_dane_lycee_en_cohort(context.id_context_categorie, user_type,\
                         self.context.timestamp_now_sql, log)

                # Pour les différents type d'utilisateurs
                log.info("Création des cohortes dane pour les collèges par département")
                for user_type in UserType:
                    self.ids_cohorts_dane_dep_clg[user_type] = {}
                    # Récupération des identifiants des cohortes pour les collèges par départements
                    for departement in self.__config.constantes.departements:
                        self.ids_cohorts_dane_dep_clg[user_type][departement] = \
                            self.get_or_create_dane_dep_clg_cohort(context.id_context_categorie, user_type,\
                             departement, self.context.timestamp_now_sql, log)

            #Cas ou on est en readonly : on ne fait que récupérer les ids des cohortes
            else:
                for user_type in UserType:
                    self.ids_cohorts_dane_lycee_en[user_type] = \
                        self.get_dane_lycee_en_cohort(context.id_context_categorie, user_type)
                for user_type in UserType:
                    self.ids_cohorts_dane_dep_clg[user_type] = {}
                    for departement in self.__config.constantes.departements:
                        self.ids_cohorts_dane_dep_clg[user_type][departement] = \
                            self.get_dane_dep_clg_cohort(context.id_context_categorie, user_type, departement)
        else:
            log.debug("La structure dane n'a pas été trouvée")

        #Mise à jour du contexte dane pour le synchronizer
        self.context_dane = context
        return context


    def handle_etablissement(self, uai: str, log=getLogger(), readonly=False) -> EtablissementContext:
        """
        Synchronise un établissement.

        :param uai: Le code établissement
        :param log: Le logger
        :param readonly: Si True, pas d'insertions/modifications dans la bd
        :return: Le contexte de l'établissement synchronisé
        """
        context = EtablissementContext(uai)
        context.gere_admin_local = uai not in self.__action_config.etablissements.liste_etab_sans_admin
        context.etablissement_regroupe = est_grp_etab(uai, self.__action_config.etablissements)
        # Regex pour savoir si l'utilisateur est administrateur moodle
        context.regexp_admin_moodle = self.__action_config.etablissements.prefix_admin_moodle_local + f".*_{uai}$"
        # Regex pour savoir si l'utilisateur est administrateur local
        context.regexp_admin_local = self.__action_config.etablissements.prefix_admin_local + f".*_{uai}$"

        log.debug("Recherche de la structure dans l'annuaire")
        structure_ldap = self.__ldap.get_structure(uai)
        if structure_ldap:
            log.debug("La structure a été trouvée")
            etablissement_path = "/1"

            # Si l'etablissement fait partie d'un groupement
            if context.etablissement_regroupe:
                etablissement_ou = context.etablissement_regroupe.nom
                structure_ldap.uai = context.etablissement_regroupe.uais[0]
                log.debug("L'établissement fait partie d'un groupement: ou=%s, uai=%s",
                          etablissement_ou, structure_ldap.uai)
            else:
                etablissement_ou = structure_ldap.nom
                log.debug("L'établissement ne fait partie d'un groupement: ou=%s", etablissement_ou)

            # Recuperation du bon theme
            context.etablissement_theme = structure_ldap.uai.lower()

            # Affectation des informations utiles pour la constitution des groupes dane
            context.departement = context.uai[1:3] if context.uai[0] == '0' else context.uai[:3]
            context.college = structure_ldap.type == self.__config.constantes.type_structure_clg
            context.lycee = structure_ldap.type.startswith(self.__config.constantes.type_structure_lycee_start_with)
            context.etablissement_en = structure_ldap.jointure.startswith(\
                self.__config.constantes.type_structure_jointure_en_start_with
                )

            # Creation de la structure si elle n'existe pas encore
            id_etab_categorie = self.__db.get_id_course_category_by_theme(context.etablissement_theme)
            if id_etab_categorie is None and not readonly:
                log.info("Création de la structure")
                self.insert_moodle_structure(context.etablissement_regroupe, structure_ldap.nom,
                                             etablissement_path, etablissement_ou,
                                             structure_ldap.siren, context.etablissement_theme)
                id_etab_categorie = self.__db.get_id_course_category_by_id_number(structure_ldap.siren)

            #Mise à jour de l'idnumber et de la description de l'établissement (utile si changement de SIREN)
            else:
                if id_etab_categorie is not None and not readonly and not context.etablissement_regroupe:
                    log.info("Mise à jour de la structure")
                    self.__db.update_course_category_description(id_etab_categorie, structure_ldap.siren)
                    self.__db.update_course_category_idnumber(id_etab_categorie, structure_ldap.siren)

            # Mise a jour de la description dans la cas d'un groupement d'etablissement
            if context.etablissement_regroupe and not readonly:
                description = self.__db.get_description_course_category(id_etab_categorie)
                if description.find(structure_ldap.siren) == -1:
                    log.info("Mise à jour de la description")
                    description = f"{description}${structure_ldap.siren}@{structure_ldap.nom}"
                    self.__db.update_course_category_description(id_etab_categorie, description)
                    self.__db.update_course_category_name(id_etab_categorie, etablissement_ou)

            # Recuperation de l'id du contexte correspondant à l'etablissement
            if id_etab_categorie is not None:
                context.id_context_categorie = self.__db.get_id_context_categorie(id_etab_categorie)

            context.id_zone_privee = self.__db.get_id_course_by_id_number("ZONE-PRIVEE-" + structure_ldap.siren)

            # Recreation de la zone privee si celle-ci n'existe plus
            if context.id_zone_privee is None and not readonly:
                log.info("Création de la zone privée")
                context.id_zone_privee = self.__db.insert_zone_privee(id_etab_categorie, structure_ldap.siren,
                                                                      etablissement_ou, self.context.timestamp_now_sql)

            if context.id_zone_privee is not None:
                context.id_context_course_forum = self.__db.get_id_context(self.__config.constantes.niveau_ctx_cours, 3,
                                                                           context.id_zone_privee)
            if context.id_context_course_forum is None and not readonly:
                log.info("Création du cours associé à la zone privée")
                context.id_context_course_forum = self.__db.insert_zone_privee_context(context.id_zone_privee)

            context.structure_ldap = structure_ldap
        return context


    def construct_classe_to_niv_formation(self, etablissement_context: EtablissementContext,
                                          list_eleve_ldap: list[tuple]):
        """
        Associe au contexte de l'établissement un dictionnaire associant une classe à
        un niveau de formation. Utilisé pour pouvoir récupérer le niveau de formation
        d'un enseignant comme il n'est pas présent directement dans le ldap.

        :param etablissement_context: Le contexte de l'établissement dans lequel on construit le dictionnaire
        :param list_eleve_ldap : Une liste de tuples (classe, niveau) d'élèves
        """
        for eleve_ldap in list_eleve_ldap:
            eleve_classes_for_etab = []
            if eleve_ldap[0].etab_dn == etablissement_context.structure_ldap.dn:
                eleve_classes_for_etab.append(eleve_ldap[0].classe)
            for classe in eleve_classes_for_etab:
                etablissement_context.classe_to_niv_formation[classe] = eleve_ldap[1]


    def handle_eleve(self, etablissement_context: EtablissementContext, eleve_ldap: EleveLdap, log=getLogger()):
        """
        Synchronise un élève au sein d'un établissement.

        :param etablissement_context: Le contexte de l'établissement dans lequel on synchronise l'élève
        :param eleve_ldap: L'élève à synchroniser
        :param log: Le logger
        """

        mail_display = self.__config.constantes.default_mail_display
        if not eleve_ldap.mail:
            eleve_ldap.mail = self.__config.constantes.default_mail
            log.info("Le mail de l'élève n'est pas défini dans l'annuaire, "
                     "utilisation de la valeur par défault: %s", eleve_ldap.mail)

        eleve_id = self.__db.get_user_id(eleve_ldap.uid)

        if not eleve_id:
            log.info("Ajout de l'utilisateur: %s", eleve_ldap)
            self.__db.insert_moodle_user(eleve_ldap.uid, eleve_ldap.given_name,
                                         eleve_ldap.sn, eleve_ldap.mail,
                                         mail_display, etablissement_context.etablissement_theme)
            eleve_id = self.__db.get_user_id(eleve_ldap.uid)
        else:
            log.info("Mise à jour de l'utilisateur: %s", eleve_ldap)
            self.__db.update_moodle_user(eleve_id, eleve_ldap.given_name,
                                         eleve_ldap.sn, eleve_ldap.mail, mail_display,
                                         etablissement_context.etablissement_theme)

        # Ajout ou suppression du role d'utilisateur avec droits limités Pour les eleves de college
        if etablissement_context.structure_ldap.type == self.__config.constantes.type_structure_clg:
            log.info("Ajout du rôle droit limités à l'utilisateur: %s", eleve_ldap)
            self.__db.add_role_to_user(self.__config.constantes.id_role_utilisateur_limite,
                                       self.__config.constantes.id_instance_moodle, eleve_id)
        else:
            self.__db.remove_role_to_user(self.__config.constantes.id_role_utilisateur_limite,
                                          self.__config.constantes.id_instance_moodle, eleve_id)
            log.info(
                "Suppression du role d'utilisateur avec des droits limites à l'utilisateur %s %s %s (id = %s)"
                , eleve_ldap.given_name, eleve_ldap.sn, eleve_ldap.uid, str(eleve_id))

        # Inscription dans les cohortes associees aux classes
        eleve_cohorts = []
        eleve_classes_for_etab = []
        for classe in eleve_ldap.classes:
            if classe.etab_dn == etablissement_context.structure_ldap.dn:
                eleve_classes_for_etab.append(classe.classe)
        if eleve_classes_for_etab:
            log.info("Inscription de l'élève %s "
                     "dans les cohortes de classes %s", eleve_ldap, eleve_classes_for_etab)
            name_pattern = self.__config.constantes.cohortname_pattern_eleves_classe.replace("%","%s")
            idnumber_pattern = self.__config.constantes.cohortidnumber_pattern_eleves_classe.replace("%","%s")
            desc_pattern = self.__config.constantes.cohortdesc_pattern_eleves_classe.replace("%","%s")
            ids_classes_cohorts = self.get_or_create_classes_cohorts(etablissement_context.id_context_categorie,
                                                                     eleve_classes_for_etab,
                                                                     self.context.timestamp_now_sql,
                                                                     name_pattern,
                                                                     idnumber_pattern,
                                                                     desc_pattern,
                                                                     log=log)
            for ids_classe_cohorts in ids_classes_cohorts:
                self.__db.enroll_user_in_cohort(ids_classe_cohorts, eleve_id, self.context.timestamp_now_sql)

            eleve_cohorts.extend(ids_classes_cohorts)

        # Inscription dans la cohorte associee au niveau de formation
        if eleve_ldap.niveau_formation:
            log.info("Inscription de l'élève %s "
                     "dans la cohorte de niveau de formation %s", eleve_ldap, eleve_ldap.niveau_formation)
            id_formation_cohort = self.get_or_create_formation_cohort(etablissement_context.id_context_categorie,
                                                                      eleve_ldap.niveau_formation,
                                                                      self.context.timestamp_now_sql,
                                                                      log=log)
            self.__db.enroll_user_in_cohort(id_formation_cohort, eleve_id, self.context.timestamp_now_sql)
            eleve_cohorts.append(id_formation_cohort)

        # Inscription dans les cohortes de la Dane
        if etablissement_context.college and etablissement_context.departement in self.__config.constantes.departements:
            log.info("Inscription de l'élève %s dans la cohorte collège %s de la dane",
                     eleve_ldap, etablissement_context.departement)
            self.__db.enroll_user_in_cohort(
                self.ids_cohorts_dane_dep_clg[UserType.ELEVE][etablissement_context.departement],
                eleve_id, self.context.timestamp_now_sql
                )
            eleve_cohorts.append(self.ids_cohorts_dane_dep_clg[UserType.ELEVE][etablissement_context.departement])
        elif etablissement_context.lycee and etablissement_context.etablissement_en:
            log.info("Inscription de l'élève %s dans la cohorte lycée de la dane", eleve_ldap)
            self.__db.enroll_user_in_cohort(
                self.ids_cohorts_dane_lycee_en[UserType.ELEVE],
                eleve_id, self.context.timestamp_now_sql
                )
            eleve_cohorts.append(self.ids_cohorts_dane_lycee_en[UserType.ELEVE])

        log.info("Désinscription de l'élève %s des anciennes cohortes", eleve_ldap)
        self.__db.disenroll_user_from_cohorts(eleve_cohorts, eleve_id)

        # Mise a jour de la classe
        id_user_info_data = self.__db.get_id_user_info_data(eleve_id, self.context.id_field_classe)
        if id_user_info_data is not None:
            self.__db.update_user_info_data(eleve_id, self.context.id_field_classe, eleve_ldap.classe.classe)
            log.debug("Mise à jour user_info_data")
        else:
            self.__db.insert_moodle_user_info_data(eleve_id, self.context.id_field_classe, eleve_ldap.classe.classe)
            log.debug("Insertion user_info_data")

        # Mise a jour du Domaine
        user_domain = self.__config.constantes.default_domain
        if len(eleve_ldap.domaines) == 1:
            user_domain = eleve_ldap.domaines[0]
        else:
            if eleve_ldap.uai_courant and eleve_ldap.uai_courant in self.context.map_etab_domaine:
                user_domain = self.context.map_etab_domaine[eleve_ldap.uai_courant][0]
        log.debug("Insertion du Domaine")
        self.__db.set_user_domain(eleve_id, self.context.id_field_domaine, user_domain)


    def handle_enseignant(self, etablissement_context: EtablissementContext,
                          enseignant_ldap: EnseignantLdap, log=getLogger()):
        """
        Met à jour un enseignant ou un personnel de direction au sein d'un établissement.

        :param etablissement_context: Le contexte de l'établissement dans lequel on synchronise l'élève
        :param enseignant_ldap: L'enseignant à synchroniser
        :param log: Le logger
        """

        enseignant_infos = f"{enseignant_ldap.uid} {enseignant_ldap.given_name} {enseignant_ldap.sn}"

        if enseignant_ldap.uai_courant and not etablissement_context.etablissement_regroupe:
            etablissement_context.etablissement_theme = enseignant_ldap.uai_courant.lower()

        if not enseignant_ldap.mail:
            enseignant_ldap.mail = self.__config.constantes.default_mail

        # Affichage du mail reserve aux membres de cours
        mail_display = self.__config.constantes.default_mail_display
        if etablissement_context.structure_ldap.uai in self.__action_config.etablissements.liste_etab_sans_mail:
            # Desactivation de l'affichage du mail
            mail_display = 0

        # Insertion de l'enseignant
        id_user = self.__db.get_user_id(enseignant_ldap.uid)
        if not id_user:
            self.__db.insert_moodle_user(enseignant_ldap.uid, enseignant_ldap.given_name, enseignant_ldap.sn,
                                         enseignant_ldap.mail,
                                         mail_display, etablissement_context.etablissement_theme)
            id_user = self.__db.get_user_id(enseignant_ldap.uid)
        else:
            self.__db.update_moodle_user(id_user, enseignant_ldap.given_name, enseignant_ldap.sn, enseignant_ldap.mail,
                                         mail_display, etablissement_context.etablissement_theme)

        # Mise à jour des droits sur les anciens etablissement
        if enseignant_ldap.uais is not None and not etablissement_context.etablissement_regroupe:
            # Recuperation des uais des etablissements dans lesquels l'enseignant est autorise
            self.mettre_a_jour_droits_enseignant(enseignant_infos, id_user, enseignant_ldap.uais, log=log)

        # Ajout du role de createur de cours au niveau de la categorie inter-etablissement Moodle
        self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                   self.context.id_context_categorie_inter_etabs, id_user)
        log.info("Ajout du role de createur de cours dans la categorie inter-etablissements")

        # Si l'enseignant fait partie d'un CFA
        # Ajout du role createur de cours au niveau de la categorie inter-cfa
        if etablissement_context.structure_ldap.type == self.__config.constantes.type_structure_cfa:
            self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                       self.context.id_context_categorie_inter_cfa, id_user)
            log.info("Ajout du role de createur de cours dans la categorie inter-cfa")
        else:
            if  etablissement_context.structure_ldap.type.startswith('LYCEE') \
                or etablissement_context.structure_ldap.type == self.__config.constantes.type_structure_ens_adapte \
                or etablissement_context.structure_ldap.uai == '0370074E' \
                or ( etablissement_context.structure_ldap.type.startswith('COLLEGE') \
                or etablissement_context.structure_ldap.type == self.__config.constantes.type_structure_cfa_agricole):
                if set(enseignant_ldap.profils).intersection(['National_ENS','National_DOC','National_DIR',\
                                                              'National_ETA', 'National_EVS']):
                    log.info("Ajout du rôle bigbluebutton pour l'utilisateur %s", enseignant_ldap)
                    self.__db.add_role_to_user(self.__config.constantes.id_role_bigbluebutton,
                                               self.__config.constantes.id_instance_moodle, id_user)

        # ajout du role de createur de cours dans l'etablissement
        self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                   etablissement_context.id_context_categorie, id_user)

        # Ajouts des autres roles pour le personnel établissement
        if set(enseignant_ldap.profils).intersection(['National_ENS', 'National_DIR', 'National_EVS', 'National_ETA']):
            # Ajout des roles sur le contexte forum
            self.__db.add_role_to_user(self.__config.constantes.id_role_eleve,
                                       etablissement_context.id_context_course_forum, id_user)
            # Inscription à la Zone Privée
            self.__db.enroll_user_in_course(self.__config.constantes.id_role_eleve,
                                            etablissement_context.id_zone_privee, id_user)

            if set(enseignant_ldap.profils).intersection(['National_ENS', 'National_EVS', 'National_ETA']):
                if not etablissement_context.gere_admin_local:
                    self.__db.add_role_to_user(self.context.id_role_extended_teacher,
                                               etablissement_context.id_context_categorie,
                                               id_user)
            elif 'National_DIR' in enseignant_ldap.profils:
                self.__db.add_role_to_user(self.__config.constantes.id_role_directeur,
                                           etablissement_context.id_context_categorie, id_user)

        # Ajout des droits d'administration locale pour l'etablissement
        if etablissement_context.gere_admin_local:
            for member in enseignant_ldap.is_member_of:
                # L'enseignant est il administrateur Moodle ?
                admin_moodle = re.match(etablissement_context.regexp_admin_moodle, member, flags=re.IGNORECASE)
                if admin_moodle:
                    self.__db.insert_moodle_local_admin(etablissement_context.id_context_categorie, id_user)
                    log.info("Insertion d'un admin  local %s %s %s",
                             enseignant_ldap.uid, enseignant_ldap.given_name, enseignant_ldap.sn)
                    # Si il est admin local on en fait un utilisateur avancé par default
                    if not self.__db.is_enseignant_avance(id_user, self.context.id_role_advanced_teacher):
                        self.__db.add_role_to_user(self.context.id_role_advanced_teacher, 1, id_user)
                    break
                delete = self.__db.delete_moodle_local_admin(self.context.id_context_categorie_inter_etabs, id_user)
                if delete:
                    log.info("Suppression d'un admin local %s %s %s",
                             enseignant_ldap.uid, enseignant_ldap.given_name, enseignant_ldap.sn)

        # Inscription dans les cohortes associees aux classes et au niveau de formation si c'est un enseignant
        if set(enseignant_ldap.profils).intersection(['National_ENS']) or len(enseignant_ldap.classes)>0:
            enseignant_classes_for_etab = []
            #Récupération des classes de l'établissement traité actuellement
            for classe in enseignant_ldap.classes:
                if classe.etab_dn == etablissement_context.structure_ldap.dn:
                    enseignant_classes_for_etab.append(classe.classe)
            if enseignant_classes_for_etab:
                log.info("Inscription de l'enseignant %s dans les cohortes de classes %s",
                         enseignant_ldap, enseignant_classes_for_etab)
                name_pattern = self.__config.constantes.cohortname_pattern_enseignants_classe.replace("%","%s")
                idnumber_pattern = self.__config.constantes.cohortidnumber_pattern_enseignants_classe.replace("%","%s")
                desc_pattern = self.__config.constantes.cohortdesc_pattern_enseignants_classe.replace("%","%s")
                #Création des cohortes de classes
                ids_classes_cohorts = self.get_or_create_classes_cohorts(etablissement_context.id_context_categorie,
                                                                         enseignant_classes_for_etab,
                                                                         self.context.timestamp_now_sql,
                                                                         name_pattern=name_pattern,
                                                                         idnumber_pattern=idnumber_pattern,
                                                                         desc_pattern=desc_pattern,
                                                                         log=log)
                #Inscription dans les cohortes de classe
                for ids_classe_cohorts in ids_classes_cohorts:
                    self.__db.enroll_user_in_cohort(ids_classe_cohorts, id_user, self.context.timestamp_now_sql)

                #Inscription dans les cohortes de niveau de formation
                enseignant_niv_formation = set()
                for classe in enseignant_classes_for_etab:
                    #Il est possible que l'enseignant enseigne dans une classe mais qui n'est pas dans cet établissement
                    #Il sera alors inscrit dans la cohorte du niveau de formation correspondant à la classe lorsqu'on le
                    #traitera avec l'autre établissement en question
                    if classe in etablissement_context.classe_to_niv_formation:
                        enseignant_niv_formation.add(etablissement_context.classe_to_niv_formation[classe])
                    else:
                        log.warning(
                        "Impossible d'inscrire l'enseignant %s dans les cohortes"
                        " de niveau de formation associées à la classe %s",
                         enseignant_ldap, classe
                         )

                if len(enseignant_niv_formation) > 0:
                    log.info("Inscription de l'enseignant %s dans les cohortes de niveau de formation %s",
                             enseignant_ldap, enseignant_niv_formation)

                    name_pattern = self.__config.constantes.cohortname_pattern_enseignants_niv_formation.replace("%","%s")
                    idnumber_pattern = self.__config.constantes.cohortidnumber_pattern_enseignants_niv_formation.replace("%","%s")
                    desc_pattern = self.__config.constantes.cohortdesc_pattern_enseignants_niv_formation.replace("%","%s")
                    #Création des cohortes de niveau de formation
                    ids_niv_formation_cohorts = self.get_or_create_niv_formation_cohorts(etablissement_context.id_context_categorie,
                                                                                         enseignant_niv_formation,
                                                                                         self.context.timestamp_now_sql,
                                                                                         name_pattern=name_pattern,
                                                                                         idnumber_pattern=idnumber_pattern,
                                                                                         desc_pattern=desc_pattern,
                                                                                         log=log)
                    #Inscription dans les cohortes de niveau de formation
                    for id_cohort_niv_formation in ids_niv_formation_cohorts:
                        self.__db.enroll_user_in_cohort(id_cohort_niv_formation, id_user, self.context.timestamp_now_sql)

        if "ENTAuxEnseignant" in enseignant_ldap.object_classes:
            log.info("Inscription de l'enseignant %s dans la cohorte d'enseignants de l'établissement", enseignant_ldap)
            id_prof_etabs_cohort = self.get_or_create_profs_etab_cohort(etablissement_context, log)

            id_user = self.__db.get_user_id(enseignant_ldap.uid)
            self.__db.enroll_user_in_cohort(id_prof_etabs_cohort, id_user, self.context.timestamp_now_sql)

        # Inscription dans les cohortes de la dane
        # Enseignants
        if 'National_ENS' in enseignant_ldap.profils:
            if etablissement_context.college and etablissement_context.departement in self.__config.constantes.departements:
                log.info("Inscription de l'enseignant %s dans la cohorte collège %s de la dane",
                         enseignant_ldap, etablissement_context.departement)
                self.__db.enroll_user_in_cohort(
                    self.ids_cohorts_dane_dep_clg[UserType.ENSEIGNANT][etablissement_context.departement],
                    id_user, self.context.timestamp_now_sql)
            elif etablissement_context.lycee and etablissement_context.etablissement_en:
                log.info("Inscription de l'enseignant %s dans la cohorte lycée de la dane", enseignant_ldap)
                self.__db.enroll_user_in_cohort(
                    self.ids_cohorts_dane_lycee_en[UserType.ENSEIGNANT],
                    id_user, self.context.timestamp_now_sql)

        # Personnel de direction
        if 'National_DIR' in enseignant_ldap.profils:
            if etablissement_context.college and etablissement_context.departement in self.__config.constantes.departements:
                log.info("Inscription du personnel de direction %s dans la cohorte collège %s de la dane",
                         enseignant_ldap, etablissement_context.departement)
                self.__db.enroll_user_in_cohort(self.ids_cohorts_dane_dep_clg[
                    UserType.PERSONNEL_DE_DIRECTION][etablissement_context.departement],
                    id_user, self.context.timestamp_now_sql)
            elif etablissement_context.lycee and etablissement_context.etablissement_en:
                log.info("Inscription du personnel de direction %s dans la cohorte lycée de la dane", enseignant_ldap)
                self.__db.enroll_user_in_cohort(
                    self.ids_cohorts_dane_lycee_en[UserType.PERSONNEL_DE_DIRECTION],
                    id_user, self.context.timestamp_now_sql)

        # Mise a jour du Domaine
        user_domain = self.__config.constantes.default_domain
        if len(enseignant_ldap.domaines) == 1:
            user_domain = enseignant_ldap.domaines[0]
        else:
            if enseignant_ldap.uai_courant and enseignant_ldap.uai_courant in self.context.map_etab_domaine:
                user_domain = self.context.map_etab_domaine[enseignant_ldap.uai_courant][0]
        log.debug("Insertion du Domaine")
        self.__db.set_user_domain(id_user, self.context.id_field_domaine, user_domain)


    def handle_specific_cohorts(self, etablissement_context: EtablissementContext,
                                cohorts: dict[str,str], log=getLogger()):
        """
        Met à jour les cohortes spécifiques d'un établissement en particulier

        :param etablissement_context: Le contexte de l'établissement dans lequel on synchronise l'élève
        :param cohorts: Un dictionnaire {filtre_isMemberOf_ldap : nomCohorte_moodle}
        :param log: Le logger
        """
        self.context.timestamp_now_sql = self.__db.get_timestamp_now()
        for filtre,cohort_name in cohorts.items():
            #On créé la cohorte dans moodle si elle n'existe pas déjà
            id_cohort = self.get_or_create_cohort(etablissement_context.id_context_categorie,
                                                  cohort_name,
                                                  cohort_name,
                                                  cohort_name,
                                                  self.context.timestamp_now_sql,
                                                  log=log)
            #On récupère les personnes pour chaque cohorte à créer
            personnes_ldap = self.__ldap.search_memberOf(etablissement_context.uai,filtre)
            #On inscrit une à une les personnes dans cette cohorte
            for personne in personnes_ldap:
                #On récupère l'utilisateur associé dans moodle
                user_id = self.__db.get_user_id(personne.uid)
                #On l'inscrit dans la cohorte
                log.info("Inscription de l'utilisateur %s dans la cohorte %s", personne, cohort_name)
                self.__db.enroll_user_in_cohort(id_cohort, user_id, self.context.timestamp_now_sql)


    def get_specific_cohort_users(self, etablissement_context: EtablissementContext,
                                  name: str, filtre: str) -> tuple[list[str],list[PersonneLdap]]:
        """
        Retourne deux listes correspondants aux personnes dans la bd et dans le ldap inscrites dans la cohorte

        :param etablissement_context: Le contexte de l'établissement dans lequel on synchronise l'élève
        :param name: Le nom de la cohorte dans la BD
        :param filtre: Le valeur de l'attribut isMemberOf dans le LDAP
        :param log: Le logger
        :return: Un tuple avec deux listes : un pour les personnes de la bd, et l'autre les personnes du ldap
        """
        cohort_id = self.__db.get_cohort_id_from_name(etablissement_context.id_context_categorie, name)
        personnes_bd = self.__db.get_cohort_members_list(cohort_id)
        personnes = self.__ldap.search_memberOf(etablissement_context.uai, filtre)
        personnes_ldap = []
        for personne in personnes:
            personnes_ldap.append(personne.uid.lower())
        return personnes_bd, personnes_ldap

    def handle_user_interetab(self, personne_ldap: PersonneLdap, log=getLogger()):
        """
        Synchronise un utilisateur inter-établissement.

        :param personne_ldap: L'utilisateur à synchroniser
        :param log: Le logger
        """

        #Récupération du contexte à partir du nom de la catégorie paramétrée dans l'action
        id_categorie_inter_etabs_action = self.__db.get_id_categorie(self.__action_config.inter_etablissements.categorie_name)
        id_context_categorie_inter_etabs_action = self.__db.get_id_context_categorie(id_categorie_inter_etabs_action)

        if not personne_ldap.mail:
            personne_ldap.mail = self.__config.constantes.default_mail

        # Creation de l'utilisateur
        id_user = self.__db.get_user_id(personne_ldap.uid)
        if not id_user:
            self.__db.insert_moodle_user(personne_ldap.uid, personne_ldap.given_name, personne_ldap.sn,
                                         personne_ldap.mail,
                                         self.__config.constantes.default_mail_display,
                                         self.__config.constantes.default_moodle_theme)
            id_user = self.__db.get_user_id(personne_ldap.uid)
        else:
            self.__db.update_moodle_user(id_user, personne_ldap.given_name, personne_ldap.sn, personne_ldap.mail,
                                         self.__config.constantes.default_mail_display,
                                         self.__config.constantes.default_moodle_theme)

        # Ajout du role de createur de cours
        self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                   id_context_categorie_inter_etabs_action, id_user)

        # Attribution du role admin local si necessaire
        for member in personne_ldap.is_member_of:
            admin = re.match(self.__action_config.inter_etablissements.ldap_valeur_attribut_admin, member,
                             flags=re.IGNORECASE)
            if admin:
                insert = self.__db.insert_moodle_local_admin(id_context_categorie_inter_etabs_action, id_user)
                if insert:
                    log.info("Insertion d'un admin local %s %s %s",
                             personne_ldap.uid, personne_ldap.given_name, personne_ldap.sn)
                break
            delete = self.__db.delete_moodle_local_admin(id_context_categorie_inter_etabs_action, id_user)
            if delete:
                log.info("Suppression d'un admin local %s %s %s",
                         personne_ldap.uid, personne_ldap.given_name, personne_ldap.sn)

    def handle_inspecteur(self, personne_ldap: PersonneLdap, log=getLogger()):
        """
        Synchronise un inspecteur.

        :param personne_ldap: L'utilisateur à synchroniser
        :param log: Le logger
        """
        if not personne_ldap.mail:
            personne_ldap.mail = self.__config.constantes.default_mail

            # Creation de l'utilisateur
            self.__db.insert_moodle_user(personne_ldap.uid, personne_ldap.given_name, personne_ldap.sn,
                                         personne_ldap.mail,
                                         self.__config.constantes.default_mail_display,
                                         self.__config.constantes.default_moodle_theme)
        id_user = self.__db.get_user_id(personne_ldap.uid)
        if not id_user:
            self.__db.insert_moodle_user(personne_ldap.uid, personne_ldap.given_name, personne_ldap.sn,
                                         personne_ldap.mail,
                                         self.__config.constantes.default_mail_display,
                                         self.__config.constantes.default_moodle_theme)
            id_user = self.__db.get_user_id(personne_ldap.uid)
        else:
            self.__db.update_moodle_user(id_user, personne_ldap.given_name, personne_ldap.sn, personne_ldap.mail,
                                         self.__config.constantes.default_mail_display,
                                         self.__config.constantes.default_moodle_theme)

        # Ajout du role de createur de cours au niveau de la categorie inter-etablissement Moodle
        self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                   self.context.id_context_categorie_inter_etabs, id_user)
        log.info("Ajout du role de createur de cours dans la categorie inter-etablissements")

        # Mise a jour du Domaine
        user_domain = self.__config.constantes.default_domain
        if len(personne_ldap.domaines) == 1:
            user_domain = personne_ldap.domaines[0]
        else:
            if personne_ldap.uai_courant and personne_ldap.uai_courant in self.context.map_etab_domaine:
                user_domain = self.context.map_etab_domaine[personne_ldap.uai_courant][0]
        log.debug("Insertion du Domaine")
        self.__db.set_user_domain(id_user, self.context.id_field_domaine, user_domain)

    def mettre_a_jour_droits_enseignant(self, enseignant_infos: str, id_enseignant: int,
                                        uais_autorises: list[str], log=getLogger()):
        """
        Fonction permettant de mettre à jour les droits d'un enseignant.
        Cette mise à jour consiste à supprimer les roles non autorises puis
        ajouter les roles autorisés.

        :param enseignant_infos: Les infos de l'enseignant (pour print)
        :param id_enseignant: L'id de l'enseignant
        :param uais_autorises: La liste des uai autorisés
        :param log: Le logger
        """
        # Recuperation des themes autorises pour l'enseignant
        themes_autorises = [uai_autorise.lower() for uai_autorise in uais_autorises]
        log.debug("Etablissements autorises pour l'enseignant pour %s : %s",
                  enseignant_infos, themes_autorises)

        #########################
        # ZONES PRIVEES
        #########################
        # Recuperation des ids des roles et les themes non autorises
        ids_roles_non_autorises, ids_themes_non_autorises = self.__db.get_ids_and_themes_not_allowed_roles(
            id_enseignant, themes_autorises)

        # Suppression des roles non autorises
        if ids_roles_non_autorises:
            self.__db.delete_roles(ids_roles_non_autorises)
            log.info("Suppression des rôles d'enseignant pour %s dans les établissements %s"
                     , enseignant_infos, str(ids_themes_non_autorises))
            log.info("Les seuls établissements autorisés pour cet enseignant sont %s", themes_autorises)

        #########################
        # FORUMS
        #########################
        # Recuperation des SIREN des etablissements dans lequel l'enseignant travaille
        sirens = self.__db.get_descriptions_course_categories_by_themes(themes_autorises)

        # Shortname des forums associes
        shortnames_forums = []
        for siren in sirens:
            #Cas spécifique pour les regroupement d'établissement, pour construire le nom des zones
            #privées il ne suffit pas de concaténer le valeur dans la colonne description dans la bd
            if "$" in siren:
                #Récupération de tous les sirens des établissements du regroupement
                rgp_sirens = siren.split("$")
                rgp_sirens[-1] = rgp_sirens[-1].split("@")[0]
                for rgp_siren in rgp_sirens:
                    shortnames_forums.append(f"ZONE-PRIVEE-{rgp_siren}")
            #Cas général
            else:
                shortnames_forums.append(f"ZONE-PRIVEE-{siren}")

        # Recuperation des roles sur les forums qui ne devraient plus exister
        ids_roles_non_autorises, forums_summaries = self.__db.get_ids_and_summaries_not_allowed_roles(id_enseignant,
                                                                                                      shortnames_forums)
        # Suppression des roles non autorises
        if ids_roles_non_autorises:
            # Suppression des roles
            self.__db.delete_roles(ids_roles_non_autorises)
            log.info("Suppression des rôles d'enseignant pour %s sur les forum '%s' ",
                     enseignant_infos, str(forums_summaries))
            log.info("Les seuls établissements autorisés pour cet enseignant sont '%s'", themes_autorises)

        # Recuperation des inscriptions sur les forums qui ne devraient plus exister
        ids_enrolments_non_autorises, forums_summaries = self.__db.get_ids_and_summaries_not_allowed_enrolments(id_enseignant,
                                                                                                                shortnames_forums)
        # Suppression des inscriptions non autorisees
        if ids_enrolments_non_autorises:
            # Suppression des inscriptions
            self.__db.delete_user_enrolments(ids_enrolments_non_autorises)
            log.info("Suppression des inscriptions pour %s sur les forum '%s' ",
                     enseignant_infos, str(forums_summaries))
            log.info("Les seuls établissements autorisés pour cet enseignant sont '%s'", themes_autorises)

    def get_or_create_cohort(self, id_context: int, name: str, id_number: str,
                             description: str, time_created: int, log=getLogger()) -> int:
        """
        Fonction permettant de creer une nouvelle cohorte pour un contexte donné.

        :param id_context: L'id du contexte dans lequel on créé la cohorte
        :param name: Le nom de la cohorte
        :param id_number: L'id_number de la cohorte
        :param description: La description de la cohorte
        :param time_created: La date de création de la cohorte
        :return: L'id de la cohorte
        """
        id_cohort = self.__db.get_id_cohort(id_context, name)
        if id_cohort is None:
            self.__db.create_cohort(id_context, name, id_number, description, time_created)
            log.info("Creation de la cohorte (name=%s)", name)
            return self.__db.get_id_cohort(id_context, name)
        return id_cohort

    def get_cohort(self, id_context: int, name: str) -> int:
        """
        Fonction permettant de récupérer l'id d'une cohorte pour un contexte donné.

        :param id_context: Id du du contexte associé dans la table mdl_context
        :param name: Nom de la cohorte
        :return: L'id de la cohorte
        """
        return self.__db.get_id_cohort(id_context, name)

    def get_dane_lycee_en_cohort(self, id_context_dane: int, user_type: UserType) -> int:
        """
        Charge une cohorte dane lycee_en soit pour les élèves, les enseignants ou le personnel de direction.

        :param id_context_dane: Id du du contexte associé dans la table mdl_context
        :param user_type: Type d'utilisateurs de la cohorte
        :return: L'id de la cohorte
        """
        all_cohort_name = {
            UserType.ELEVE: 'Élèves des lycées de l\'éducation national',
            UserType.ENSEIGNANT: 'Enseignants des lycées de l\'éducation national',
            UserType.PERSONNEL_DE_DIRECTION: 'Personnel de direction des lycées de l\'éducation national'
        }
        cohort_name = all_cohort_name[user_type]
        id_cohort = self.get_cohort(id_context_dane, cohort_name)
        return id_cohort

    def get_or_create_dane_lycee_en_cohort(self, id_context_dane: int, user_type: UserType,
                                           timestamp_now_sql: int, log=getLogger()) -> int:
        """
        Charge ou créer une cohorte dane lycee_en soit pour les élèves, les enseignant ou le personnel de direction.

        :param id_context_dane: L'id du contexte dans lequel on créé la cohorte
        :param user_type: Le type d'utilisateur pour lequel on créé la cohorte
        :param timestamp_now_sql: La timestamp actuel
        :param log: Le logger
        :return: L'id de la cohorte récupérée
        """
        all_cohort_name = {
            UserType.ELEVE: 'Élèves des lycées de l\'éducation national',
            UserType.ENSEIGNANT: 'Enseignants des lycées de l\'éducation national',
            UserType.PERSONNEL_DE_DIRECTION: 'Personnel de direction des lycées de l\'éducation national'
        }
        cohort_name = all_cohort_name[user_type]
        cohort_description = cohort_name
        id_cohort = self.get_or_create_cohort(id_context_dane, cohort_name, cohort_name, cohort_description,
                                              timestamp_now_sql, log)
        return id_cohort

    def get_or_create_dane_dep_clg_cohort(self, id_context_dane: int, user_type: UserType,
                                          departement: str, timestamp_now_sql: int, log=getLogger()) -> int:
        """
        Charge ou créer une cohorte dane dep_clg soit pour les élèves, les enseignant ou le personnel de direction.

        :param id_context_dane: L'id du contexte dans lequel on créé la cohorte
        :param user_type: Le type d'utilisateur pour lequel on créé la cohorte
        :param departement: Le département associé à la cohorte
        :param timestamp_now_sql: La timestamp actuel
        :param log: Le logger
        :return: L'id de la cohorte récupérée
        """
        all_cohort_name = {
            UserType.ELEVE: 'Élèves des collèges du {}',
            UserType.ENSEIGNANT: 'Enseignants des collèges du {}',
            UserType.PERSONNEL_DE_DIRECTION: 'Personnel de direction des collèges du {}'
        }
        cohort_name = all_cohort_name[user_type].format(departement)
        cohort_description = cohort_name
        id_cohort = self.get_or_create_cohort(id_context_dane, cohort_name, cohort_name, cohort_description,
                                              timestamp_now_sql, log)
        return id_cohort

    def get_dane_dep_clg_cohort(self, id_context_dane, user_type: UserType, departement: str) -> int:
        """
        Charge ou créer une cohorte dane dep_clg soit pour les élèves, les enseignant ou le personnel de direction.

        :param id_context_dane: L'id du contexte dans lequel on créé la cohorte
        :param user_type: Le type d'utilisateur pour lequel on créé la cohorte
        :param departement: Le département associé à la cohorte
        :return: L'id de la cohorte récupérée
        """
        all_cohort_name = {
            UserType.ELEVE: 'Élèves des collèges du {}',
            UserType.ENSEIGNANT: 'Enseignants des collèges du {}',
            UserType.PERSONNEL_DE_DIRECTION: 'Personnel de direction des collèges du {}'
        }
        cohort_name = all_cohort_name[user_type].format(departement)
        id_cohort = self.get_cohort(id_context_dane, cohort_name)
        return id_cohort

    def get_or_create_formation_cohort(self, id_context_etab: int, niveau_formation: str,
                                       timestamp_now_sql: int, log=getLogger()) -> int:
        """
        Charge ou créer une cohorte de formation d'élèves.

        :param etab_context: Le contexte de l'établissement
        :param niveau_formation: Le niveau de formation
        :param timestamp_now_sql: Le timestamp actuel
        :param log: Le logger
        :return: L'id de la cohorte créée ou récupérée
        """
        cohort_name = self.__config.constantes.cohortname_pattern_eleves_niv_formation.replace("%",niveau_formation)
        cohort_idnumber = self.__config.constantes.cohortidnumber_pattern_eleves_niv_formation.replace("%",niveau_formation)
        cohort_description = self.__config.constantes.cohortdesc_pattern_eleves_niv_formation.replace("%",niveau_formation)
        id_cohort = self.get_or_create_cohort(id_context_etab, cohort_name, cohort_idnumber, cohort_description,
                                              timestamp_now_sql, log)
        return id_cohort

    def get_or_create_classes_cohorts(self, id_context_etab, classes_names, time_created, name_pattern=None,
                                      idnumber_pattern=None, desc_pattern=None, log=getLogger()) -> list[int]:
        """
        Charge ou crée des cohortes a partir de classes liées a un établissement.

        :param id_context_etab: Le contexte de l'établissement dans lequel on crée les cohortes
        :param classes_names: Les différentes classes dont on veut créer les cohortes
        :param time_created: La date de création de la cohorte si il y a création
        :param name_pattern: Le pattern à faire correspondre pour le nom de la cohorte
        :param desc_pattern: Le pattern à faire correspondre pour la description de la cohorte
        :param log: Le logger
        :return: La liste des ids des cohortes créees ou récupérées
        """
        ids_cohorts = []
        for class_name in classes_names:
            cohort_name = name_pattern % class_name
            cohort_idnumber = idnumber_pattern % class_name
            cohort_description = desc_pattern % class_name
            id_cohort = self.get_or_create_cohort(id_context_etab,
                                                  cohort_name,
                                                  cohort_idnumber,
                                                  cohort_description,
                                                  time_created,
                                                  log=log)
            ids_cohorts.append(id_cohort)
        return ids_cohorts

    def get_or_create_niv_formation_cohorts(self, id_context_etab: int, niveaux_formation: list[str],
     time_created: int, name_pattern: str, idnumber_pattern: str, desc_pattern: str, log=getLogger()) -> list[int]:
        """
        Charge ou crée des cohortes a partir de niveau de formation liés a un établissement.

        :param id_context_etab: Le contexte de l'établissement dans lequel on crée les cohortes
        :param niveaux_formation: Les différents niveaux de formation dont on veut créer les cohortes
        :param time_created: La date de création de la cohorte si il y a création
        :param name_pattern: Le pattern à faire correspondre pour le nom de la cohorte
        :param desc_pattern: Le pattern à faire correspondre pour la description de la cohorte
        :param log: Le logger
        :return: La liste des ids des cohortes créees ou récupérées
        """

        ids_cohorts = []
        for niveau_formation in niveaux_formation:
            cohort_name = name_pattern % niveau_formation
            cohort_idnumber = idnumber_pattern % niveau_formation
            cohort_description = desc_pattern % niveau_formation
            id_cohort = self.get_or_create_cohort(id_context_etab,
                                                  cohort_name,
                                                  cohort_idnumber,
                                                  cohort_description,
                                                  time_created,
                                                  log=log)
            ids_cohorts.append(id_cohort)
        return ids_cohorts

    def get_or_create_profs_etab_cohort(self, etab_context: EtablissementContext, log=getLogger()) -> int:
        """
        Charge ou crée la cohorte d'enseignant de l'établissement.

        :param etab_context: Le contexte de l'établissement
        :param log: Le logger
        :return: L'id de la cohorte d'enseignants de l'établissement
        """
        cohort_name = self.__config.constantes.cohortname_pattern_enseignants_etablissement.replace("%",f"({etab_context.uai})")
        cohort_idnumber = self.__config.constantes.cohortidnumber_pattern_enseignants_etablissement.replace("%",f"{etab_context.uai}")
        cohort_description = self.__config.constantes.cohortdesc_pattern_enseignants_etablissement.replace("%",f"{etab_context.uai}")
        id_cohort_enseignants = self.get_or_create_cohort(etab_context.id_context_categorie,
                                                          cohort_name,
                                                          cohort_idnumber,
                                                          cohort_description,
                                                          self.context.timestamp_now_sql,
                                                          log=log)
        return id_cohort_enseignants

    def get_users_by_cohorts_comparators_eleves_classes(self, etab_context: EtablissementContext,
     cohortname_pattern_re: str, cohortname_pattern: str, log=getLogger()) -> (Dict[str, List[str]], Dict[str, List[str]]):
        """
        Renvoie deux dictionnaires listant les élèves (uid) dans chacune des classes.
        Le premier dictionnaire contient les valeurs de la BDD, le second celles du LDAP.

        :param etab_context: Le contexte de l'établissement dans lequel on recherche les cohortes
        :param cohortname_pattern_re: Le pattern à faire correspondre pour le nom de la cohorte
        :param cohortname_pattern: Le pattern à faire correspondre pour le nom de la cohorte
        :return: Un tuple contenant les deux dictionnaires
        """
        # Récupére les cohortes qui correspondent au pattern et qui sont lié à l'établissement du context
        classes_cohorts = self.__db.get_user_filtered_cohorts(etab_context.id_context_categorie, cohortname_pattern)

        # Dictionnaire contenant la liste des élèves par cohorte provenant de la bdd
        eleves_by_cohorts_db = {}
        # Pour chaque cohorte de la bdd
        for cohort in classes_cohorts:
            matches = re.search(cohortname_pattern_re, cohort.name)
            if matches is not None:
                # On récupére le nom de la classe (fin du nom de la cohorte qui lui est fixe)
                classe_name = matches.group(2)
                # On créé le tableau vide pour y stocker les élèves
                eleves_by_cohorts_db[classe_name] = []
                # Et on stocke les élèves de cette cohorte en provenant ce la bdd
                for username in self.__db.get_cohort_members(cohort.id):
                    eleves_by_cohorts_db[classe_name].append(username.lower())
            else:
                log.warning("Nom de la cohorte %s dans la catégorie %d invalide",
                            cohort.name, etab_context.id_context_categorie)

        # Dictionnaire contenant la liste des élèves par cohorte provenant du ldap
        eleves_by_cohorts_ldap = {}
        # Pour chaque cohorte de la bdd
        for classe in eleves_by_cohorts_db:
            # On créé le tableau vide pour y stocker les élèves
            eleves_by_cohorts_ldap[classe] = []
            # Et on stocke les élèves de cette cohorte en provenant du ldap
            for eleve in self.__ldap.search_eleves_in_classe(classe, etab_context.uai):
                eleves_by_cohorts_ldap[classe].append(eleve.uid.lower())

        return eleves_by_cohorts_db, eleves_by_cohorts_ldap


    def get_users_by_cohorts_comparators_eleves_niveau(self, etab_context: EtablissementContext,
     cohortname_pattern_re: str, cohortname_pattern: str) -> (Dict[str, List[str]], Dict[str, List[str]]):
        """
        Renvoie deux dictionnaires listant les élèves (uid) dans chacun des niveaux de formation.
        Le premier dictionnaire contient les valeurs de la BDD, le second celles du LDAP.

        :param etab_context: Le contexte de l'établissement dans lequel on recherche les cohortes
        :param cohortname_pattern_re: Le pattern à faire correspondre pour le nom de la cohorte
        :param cohortname_pattern: Le pattern à faire correspondre pour le nom de la cohorte
        :return: Un tuple contenant les deux dictionnaires
        """
        level_cohorts = self.__db.get_user_filtered_cohorts(etab_context.id_context_categorie, cohortname_pattern)

        eleves_by_cohorts_db = {}
        for cohort in level_cohorts:
            matches = re.search(cohortname_pattern_re, cohort.name)
            classe_name = matches.group(2)
            eleves_by_cohorts_db[classe_name] = []
            for username in self.__db.get_cohort_members(cohort.id):
                eleves_by_cohorts_db[classe_name].append(username.lower())

        eleves_by_cohorts_ldap = {}
        for niveau in eleves_by_cohorts_db:
            eleves_by_cohorts_ldap[niveau] = []
            for eleve in self.__ldap.search_eleves_in_niveau(niveau, etab_context.uai):
                eleves_by_cohorts_ldap[niveau].append(eleve.uid.lower())

        return eleves_by_cohorts_db, eleves_by_cohorts_ldap

    def get_users_by_cohorts_comparators_profs_classes(self, etab_context: EtablissementContext,
     cohortname_pattern_re: str, cohortname_pattern: str) -> (Dict[str, List[str]], Dict[str, List[str]]):
        """
        Renvoie deux dictionnaires listant les profs (uid) dans chacune des classes.
        Le premier dictionnaire contient les valeurs de la BDD, le second celles du LDAP.

        :param etab_context: Le contexte de l'établissement dans lequel on recherche les cohortes
        :param cohortname_pattern_re: Le pattern à faire correspondre pour le nom de la cohorte
        :param cohortname_pattern: Le pattern à faire correspondre pour le nom de la cohorte
        :return: Un tuple contenant les deux dictionnaires
        """
        classes_cohorts = self.__db.get_user_filtered_cohorts(etab_context.id_context_categorie, cohortname_pattern)

        profs_by_cohorts_db = {}
        for cohort in classes_cohorts:
            matches = re.search(cohortname_pattern_re, cohort.name)
            classe_name = matches.group(2)
            profs_by_cohorts_db[classe_name] = []
            for username in self.__db.get_cohort_members(cohort.id):
                profs_by_cohorts_db[classe_name].append(username.lower())

        profs_by_cohorts_ldap = {}
        for classe in profs_by_cohorts_db:
            profs_by_cohorts_ldap[classe] = []
            for prof in self.__ldap.search_enseignants_in_classe(classe, etab_context.uai):
                profs_by_cohorts_ldap[classe].append(prof.uid.lower())

        return profs_by_cohorts_db, profs_by_cohorts_ldap


    def get_users_by_cohorts_comparators_profs_etab(self, etab_context: EtablissementContext,
     cohortname_pattern_re: str, cohortname_pattern: str) -> (Dict[str, List[str]], Dict[str, List[str]]):
        """
        Renvoie deux dictionnaires listant les profs (uid) dans chacun des établissement.
        Le premier dictionnaire contient les valeurs de la BDD, le second celles du LDAP.

        :param etab_context: Le contexte de l'établissement dans lequel on recherche les cohortes
        :param cohortname_pattern_re: Le pattern à faire correspondre pour le nom de la cohorte
        :param cohortname_pattern: Le pattern à faire correspondre pour le nom de la cohorte
        :return: Un tuple contenant les deux dictionnaires
        """
        etab_cohorts = self.__db.get_user_filtered_cohorts(etab_context.id_context_categorie, cohortname_pattern)

        profs_by_cohorts_db = {}
        for cohort in etab_cohorts:
            matches = re.search(cohortname_pattern_re, cohort.name)
            etab_name = matches.group(2)
            profs_by_cohorts_db[etab_name] = []
            for username in self.__db.get_cohort_members(cohort.id):
                profs_by_cohorts_db[etab_name].append(username.lower())

        profs_by_cohorts_ldap = {}
        for etab in profs_by_cohorts_db:
            profs_by_cohorts_ldap[etab] = []
            for prof in self.__ldap.search_enseignants_in_etab(etab_context.uai):
                profs_by_cohorts_ldap[etab].append(prof.uid.lower())

        return profs_by_cohorts_db, profs_by_cohorts_ldap


    def get_users_by_cohorts_comparators_profs_niveau(self, etab_context: EtablissementContext,
     cohortname_pattern_re: str, cohortname_pattern: str) -> (Dict[str, List[str]], Dict[str, List[str]]):
        """
        Renvoie deux dictionnaires listant les profs (uid) dans chacun des niveaux de formation.
        Le premier dictionnaire contient les valeurs de la BDD, le second celles du LDAP.

        :param etab_context: Le contexte de l'établissement dans lequel on recherche les cohortes
        :param cohortname_pattern_re: Le pattern à faire correspondre pour le nom de la cohorte
        :param cohortname_pattern: Le pattern à faire correspondre pour le nom de la cohorte
        :return: Un tuple contenant les deux dictionnaires
        """

        #Construit le dictionnaire pour avoir l'association classe -> niveau de formation
        self.construct_classe_to_niv_formation(etab_context,
                                               self.__ldap.search_eleve_classe_and_niveau(etab_context.uai))

        #Récupère les cohortes coté moodle
        levels_cohorts = self.__db.get_user_filtered_cohorts(etab_context.id_context_categorie, cohortname_pattern)

        profs_by_cohorts_db = {}
        for cohort in levels_cohorts:
            matches = re.search(cohortname_pattern_re, cohort.name)
            level_name = matches.group(2)
            profs_by_cohorts_db[level_name] = []
            for username in self.__db.get_cohort_members(cohort.id):
                profs_by_cohorts_db[level_name].append(username.lower())

        profs_by_cohorts_ldap = {}
        for niveau in profs_by_cohorts_db:
            profs_by_cohorts_ldap[niveau] = []
            for prof in self.__ldap.search_enseignants_in_niveau(niveau, etab_context.uai,
             etab_context.classe_to_niv_formation):
                profs_by_cohorts_ldap[niveau].append(prof.uid.lower())

        return profs_by_cohorts_db, profs_by_cohorts_ldap

    def backup_course(self, shortname: str, fullname: str, categoryid: int, log=getLogger()) -> bool:
        """
        Permet de copier le backup un cours.
        La règle de nommage est : backup-categorie-shortname-fullname-timestamp

        :param shortname: Le shortname du cours supprimé
        :param shortname: Le fullname du cours supprimé
        :param categoryid: L'id de la catégorie d'ou le cours a été supprimé
        """

        now = self.__db.get_timestamp_now()

        #URL ou est situé le fichier de backup
        url = self.__db.get_backup_course_file_url(categoryid, shortname)

        #On fait attention aux caractères génants dans le nom du fichier
        from_copy = self.__config.constantes.moodledatadir+"/filedir/"+url
        shortname = shortname.replace("-","_")
        fullname = fullname.replace("-","_")
        filename = "backup-"+str(categoryid)+"-"+shortname+"-"+fullname+"-"+str(now)+".mbz"
        filename = filename.replace("/","")
        re.sub(r'\W+', '', filename)
        to_copy = self.__config.constantes.backup_destination+"/"+filename

        #Copie du fichier
        log.debug("Copie de %s vers %s", from_copy, to_copy)
        shutil.copy(from_copy, to_copy)

        #Réécriture de l'ancien fichier pour le vider
        log.debug("Nettoyage du fichier %s", from_copy)
        old_file = open(from_copy, "w")
        old_file.write("")
        old_file.close()


    def check_and_process_user_courses(self, user_id: int, log=getLogger()):
        """
        Effectue les traitements nécéssaires sur tous les cours d'un l'enseignant.

        :param user_id: L'enseignant dont on doit traiter les cours
        :param log: Le logger
        """
        #Liste stockant tous les cours à supprimer
        courses_to_delete = set()
        #Récupère tous les cours de l'utilisateur
        user_courses = self.__db.get_courses_data_owned_or_teach(user_id)
        #Date actuelle
        now = self.__db.get_timestamp_now()

        #Pour chaque cours de l'utilisateur
        for (courseid,shortname,fullname,categoryid) in user_courses:
            log.info("Traitement du cours %d", courseid)
            #On récupère tous les Propriétaire de cours de ce cours
            owners_ids = [ownerid[0] for ownerid in self.__db.get_userids_owner_of_course(courseid)]
            #Si il est tout seul à posséder ce cours
            if len(owners_ids) == 1 and owners_ids[0] == user_id:
                #Récupération de la date de dernière modification
                timemodified = self.__db.get_course_timemodified(courseid)
                #Récupération du délai avant suppression du cours
                delay_backup_course = self.__config.delete.delay_backup_course

                #Test pour voir si le cours doit être supprimé
                if timemodified < now - (delay_backup_course * SECONDS_PER_DAY):
                    log.info("Le cours %d n'a pas été modifié depuis plus de %d jours,"
                             " et l'utilisateur %d est le seul propriétaire de ce cours,"
                             " il va donc être supprimé", courseid,
                             int((now - timemodified) / SECONDS_PER_DAY), user_id)
                    courses_to_delete.add((courseid,shortname,fullname,categoryid))

            #Sinon s'il n'est pas tout seul à posséder ce cours, on lui retire son rôle
            #Autrement dit on le désinscrit du cours
            else:
                log.info("L'utilisateur %d n'est pas le seul enseignant du cours %d, il va donc être désinscrit",\
                 user_id, courseid)
                self.__db.unenrol_user_from_course(courseid, user_id)

        #Commit pour libérer le lock pour le WebService
        self.__db.connection.commit()

        #Suppression des cours
        if courses_to_delete:
            self.delete_courses(courses_to_delete)

    def anonymize_or_delete_users(self, db_users: list[tuple], ldap_users: set[str], log=getLogger()):
        """
        Anonymise ou supprime les utilisateurs devenus inutiles.

        :param db_users: La liste de toutes les personnes dans moodle
        :param ldap_users: L'ensemble des uid de toutes les personnes dans le ldap
        :param log: Le logger
        """
        log.debug("Utilisateurs récupérés. Début de la procédure.")
        user_ids_to_delete = [] #Utilisateurs à supprimer
        user_ids_to_anonymize = [] #Utilisateurs à anonymiser
        user_ids_to_process_courses = [] #Enseignants dont les cours doivent subir un traitement
        now = self.__db.get_timestamp_now()
        is_teacher = False

        #Pour chaque utilisateur en BD
        for db_user in db_users:

            #Si jamais c'est un utilisateur à ne pas supprimer
            if db_user[0] in self.__config.delete.ids_users_undeletable:
                continue

            #Si l'utilisateur n'est plus présent dans l'annuaire LDAP, alors il faut faire un traitement
            if db_user[1] not in ldap_users:
                log.info("L'utilisateur %s n'est plus présent dans l'annuaire LDAP", db_user[1])
                #Dans tous les cas, si jamais il n'a jamais utilisé moodle alors on peut le supprimer
                if not self.__db.user_has_used_moodle(db_user[0]):
                    log.info("L'utilisateur %s n'a jamais utilisé moodle. Il va être supprimé", db_user[1])
                    user_ids_to_delete.append(db_user[0])

                #Traitement pour les utilisateurs ayant déjà utilisé moodle
                else:
                    #Booléen pour savoir si l'utilisateur qu'on traite est un enseignant ou non
                    is_teacher = self.__db.user_has_role(db_user[0], self.__config.delete.ids_roles_teachers)

                    #Récupération des délais avant anonymisation et avant suppression
                    delete_delay = self.__config.delete.delay_delete_teacher if is_teacher else \
                        self.__config.delete.delay_delete_student
                    anon_delay = self.__config.delete.delay_anonymize_teacher if is_teacher else \
                        self.__config.delete.delay_anonymize_student

                    #Récupération de la liste des cours de l'utilisateur
                    user_courses = self.__webservice.get_courses_user_enrolled(db_user[0])

                    #Si c'est un enseignant il ne faut pas tenir compte des cours ou il est propriétaire/enseignant
                    if is_teacher:
                        owned_courses = self.__db.get_courses_ids_owned_or_teach(db_user[0])
                        for course_owned in owned_courses:
                            if course_owned in user_courses:
                                user_courses.remove(course_owned)

                    #Cas ou on doit supprimer un élève : plus présent dans le ldap, et
                    #pas de connexion a moodle depuis plus de delay_force_delete jours
                    if not is_teacher:
                        if db_user[2] < now - (self.__config.delete.delay_force_delete * SECONDS_PER_DAY):
                            log.info("L'élève %s ne s'est pas connecté depuis au moins %s jours. Il va être supprimé",\
                             db_user[1], self.__config.delete.delay_force_delete)
                            user_ids_to_delete.append(db_user[0])

                    #Suite du traitement si on ne sait pas encore si on doit supprimer l'utilisateur
                    if db_user[0] not in user_ids_to_delete:

                        #Cas ou on doit supprimer un utilisateur : plus présent dans le ldap
                        #et pas de connection à moodle depuis plus de delete_delay jours
                        if db_user[2] < now - (delete_delay * SECONDS_PER_DAY):
                            if len(user_courses) == 0: #inscription à aucun cours
                                #Différence de traitement au niveau des références entre un enseignant et un élève
                                if is_teacher:
                                    if not self.__db.enseignant_has_references(db_user[0]): #si pas de références
                                        log.info("L'enseignant %s ne s'est pas connecté depuis au moins %s jours"
                                                 " et n'est pas inscrit à un cours, ni ne possède de référénces."
                                                 " Il va être supprimé", db_user[1], delete_delay)
                                        user_ids_to_delete.append(db_user[0])
                                else:
                                    if not self.__db.eleve_has_references(db_user[0]): #si pas de références
                                        log.info("L'élève %s ne s'est pas connecté depuis au moins %s jours"
                                                 " et n'est pas inscrit à un cours, ni ne possède de référénces."
                                                 " Il va être supprimé", db_user[1], delete_delay)
                                        user_ids_to_delete.append(db_user[0])

                        if db_user[0] not in user_ids_to_delete:
                            #Cas ou on doit anonymiser un utilisateur : plus présent dans le ldap,
                            #pas inscrit dans un seul cours avec le rôle propriétaire ou enseignant,
                            #et pas de connection à moodle depuis plus de anon_delay jours
                            if db_user[2] < now - (anon_delay * SECONDS_PER_DAY): #délai de connexion
                                #Différence de traitement au niveau des références entre un enseignant et un élève
                                if is_teacher:
                                    #On vérifie que l'enseignant n'est pas inscrit dans un seul cours
                                    #avec le rôle propriétaire ou enseignant
                                    if len(self.__db.get_courses_ids_owned_or_teach(db_user[0])) == 0:
                                        #S'il doit être anonymisé, on vérifie qu'il ne l'est pas déjà
                                        if self.__db.get_user_data(db_user[0])[10] != self.__config.constantes.anonymous_name:
                                            log.info("L'enseignant %s ne s'est pas connecté depuis au moins %s jours"
                                                     " et est inscrit à des cours ou possèdes des références."
                                                     " Il va être anonymisé", db_user[1], anon_delay)
                                            user_ids_to_anonymize.append(db_user[0])
                                        else:
                                            log.info("L'enseignant %s doit être anonymisé, mais il est déja anonymisé",
                                             db_user[1])
                                else:
                                    #Même principe pour les élèves
                                    if self.__db.get_user_data(db_user[0])[10] != self.__config.constantes.anonymous_name:
                                        log.info("L'élève %s ne s'est pas connecté depuis au moins %s jours"
                                                 " et est inscrit à des cours ou possèdes des références."
                                                 " Il va être anonymisé", db_user[1], anon_delay)
                                        user_ids_to_anonymize.append(db_user[0])
                                    else:
                                        log.info("L'élève %s doit être anonymisé, mais il est déja anonymisé",
                                                 db_user[1])

                            #Cas ou on doit effectuer un traitement sur les cours d'un prof : plus présent dans le ldap,
                            #inscrit avec le role propriétaire de cours
                            #ou enseignant dans au moins 1 cours,
                            #et pas de connection à moodle depuis plus de delay_backup_course jours
                            if is_teacher and (db_user[2] < now - (self.__config.delete.delay_backup_course * SECONDS_PER_DAY)):
                                owned_or_teach_courses = [user_course[0] for user_course in self.__db.get_courses_ids_owned_or_teach(db_user[0])]
                                if len(owned_or_teach_courses) > 0:
                                    log.info("L'enseignant %s ne s'est pas connecté depuis au moins %s jours. "
                                             "Un traitement va être effectué sur ses cours",
                                             db_user[1], self.__config.delete.delay_backup_course)
                                    user_ids_to_process_courses.append(db_user[0])

        #Traitement sur les cours des enseignants
        for user_id in user_ids_to_process_courses:
            log.info("Traitement des cours de l'enseignant %s", user_id)
            self.check_and_process_user_courses(user_id, log=log)

        #Libération mémoire
        del user_ids_to_process_courses

        #On supprime les utilisateurs en fonction de user_ids_to_delete
        if user_ids_to_delete:
            log.info("Suppression des utilisateurs en cours...")
            self.delete_users(user_ids_to_delete, log=log)
            log.info("%d utilisateurs supprimés", len(user_ids_to_delete))

        #Libération mémoire
        del user_ids_to_delete

        #Ici on peut perdre la connection à la BD si la suppression à pris trop de temps
        #Si on est plus connecté, on va donc se reconnecter
        if not self.__db.connection.is_connected():
            self.__db.connection.reconnect(attempts=5, delay=1)

        #On anonymise les utilisateurs en fonction de user_ids_to_anonymize
        if user_ids_to_anonymize:
            log.info("Anonymisation des utilisateurs en cours...")
            self.__db.anonymize_users(user_ids_to_anonymize)
            log.info("%d utilisateurs anonymisés", len(user_ids_to_anonymize))
        #Pas la peine de libérer la mémoire ici dans la mesure ou on sort de la fonction


    def delete_empty_cohorts(self, log=getLogger()):
        """
        Supprime les cohortes vides en paginant les appels au WebService.

        :param log: Le logger
        """
        #Récupère les ids des cohortes
        empty_cohorts_ids = self.__db.get_empty_cohorts()
        if len(empty_cohorts_ids) > 0:
            #Fait appel au webservice moodle pour suppression
            pagesize = 50
            i = 0
            total = len(empty_cohorts_ids)
            empty_cohorts_ids_page = []
            for cohort_id in empty_cohorts_ids:
                empty_cohorts_ids_page.append(cohort_id)
                i += 1
                if i % pagesize == 0:
                    self.__webservice.delete_cohorts(empty_cohorts_ids_page)
                    empty_cohorts_ids_page = []
                    log.info("%d / %d cohortes supprimées", i, total)
            if i % pagesize > 0:
                self.__webservice.delete_cohorts(empty_cohorts_ids_page)
                log.info("%d / %d cohortes supprimées", i, total)


    def delete_users(self, userids: List[int], log=getLogger()):
        """
        Supprime les utilisateurs d'une liste en paginant les appels au webservice.

        :param userids: La liste des id des utilisateurs à supprimer
        :param pagesize: Le nombre d'utilisateurs supprimés en un seul appel au webservice
        :param log: Le logger
        """
        pagesize = self.__config.webservice.user_delete_pagesize
        i = 0
        total = len(userids)
        userids_page = []
        for userid in userids:
            userids_page.append(userid)
            i += 1
            if i % pagesize == 0:
                self.__webservice.delete_users(userids_page)
                userids_page = []
                log.info("%d / %d utilisateurs supprimés", i, total)
        if i % pagesize > 0:
            self.__webservice.delete_users(userids_page)
            log.info("%d / %d utilisateurs supprimés", i, total)


    def delete_courses(self, courses_to_delete: list[tuple[int,str,str,int]], log=getLogger()):
        """
        Supprime les cours d'une liste en faisant appel au webservice.
        Copie le backup du cours dans un répertoire configuré.

        :param courses_to_delete: La liste des cours à supprimer
        :param log: Le logger
        """

        #Pour chaque cours à supprimer
        for (courseid, shortname, fullname, categoryid) in courses_to_delete:
            #Suppression du cours
            log.debug("Suppression du cours %d", courseid)
            self.__webservice.delete_course(courseid)
            log.info("Le cours %d a été supprimé", courseid)
            #Faire apparaître la ligne avec le fichier de backup dans la table mdl_files
            self.__db.connection.commit()
            #Copie du backup du cours
            log.debug("Début de la procédure de copie du backup")
            self.backup_course(shortname, fullname, categoryid)
            log.info("Le backup du cours %d a été copié", courseid)


    def purge_cohorts(self, users_by_cohorts_db: Dict[str, List[str]],
                      users_by_cohorts_ldap: Dict[str, List[str]],
                      cohortname_pattern: str,
                      log=getLogger()):
        """
        Vide les cohortes d'utilisateurs conformément à l'annuaire LDAP.

        :param users_by_cohorts_db: L'association nom de cohorte moodle et liste de ses utilisateurs
        :param users_by_cohorts_ldap: L'association nom de cohorte ldap et liste de ses utilisateurs
        :param cohortname_pattern: Le pattern à faire correspondre pour le nom des cohortes
        :param log: Le logger
        """
        # On boucle avec à chaque fois une cohorte et son tableau d'élèves de la bdd
        for cohort_db, eleves_db in users_by_cohorts_db.items():
            # Calcul du nom complet de la cohorte
            cohortname = cohortname_pattern % cohort_db
            # Si la cohorte n'est pas présente dans le ldap
            # (ce qui ne doit pas être possible, au pire on a un tableau vide)
            # On désenrole les users de la cohortes côté bdd
            if cohort_db not in users_by_cohorts_ldap:
                for username_db in users_by_cohorts_db[cohort_db]:
                    log.info("Désenrollement de l'utilisateur %s de la cohorte \"%s\"", username_db, cohort_db)
                    self.__db.disenroll_user_from_username_and_cohortname(username_db, cohortname)
            # Sinon, on test pour chaque user si il est présent, et si il est absent on le désenrole
            else:
                for username_db in eleves_db:
                    if username_db not in users_by_cohorts_ldap[cohort_db]:
                        log.info("Désenrollement de l'utilisateur %s de la cohorte \"%s\"", username_db, cohort_db)
                        self.__db.disenroll_user_from_username_and_cohortname(username_db, cohortname)

    def purge_specific_cohort(self, users_by_cohorts_db: List[str],
                                    users_by_cohorts_ldap: List[str],
                                    cohortname: str,
                                    log=getLogger()):
        """
        Vide une cohorte d'utilisateurs conformément à l'annuaire LDAP.

        :param users_by_cohorts_db: La liste des utilisateurs de la cohorte dans moodle
        :param users_by_cohorts_ldap: La liste des utilisateurs qui doivent être dans la cohorte dans le ldap
        :param cohortname: Le nom de la cohorte dans moodle
        :param log: Le logger
        """
        #On boucle pour chaque utilisateur dans la BD et on regarde s'il est censé y être dans le ldap
        for username_db in users_by_cohorts_db:
            if username_db not in users_by_cohorts_ldap:
                log.info("Désenrollement de l'utilisateur %s de la cohorte \"%s\"", username_db, cohortname)
                self.__db.disenroll_user_from_username_and_cohortname(username_db, cohortname)

    def purge_cohort_dane_lycee_en(self, lycee_ldap: dict, log=getLogger()) -> dict[str,list[str]]:
        """
        Purge les cohortes dane des différents types d'utilisateurs dans les lycées.

        :param lycee_ldap: Les utilisateurs des cohortes dane lycées par type d'utilisateur
        """
        #Pour chaque cohorte de chaque type d'utilisateur
        for user_type in UserType:

            log.info("Purge de la cohorte dane %s", user_type.name.capitalize())

            # Récupération des username des utilisateurs de la cohorte en db
            lycee_en_db = self.__db.get_cohort_members_list(self.ids_cohorts_dane_lycee_en[user_type])

            # Boucle sur chaques user en db et le désenrole si il n'est pas rpésent dans le ldap
            for username_db in lycee_en_db:
                if username_db not in lycee_ldap[user_type]:
                    log.info("Désenrollement de l'utilisateur %s de la cohorte dane lycée %s",
                     username_db, user_type)
                    self.__db.disenroll_user_from_username_and_cohortid(username_db,
                                                                        self.ids_cohorts_dane_lycee_en[user_type])

    def purge_cohort_dane_clg_dep(self, clg_ldap: dict, departement: str, log=getLogger()) -> dict[str,list[str]]:
        """
        Purge les cohortes dane des différents types d'utilisateurs dans les collèges par département.

        :param lycee_ldap: Les utilisateurs des cohortes dane collège par type d'utilisateur et département
        :param log: Le logger
        """
        #Pour chaque cohorte de chaque type d'utilisateur
        for user_type in UserType:

            log.info("Purge de la cohorte dane %s", user_type.name.capitalize())

            # Récupération des username des utilisateurs de la cohorte en db
            clg_en_db = self.__db.get_cohort_members_list(self.ids_cohorts_dane_dep_clg[user_type][departement])

            # Boucle sur chaques user en db et le désenrole si il n'est pas rpésent dans le ldap
            for username_db in clg_en_db:
                if username_db not in clg_ldap[user_type]:
                    log.info("Désenrollement de l'utilisateur %s de la cohorte dane collège %s du %s",
                     username_db, user_type, departement)
                    self.__db.disenroll_user_from_username_and_cohortid(
                        username_db,
                        self.ids_cohorts_dane_dep_clg[user_type][departement]
                    )

    def mise_a_jour_cohorte_interetab(self, is_member_of: str, cohort_name: str, since_timestamp: datetime.datetime,
                                      log=getLogger()):
        """
        Met à jour une cohorte inter-etablissement.

        :param is_member_of: La filtre pour identifier des utilisateurs interEtablissements
        :param cohort_name: Le nom de la cohorte d'utilisateurs inter_etabs
        :param since_timestamp: Le timestamp au delà duquel on ne traite pas les utilisateurs
        :param log: Le logger
        """

        #Récupération du contexte à partir du nom de la catégorie paramétrée dans l'action
        id_categorie_inter_etabs_action = self.__db.get_id_categorie(self.__action_config.inter_etablissements.categorie_name)
        id_context_categorie_inter_etabs_action = self.__db.get_id_context_categorie(id_categorie_inter_etabs_action)

        # Creation de la cohort si necessaire
        self.get_or_create_cohort(id_context_categorie_inter_etabs_action, cohort_name, cohort_name,
                                  cohort_name, self.context.timestamp_now_sql, log=log)
        id_cohort = self.__db.get_id_cohort(id_context_categorie_inter_etabs_action, cohort_name)

        # Recuperation des utilisateurs
        is_member_of_list = [is_member_of]

        # Ajout des utilisateurs dans la cohorte
        for personne_ldap in self.__ldap.search_personne(
                since_timestamp = since_timestamp,
                isMemberOf = is_member_of_list):
            user_id = self.__db.get_user_id(personne_ldap.uid)
            if user_id:
                self.__db.enroll_user_in_cohort(id_cohort, user_id, self.context.timestamp_now_sql)
            else:
                log.warning("Impossible d'inserer l'utilisateur %s dans la cohorte %s, "
                            "car il n'est pas connu dans Moodle", personne_ldap, cohort_name)

    def purge_cohorte_interetab(self, is_member_of: str, cohort_name: str, log=getLogger()):
        """
        Purge une cohorte inter-etablissement.

        :param is_member_of: La filtre pour identifier des utilisateurs interEtablissements
        :param cohort_name: Le nom de la cohorte d'utilisateurs inter_etabs
        :param log: Le logger
        """
        #Récupération du contexte à partir du nom de la catégorie paramétrée dans l'action
        id_categorie_inter_etabs_action = self.__db.get_id_categorie(self.__action_config.inter_etablissements.categorie_name)
        id_context_categorie_inter_etabs_action = self.__db.get_id_context_categorie(id_categorie_inter_etabs_action)

        # Récupération de la cohorte
        id_cohort = self.__db.get_id_cohort(id_context_categorie_inter_etabs_action, cohort_name)

        #Récupération des utilisateurs dans la cohorte dans la bd
        user_in_cohort_bd = self.__db.get_cohort_members_list(id_cohort)

        # Récupération des utilisateurs du ldap qui doivent être dans la cohorte
        is_member_of_list = [is_member_of]
        user_in_cohort_ldap = self.__ldap.search_personne_uid(since_timestamp = None, isMemberOf = is_member_of_list)

        #Pour chaque utilisateur de la cohorte en bd qui n'est pas dans ceux du ldap, on le désinscrit de la cohorte
        for user_in_bd in user_in_cohort_bd:
            if user_in_bd not in user_in_cohort_ldap:
                log.info("Désinscription de l'utilisateur %s de la cohorte %s", user_in_bd, cohort_name)
                self.__db.disenroll_user_from_username_and_cohortname(user_in_bd, cohort_name)


    def insert_moodle_structure(self, grp: bool, nom_structure: str, path: str,
     ou: str, siren: str, uai: str):
        """
        Fonction permettant d'inserer une structure dans Moodle.

        :param grp: Si la strucutre fait partie d'un groupement
        :param nom_structure: Le nom de la structure
        :param path: Le path de la structure
        :param ou: L'ou de la structure
        :param siren: Le siren de la structure
        :param uai: L'uai de la structure
        """
        # Recuperation du timestamp
        now = self.__db.get_timestamp_now()

        # Creation de la description pour la structure
        description = siren
        if grp:
            description = siren + "@" + nom_structure

        #########################
        # PARTIE CATEGORIE
        #########################
        # Insertion de la categorie correspondant a l'etablissement
        self.__db.insert_moodle_course_category(ou, description, description, uai)
        id_categorie_etablissement = self.__db.get_id_course_category_by_id_number(siren)

        # Mise a jour du path de la categorie
        path_etablissement = f"/{id_categorie_etablissement}"
        self.__db.update_course_category_path(id_categorie_etablissement, path_etablissement)

        #########################
        # PARTIE CONTEXTE
        #########################
        # Insertion du contexte associe a la categorie de l'etablissement
        self.__db.insert_moodle_context(self.__config.constantes.niveau_ctx_categorie,
                                        PROFONDEUR_CTX_ETAB,
                                        id_categorie_etablissement)
        id_contexte_etablissement = self.__db.get_id_context(self.__config.constantes.niveau_ctx_categorie,
                                                             PROFONDEUR_CTX_ETAB,
                                                             id_categorie_etablissement)

        # Mise a jour du path de la categorie
        path_contexte_etablissement = f"{path}/{id_contexte_etablissement}"
        self.__db.update_context_path(id_contexte_etablissement, path_contexte_etablissement)

        #########################
        # PARTIE ZONE PRIVEE
        #########################
        # Insertion du cours pour le forum de discussion
        id_zone_privee = self.__db.insert_zone_privee(id_categorie_etablissement, siren, ou, now)

        # Insertion du contexte associe
        id_contexte_zone_privee = self.__db.insert_zone_privee_context(id_zone_privee)

        # Mise a jour du path du contexte
        path_contexte_zone_privee = f"{path_contexte_etablissement}/{id_contexte_zone_privee}"
        self.__db.update_context_path(id_contexte_zone_privee, path_contexte_zone_privee)

        #########################
        # PARTIE INSCRIPTIONS
        #########################
        # Ouverture du cours a l'inscription manuelle
        role_id = self.__config.constantes.id_role_eleve
        self.__db.insert_moodle_enrol_capability("manual", 0, id_zone_privee, role_id)

        #########################
        # PARTIE FORUM
        #########################
        # Insertion du forum au sein de la zone privee
        course = id_zone_privee
        name = FORUM_NAME_ZONE_PRIVEE % ou
        intro = FORUM_INTRO_ZONE_PRIVEE
        intro_format = FORUM_INTRO_FORMAT_ZONE_PRIVEE
        max_bytes = FORUM_MAX_BYTES_ZONE_PRIVEE
        max_attachements = FORUM_MAX_ATTACHEMENTS_ZONE_PRIVEE
        time_modified = now

        id_forum = self.__db.get_id_forum(course)
        if id_forum is None:
            self.__db.insert_moodle_forum(course, name, intro, intro_format, max_bytes, max_attachements, time_modified)
            id_forum = self.__db.get_id_forum(course)

        #########################
        # PARTIE MODULE
        #########################
        # Insertion du module forum dans la zone privee
        course = id_zone_privee
        module = COURSE_MODULES_MODULE
        instance = id_forum
        added = now
        id_course_module = self.__db.get_id_course_module(course)
        if id_course_module is None:
            self.__db.insert_moodle_course_module(course, module, instance, added)
            id_course_module = self.__db.get_id_course_module(course)

        # Insertion du contexte pour le module de cours (forum)
        id_contexte_module = self.__db.get_id_context(self.__config.constantes.niveau_ctx_forum,
                                                      PROFONDEUR_CTX_MODULE_ZONE_PRIVEE,
                                                      id_course_module)
        if id_contexte_module is None:
            self.__db.insert_moodle_context(self.__config.constantes.niveau_ctx_forum,
                                            PROFONDEUR_CTX_MODULE_ZONE_PRIVEE,
                                            id_course_module)
            id_contexte_module = self.__db.get_id_context(self.__config.constantes.niveau_ctx_forum,
                                                          PROFONDEUR_CTX_MODULE_ZONE_PRIVEE,
                                                          id_course_module)

        # Mise a jour du path du contexte
        path_contexte_module = f"{path_contexte_zone_privee}/{id_contexte_module}"
        self.__db.update_context_path(id_contexte_module, path_contexte_module)

        #########################
        # PARTIE BLOC
        #########################
        # Insertion du bloc de recherche forum
        parent_context_id = id_contexte_zone_privee
        block_name = BLOCK_FORUM_SEARCH_NAME
        show_in_subcontexts = BLOCK_FORUM_SEARCH_SHOW_IN_SUB_CTX
        page_type_pattern = BLOCK_FORUM_SEARCH_PAGE_TYPE_PATTERN
        sub_page_pattern = BLOCK_FORUM_SEARCH_SUB_PAGE_PATTERN
        default_region = BLOCK_FORUM_SEARCH_DEFAULT_REGION
        default_weight = BLOCK_FORUM_SEARCH_DEFAULT_WEIGHT

        id_block = self.__db.get_id_block(parent_context_id)
        if id_block is None:
            self.__db.insert_moodle_block(block_name, parent_context_id, show_in_subcontexts, page_type_pattern,
                                          sub_page_pattern, default_region, default_weight)
            id_block = self.__db.get_id_block(parent_context_id)

        # Insertion du contexte pour le bloc
        id_contexte_bloc = self.__db.get_id_context(self.__config.constantes.niveau_ctx_bloc,
                                                    PROFONDEUR_CTX_BLOCK_ZONE_PRIVEE,
                                                    id_block)
        if id_contexte_bloc is None:
            self.__db.insert_moodle_context(self.__config.constantes.niveau_ctx_bloc,
                                            PROFONDEUR_CTX_BLOCK_ZONE_PRIVEE,
                                            id_block)
            id_contexte_bloc = self.__db.get_id_context(self.__config.constantes.niveau_ctx_bloc,
                                                        PROFONDEUR_CTX_BLOCK_ZONE_PRIVEE,
                                                        id_block)

        # Mise a jour du path du contexte
        path_contexte_bloc = f"{path_contexte_zone_privee}/{id_contexte_bloc}"
        self.__db.update_context_path(id_contexte_bloc, path_contexte_bloc)
