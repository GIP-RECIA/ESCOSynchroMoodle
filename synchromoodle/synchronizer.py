# coding: utf-8
import datetime
import re
from logging import getLogger
from typing import Dict, List

from synchromoodle.ldaputils import StructureLdap
from .arguments import default_args
from .config import EtablissementsConfig, Config, ActionConfig
from .dbutils import Database, PROFONDEUR_CTX_ETAB, COURSE_MODULES_MODULE, PROFONDEUR_CTX_MODULE_ZONE_PRIVEE, \
    PROFONDEUR_CTX_BLOCK_ZONE_PRIVEE
from .ldaputils import Ldap, EleveLdap, EnseignantLdap, PersonneLdap

#######################################
# FORUM
#######################################
# Nom du forum pour la zone privee 
# Le (%s) est reserve a l'organisation unit de l'etablissement
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


def est_grp_etab(uai: str, etablissements_config: EtablissementsConfig):
    """
    Indique si un établissement fait partie d'un regroupement d'établissement ou non
    :param uai: code de l'établissement
    :param etablissements_config: EtablissementsConfig
    :return: True si l'établissement fait partie d'un regroupement d'établissement
    """
    for regroupement in etablissements_config.etabRgp:
        if uai in regroupement.uais:
            return regroupement
    return False


class SyncContext:
    def __init__(self):
        self.timestamp_now_sql = None
        self.map_etab_domaine = None  # type: Dict[str, List[str]]
        self.id_context_categorie_inter_etabs = None  # type: int
        self.id_context_categorie_inter_cfa = None  # type: int
        self.id_role_extended_teacher = None  # type: int
        self.id_role_advanced_teacher = None  # type: int
        self.id_field_classe = None  # type: int
        self.id_field_domaine = None  # type: int
        self.utilisateurs_by_cohortes = {}


class EtablissementContext:
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


class Synchronizer:
    def __init__(self, ldap: Ldap, db: Database, config: Config, action_config: ActionConfig = None,
                 arguments=default_args):
        self.__ldap = ldap  # type: Ldap
        self.__db = db  # type: Database
        self.__config = config  # type: Config
        self.__action_config = action_config if action_config else next(iter(config.actions), ActionConfig())  # type: ActionConfig
        self.__arguments = arguments
        self.context = None  # type: SyncContext

    def initialize(self):

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

    def handle_etablissement(self, uai, log=getLogger()) -> EtablissementContext:
        """
        Met a jour l'etablissement meme si celui-ci n'a pas ete modifie depuis la derniere synchro
        car des infos doivent etre recuperees dans Moodle dans tous les cas
        :return: EtabContext
        """
        context = EtablissementContext(uai)
        context.gere_admin_local = uai not in self.__action_config.etablissements.listeEtabSansAdmin
        context.etablissement_regroupe = est_grp_etab(uai, self.__action_config.etablissements)
        # Regex pour savoir si l'utilisateur est administrateur moodle
        context.regexp_admin_moodle = self.__action_config.etablissements.prefixAdminMoodleLocal + ".*_%s$" % uai
        # Regex pour savoir si l'utilisateur est administrateur local
        context.regexp_admin_local = self.__action_config.etablissements.prefixAdminLocal + ".*_%s$" % uai

        log.debug("Recherche de la structure dans l'annuaire")
        structure_ldap = self.__ldap.get_structure(uai)
        if structure_ldap:
            log.debug("La structure a été trouvée")
            etablissement_path = "/1"

            # Si l'etablissement fait partie d'un groupement
            if context.etablissement_regroupe:
                etablissement_ou = context.etablissement_regroupe["nom"]
                structure_ldap.uai = context.etablissement_regroupe["uais"][0]
                log.debug("L'établissement fait partie d'un groupement: ou=%s, uai=%s" % (
                    etablissement_ou, structure_ldap.uai))
            else:
                etablissement_ou = structure_ldap.nom
                log.debug("L'établissement ne fait partie d'un groupement: ou=%s" % etablissement_ou)

            # Recuperation du bon theme
            context.etablissement_theme = structure_ldap.uai.lower()

            # Creation de la structure si elle n'existe pas encore
            id_etab_categorie = self.__db.get_id_course_category_by_theme(context.etablissement_theme)
            if id_etab_categorie is None:
                log.info("Création de la structure dans Moodle")
                self.insert_moodle_structure(context.etablissement_regroupe, structure_ldap.nom,
                                             etablissement_path, etablissement_ou,
                                             structure_ldap.siren, context.etablissement_theme)
                id_etab_categorie = self.__db.get_id_course_category_by_id_number(structure_ldap.siren)

            # Mise a jour de la description dans la cas d'un groupement d'etablissement
            if context.etablissement_regroupe:
                description = self.__db.get_description_course_category(id_etab_categorie)
                if description.find(structure_ldap.siren) == -1:
                    log.info("Mise à jour de la description")
                    description = "%s$%s@%s" % (description, structure_ldap.siren, structure_ldap.nom)
                    self.__db.update_course_category_description(id_etab_categorie, description)
                    self.__db.update_course_category_name(id_etab_categorie, etablissement_ou)

            # Recuperation de l'id du contexte correspondant à l'etablissement
            context.id_context_categorie = self.__db.get_id_context_categorie(id_etab_categorie)
            context.id_zone_privee = self.__db.get_id_course_by_id_number("ZONE-PRIVEE-" + structure_ldap.siren)

            # Recreation de la zone privee si celle-ci n'existe plus
            if context.id_zone_privee is None:
                log.info("Création de la zone privée")
                context.id_zone_privee = self.__db.insert_zone_privee(id_etab_categorie, structure_ldap.siren,
                                                                      etablissement_ou, self.context.timestamp_now_sql)

            context.id_context_course_forum = self.__db.get_id_context(self.__config.constantes.niveau_ctx_cours, 3,
                                                                       context.id_zone_privee)
            if context.id_context_course_forum is None:
                log.info("Création du cours associé à la zone privée")
                context.id_context_course_forum = self.__db.insert_zone_privee_context(context.id_zone_privee)

            context.structure_ldap = structure_ldap
        return context

    def handle_eleve(self, etablissement_context: EtablissementContext, eleve_ldap: EleveLdap, log=getLogger()):
        mail_display = self.__config.constantes.default_mail_display
        if not eleve_ldap.mail:
            eleve_ldap.mail = self.__config.constantes.default_mail
            log.info("Le mail de l'élève n'est pas défini dans l'annuaire, "
                     "utilisation de la valeur par défault: %s" % eleve_ldap.mail)

        eleve_id = self.__db.get_user_id(eleve_ldap.uid)
        if not eleve_id:
            log.info("Ajout de l'utilisateur: %s" % eleve_ldap)
            self.__db.insert_moodle_user(eleve_ldap.uid, eleve_ldap.given_name,
                                         eleve_ldap.given_name, eleve_ldap.mail,
                                         mail_display, etablissement_context.etablissement_theme)
            eleve_id = self.__db.get_user_id(eleve_ldap.uid)
        else:
            log.info("Mise à jour de l'utilisateur: %s" % eleve_ldap)
            self.__db.update_moodle_user(eleve_id, eleve_ldap.given_name,
                                         eleve_ldap.given_name, eleve_ldap.mail, mail_display,
                                         etablissement_context.etablissement_theme)

        # Ajout ou suppression du role d'utilisateur avec droits limités Pour les eleves de college
        if etablissement_context.structure_ldap.type == self.__config.constantes.type_structure_clg:
            log.info("Ajout du rôle droit limités à l'utilisateur: %s" % eleve_ldap)
            self.__db.add_role_to_user(self.__config.constantes.id_role_utilisateur_limite,
                                       self.__config.constantes.id_instance_moodle, eleve_id)
        else:
            self.__db.remove_role_to_user(self.__config.constantes.id_role_utilisateur_limite,
                                          self.__config.constantes.id_instance_moodle, eleve_id)
            log.info(
                "      |_ Suppression du role d'utilisateur avec des droits limites à l'utilisateur %s %s %s (id = %s)"
                % (eleve_ldap.given_name, eleve_ldap.sn, eleve_ldap.uid, str(eleve_id)))

        # Inscription dans les cohortes associees aux classes
        eleve_cohorts = []
        if eleve_ldap.classes:
            log.info("Inscription de l'élève %s "
                     "dans les cohortes de classes %s" % (eleve_ldap, eleve_ldap.classes))
            ids_classes_cohorts = self.create_classes_cohorts(etablissement_context.id_context_categorie,
                                                              eleve_ldap.classes,
                                                              self.context.timestamp_now_sql)
            for ids_classe_cohorts in ids_classes_cohorts:
                self.__db.enroll_user_in_cohort(ids_classe_cohorts, eleve_id, self.context.timestamp_now_sql)

            eleve_cohorts.extend(ids_classes_cohorts)

        # Inscription dans la cohorte associee au niveau de formation
        if eleve_ldap.niveau_formation:
            log.info("Inscription de l'élève %s "
                     "dans la cohorte de niveau de formation %s" % (eleve_ldap, eleve_ldap.niveau_formation))
            id_formation_cohort = self.create_formation_cohort(etablissement_context.id_context_categorie,
                                                               eleve_ldap.niveau_formation,
                                                               self.context.timestamp_now_sql)
            self.__db.enroll_user_in_cohort(id_formation_cohort, eleve_id, self.context.timestamp_now_sql)
            eleve_cohorts.append(id_formation_cohort)

        log.info("Désinscription de l'élève %s des anciennes cohortes" % eleve_ldap)
        self.__db.disenroll_user_from_cohorts(eleve_cohorts, eleve_id)

        # Mise a jour des dictionnaires concernant les cohortes
        for cohort_id in eleve_cohorts:
            # Si la cohorte est deja connue
            if cohort_id in etablissement_context.eleves_by_cohortes:
                etablissement_context.eleves_by_cohortes[cohort_id].append(eleve_id)
            # Si la cohorte n'a pas encore ete rencontree
            else:
                etablissement_context.eleves_by_cohortes[cohort_id] = [eleve_id]

        # Mise a jour de la classe
        id_user_info_data = self.__db.get_id_user_info_data(eleve_id, self.context.id_field_classe)
        if id_user_info_data is not None:
            self.__db.update_user_info_data(eleve_id, self.context.id_field_classe, eleve_ldap.classe)
            log.debug("Mise à jour user_info_data")
        else:
            self.__db.insert_moodle_user_info_data(eleve_id, self.context.id_field_classe,
                                                   eleve_ldap.classe)
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

    def handle_enseignant(self, etablissement_context: EtablissementContext, enseignant_ldap: EnseignantLdap,
                          log=getLogger()):
        enseignant_infos = "%s %s %s" % (enseignant_ldap.uid, enseignant_ldap.given_name, enseignant_ldap.sn)

        if enseignant_ldap.uai_courant and not etablissement_context.etablissement_regroupe:
            etablissement_context.etablissement_theme = enseignant_ldap.uai_courant.lower()

        if not enseignant_ldap.mail:
            enseignant_ldap.mail = self.__config.constantes.default_mail

        # Affichage du mail reserve aux membres de cours
        mail_display = self.__config.constantes.default_mail_display
        if etablissement_context.structure_ldap.uai in self.__action_config.etablissements.listeEtabSansMail:
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

        # Mise ajour des droits sur les anciens etablissement
        if enseignant_ldap.uais is not None and not etablissement_context.etablissement_regroupe:
            # Recuperation des uais des etablissements dans lesquels l'enseignant est autorise
            self.mettre_a_jour_droits_enseignant(enseignant_infos, etablissement_context.gere_admin_local,
                                                 etablissement_context.id_context_categorie,
                                                 etablissement_context.id_context_course_forum,
                                                 id_user, enseignant_ldap.uais, log=log)

        # Ajout du role de createur de cours au niveau de la categorie inter-etablissement Moodle
        self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                   self.context.id_context_categorie_inter_etabs, id_user)
        log.info("        |_ Ajout du role de createur de cours dans la categorie inter-etablissements")

        # Si l'enseignant fait partie d'un CFA
        # Ajout du role createur de cours au niveau de la categorie inter-cfa
        if etablissement_context.structure_ldap.type == self.__config.constantes.type_structure_cfa:
            self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                       self.context.id_context_categorie_inter_cfa, id_user)
            log.info("        |_ Ajout du role de createur de cours dans la categorie inter-cfa")

        # ajout du role de createur de cours dans l'etablissement
        self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                   etablissement_context.id_context_categorie, id_user)

        # Ajouts des autres roles pour le personnel établissement
        if 'National_3' in enseignant_ldap.profils or 'National_4' in enseignant_ldap.profils or 'National_5' in \
                enseignant_ldap.profils or 'National_6' in enseignant_ldap.profils:
            # Ajout des roles sur le contexte forum
            self.__db.add_role_to_user(self.__config.constantes.id_role_eleve,
                                       etablissement_context.id_context_course_forum, id_user)
            # Inscription à la Zone Privée
            self.__db.enroll_user_in_course(self.__config.constantes.id_role_eleve,
                                            etablissement_context.id_zone_privee, id_user)

            if 'National_3' in enseignant_ldap.profils or 'National_5' in \
                    enseignant_ldap.profils or 'National_6' in enseignant_ldap.profils:
                if not etablissement_context.gere_admin_local:
                    self.__db.add_role_to_user(self.context.id_role_extended_teacher,
                                               etablissement_context.id_context_categorie,
                                               id_user)
            elif 'National_4' in enseignant_ldap.profils:
                self.__db.add_role_to_user(self.__config.constantes.id_role_directeur,
                                           etablissement_context.id_context_categorie, id_user)

        # Ajout des droits d'administration locale pour l'etablissement
        if etablissement_context.gere_admin_local:
            for member in enseignant_ldap.is_member_of:
                # L'enseignant est il administrateur Moodle ?
                adminMoodle = re.match(etablissement_context.regexp_admin_moodle, member, flags=re.IGNORECASE)
                if adminMoodle:
                    self.__db.insert_moodle_local_admin(etablissement_context.id_context_categorie, id_user)
                    log.info("      |_ Insertion d'un admin  local %s %s %s" % (
                        enseignant_ldap.uid, enseignant_ldap.given_name, enseignant_ldap.sn))
                    # Si il est admin local on en fait un utilisateur avancé par default
                    if not self.__db.is_enseignant_avance(id_user, self.context.id_role_advanced_teacher):
                        self.__db.add_role_to_user(self.context.id_role_advanced_teacher, 1, id_user)
                    break
                else:
                    delete = self.__db.delete_moodle_local_admin(self.context.id_context_categorie_inter_etabs, id_user)
                    if delete:
                        log.info("      |_ Suppression d'un admin local %s %s %s" % (
                            enseignant_ldap.uid, enseignant_ldap.given_name, enseignant_ldap.sn))

        # Inscription dans les cohortes associees aux classes
        enseignant_cohorts = []
        if enseignant_ldap.classes:
            log.info("Inscription de l'enseignant %s dans les cohortes de classes %s"
                     % (enseignant_ldap, enseignant_ldap.classes))
            name_pattern = "Profs de la Classe %s"
            desc_pattern = "Profs de la Classe %s"
            ids_classes_cohorts = self.create_classes_cohorts(etablissement_context.id_context_categorie,
                                                              enseignant_ldap.classes,
                                                              self.context.timestamp_now_sql,
                                                              name_pattern=name_pattern,
                                                              desc_pattern=desc_pattern)
            for ids_classe_cohorts in ids_classes_cohorts:
                self.__db.enroll_user_in_cohort(ids_classe_cohorts, id_user, self.context.timestamp_now_sql)

            enseignant_cohorts.extend(ids_classes_cohorts)

        # ATTENTION: Ce code n'est jamais appelé (enseignant_ldap.niveau_formation n'est jamais peuplé) car le LDAP ne
        # contient pas l'information du niveau de formation sur les enseignants.
        # Inscription dans la cohorte associee au niveau de formation
        if enseignant_ldap.niveau_formation:
            log.info("Inscription de l'enseignant %s dans la cohorte de niveau de formation %s"
                     % (enseignant_ldap, enseignant_ldap.niveau_formation))
            id_formation_cohort = self.create_formation_cohort(etablissement_context.id_context_categorie,
                                                               enseignant_ldap.niveau_formation,
                                                               self.context.timestamp_now_sql)
            self.__db.enroll_user_in_cohort(id_formation_cohort, id_user, self.context.timestamp_now_sql)
            enseignant_cohorts.append(id_formation_cohort)

        # Mise a jour des dictionnaires concernant les cohortes
        for cohort_id in enseignant_cohorts:
            # Si la cohorte est deja connue
            if cohort_id in etablissement_context.enseignants_by_cohortes:
                etablissement_context.enseignants_by_cohortes[cohort_id].append(id_user)
            # Si la cohorte n'a pas encore ete rencontree
            else:
                etablissement_context.enseignants_by_cohortes[cohort_id] = [id_user]

        # Mise a jour du Domaine
        user_domain = self.__config.constantes.default_domain
        if len(enseignant_ldap.domaines) == 1:
            user_domain = enseignant_ldap.domaines[0]
        else:
            if enseignant_ldap.uai_courant and enseignant_ldap.uai_courant in self.context.map_etab_domaine:
                user_domain = self.context.map_etab_domaine[enseignant_ldap.uai_courant][0]
        log.debug("Insertion du Domaine")
        self.__db.set_user_domain(id_user, self.context.id_field_domaine, user_domain)

    def handle_user_interetab(self, personne_ldap: PersonneLdap, log=getLogger()):
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
                                   self.context.id_context_categorie_inter_etabs, id_user)

        # Attribution du role admin local si necessaire
        for member in personne_ldap.is_member_of:
            admin = re.match(self.__action_config.inter_etablissements.ldap_valeur_attribut_admin, member,
                             flags=re.IGNORECASE)
            if admin:
                insert = self.__db.insert_moodle_local_admin(self.context.id_context_categorie_inter_etabs, id_user)
                if insert:
                    log.info(
                        "      |_ Insertion d'un admin local %s %s %s" % (
                            personne_ldap.uid, personne_ldap.given_name, personne_ldap.sn))
                break
            else:
                delete = self.__db.delete_moodle_local_admin(self.context.id_context_categorie_inter_etabs, id_user)
                if delete:
                    log.info("      |_ Suppression d'un admin local %s %s %s" % (
                        personne_ldap.uid, personne_ldap.given_name, personne_ldap.sn))

    def handle_inspecteur(self, personne_ldap: PersonneLdap, log=getLogger()):
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
        log.info("        |_ Ajout du role de createur de cours dans la categorie inter-etablissements")

        # Mise a jour du Domaine
        user_domain = self.__config.constantes.default_domain
        if len(personne_ldap.domaines) == 1:
            user_domain = personne_ldap.domaines[0]
        else:
            if personne_ldap.uai_courant and personne_ldap.uai_courant in self.context.map_etab_domaine:
                user_domain = self.context.map_etab_domaine[personne_ldap.uai_courant][0]
        log.debug("Insertion du Domaine")
        self.__db.set_user_domain(id_user, self.context.id_field_domaine, user_domain)

    def mettre_a_jour_droits_enseignant(self, enseignant_infos, gereAdminLocal, id_enseignant, id_context_categorie,
                                        id_context_course_forum, uais_autorises, log=getLogger()):
        """
        Fonction permettant de mettre a jour les droits d'un enseignant.
        Cette mise a jour consiste a :
          - Supprimer les roles non autorises
          - ajouter les roles
        :param enseignant_infos:
        :param gereAdminLocal:
        :param id_enseignant:
        :param id_context_categorie:
        :param id_context_course_forum:
        :param uais_autorises:
        :param log:
        :return:
        """
        # Recuperation des themes autorises pour l'enseignant
        themes_autorises = [uai_autorise.lower() for uai_autorise in uais_autorises]
        log.debug(
            "      |_ Etablissements autorises pour l'enseignant pour %s : %s" % (enseignant_infos,
                                                                                  str(themes_autorises)))

        #########################
        # ZONES PRIVEES
        #########################
        # Recuperation des ids des roles et les themes non autorises
        ids_roles_non_autorises, ids_themes_non_autorises = self.__db.get_ids_and_themes_not_allowed_roles(
            id_enseignant, themes_autorises)

        # Suppression des roles non autorises
        if ids_roles_non_autorises:
            self.__db.delete_roles(ids_roles_non_autorises)
            log.info("      |_ Suppression des rôles d'enseignant pour %s dans les établissements %s" % (
                enseignant_infos, str(ids_themes_non_autorises)))
            log.info(
                "         Les seuls établissements autorisés pour cet enseignant sont %s" % str(themes_autorises))

        #########################
        # FORUMS
        #########################
        # Recuperation des SIREN des etablissements dans lequel l'enseignant travaille
        sirens = self.__db.get_descriptions_course_categories_by_themes(themes_autorises)

        # Shortname des forums associes
        # Ancien code : shortnames_forums = [ ( "ZONE-PRIVEE-%s" % str( siren ) ) for siren in sirens ]
        shortnames_forums = ["ZONE-PRIVEE-%s" % siren for siren in sirens]

        # Recuperation des roles sur les forums qui ne devraient plus exister
        ids_roles_non_autorises, forums_summaries = self.__db.get_ids_and_summaries_not_allowed_roles(id_enseignant,
                                                                                                      shortnames_forums)

        # Suppression des roles non autorises
        if ids_roles_non_autorises:
            # Suppression des roles
            self.__db.delete_roles(ids_roles_non_autorises)
            log.info("      |_ Suppression des rôles d'enseignant pour %s sur les forum '%s' " % (
                enseignant_infos, str(forums_summaries)))
            log.info("         Les seuls établissements autorisés pour cet enseignant sont '%s'" % themes_autorises)

    def create_profs_etabs_cohorts(self, etablissement_context: EtablissementContext,
                                   since_timestamp: datetime.datetime):
        """
        Fonction permettant de creer des cohortes a partir de
        etablissement. Puis de remplir la cohorte avec les enseignants de l'etablissement
        :param etablissement_context:
        :param since_timestamp:
        :return:
        """

        liste_professeurs_insere = []

        # TODO: Extraire ces deux libellés dans la configuration
        cohort_name = 'Profs de l\'établissement (%s)' % etablissement_context.uai
        cohort_description = 'Enseignants de l\'établissement %s' % etablissement_context.uai
        id_cohort = self.__db.create_cohort(etablissement_context.id_context_categorie, cohort_name, cohort_name,
                                            cohort_description, self.context.timestamp_now_sql)

        enseignants = self.__ldap.search_enseignant(since_timestamp=since_timestamp, uai=etablissement_context.uai,
                                                    tous=True)

        for enseignant in enseignants:
            id_user = self.__db.get_user_id(enseignant.uid)
            self.__db.enroll_user_in_cohort(id_cohort, id_user, self.context.timestamp_now_sql)
            liste_professeurs_insere.append(id_user)
        if since_timestamp is None:
            self.__db.purge_cohort_profs(id_cohort, liste_professeurs_insere)

    def create_formation_cohort(self, id_context_etab, niveau_formation, timestamp_now_sql):
        cohort_name = 'Élèves du Niveau de formation %s' % niveau_formation
        cohort_description = 'Eleves avec le niveau de formation %s' % niveau_formation
        id_cohort = self.__db.create_cohort(id_context_etab, cohort_name, cohort_name, cohort_description,
                                            timestamp_now_sql)
        return id_cohort

    def create_classes_cohorts(self, id_context_etab, classes_names, time_created, name_pattern=None,
                               desc_pattern=None):
        """
        Fonction permettant de creer des cohortes a partir de
        classes liees a un etablissement.
        :param id_context_etab:
        :param classes_names:
        :param time_created:
        :param name_pattern:
        :param desc_pattern:
        :return:
        """

        if name_pattern is None:
            name_pattern = "Élèves de la Classe %s"
        if desc_pattern is None:
            desc_pattern = "Élèves de la Classe %s"

        ids_cohorts = []
        for class_name in classes_names:
            cohort_name = name_pattern % class_name
            cohort_description = desc_pattern % class_name
            id_cohort = self.__db.create_cohort(id_context_etab,
                                                cohort_name,
                                                cohort_name,
                                                cohort_description,
                                                time_created)
            ids_cohorts.append(id_cohort)
        return ids_cohorts

    def get_users_by_cohorts_comparators(self, etab_context: EtablissementContext,
                                         cohortname_pattern_re=r'(Élèves de la Classe )(.*)$')\
            -> (Dict[str, List[str]], Dict[str, List[str]]):
        """
        Renvoie deux dictionnaires listant les utilisateurs (uid) dans chacune des classes.
        Le premier dictionnaire contient les valeurs de la BDD, le second celles du LDAP
        :param etab_context: EtablissementContext
        :param cohortname_pattern_re:
        :return:
        """
        classes_cohorts = self.__db.get_eleve_classe_cohorts(etab_context.id_context_categorie)

        eleves_by_cohorts_db = {}
        for cohort in classes_cohorts:
            matches = re.search(cohortname_pattern_re, cohort.name)
            classe_name = matches.group(2)
            eleves_by_cohorts_db[classe_name] = []
            for member_id, username in self.__db.get_cohort_members(cohort.id):
                eleves_by_cohorts_db[classe_name].append(username.lower())

        eleves_by_cohorts_ldap = {}
        for classe, eleves in eleves_by_cohorts_db.items():
            eleves_by_cohorts_ldap[classe] = []
            for eleve in self.__ldap.search_eleves_in_classe(classe, etab_context.uai):
                eleves_by_cohorts_ldap[classe].append(eleve.uid.lower())

        return eleves_by_cohorts_db, eleves_by_cohorts_ldap

    def purge_cohorts(self, users_by_cohorts_db: Dict[str, List[str]],
                      users_by_cohorts_ldap: Dict[str, List[str]],
                      cohortname_pattern="Élèves de la Classe %s",
                      log=getLogger()):
        """
        Vide les cohortes d'utilisateurs conformément à l'annuaire LDAP
        :param users_by_cohorts_db:
        :param users_by_cohorts_ldap:
        :param cohortname_pattern:
        :param log:
        :return:
        """
        disenrolled_users = {}
        for cohort_db, eleves_db in users_by_cohorts_db.items():
            cohortname = cohortname_pattern % cohort_db
            if cohort_db not in users_by_cohorts_ldap.keys():
                for username_db in users_by_cohorts_db[cohort_db]:
                    log.info("Désenrollement de l'utilisateur %s de la cohorte \"%s\"" % (username_db, cohort_db))
                    self.__db.disenroll_user_from_username_and_cohortname(username_db, cohortname)
                    if cohort_db not in disenrolled_users.keys():
                        disenrolled_users[cohort_db] = []
                    disenrolled_users[cohort_db].append(username_db)
            else:
                for username_db in eleves_db:
                    if username_db not in users_by_cohorts_ldap[cohort_db]:
                        log.info("Désenrollement de l'utilisateur %s de la cohorte \"%s\"" % (username_db, cohort_db))
                        self.__db.disenroll_user_from_username_and_cohortname(username_db, cohortname)
                        if cohort_db not in disenrolled_users.keys():
                            disenrolled_users[cohort_db] = []
                        disenrolled_users[cohort_db].append(username_db)
        return disenrolled_users

    def mise_a_jour_cohorte_interetab(self, is_member_of, cohort_name, since_timestamp: datetime.datetime,
                                      log=getLogger()):
        # Creation de la cohort si necessaire
        self.__db.create_cohort(self.context.id_context_categorie_inter_etabs, cohort_name, cohort_name, cohort_name,
                                self.context.timestamp_now_sql)
        id_cohort = self.__db.get_id_cohort(self.context.id_context_categorie_inter_etabs, cohort_name)

        # Liste permettant de sauvegarder les utilisateurs de la cohorte
        self.context.utilisateurs_by_cohortes[id_cohort] = []

        # Recuperation des utilisateurs
        is_member_of_list = [is_member_of]

        # Ajout des utilisateurs dans la cohorte
        for personne_ldap in self.__ldap.search_personne(
                since_timestamp=since_timestamp if not self.__arguments.purge_cohortes else None,
                isMemberOf=is_member_of_list):
            user_id = self.__db.get_user_id(personne_ldap.uid)
            if user_id:
                self.__db.enroll_user_in_cohort(id_cohort, user_id, self.context.timestamp_now_sql)
                # Mise a jour des utilisateurs de la cohorte
                self.context.utilisateurs_by_cohortes[id_cohort].append(user_id)
            else:
                log.warning("Impossible d'inserer l'utilisateur %s dans la cohorte %s, "
                            "car il n'est pas connu dans Moodle" % (personne_ldap, cohort_name))

    def insert_moodle_structure(self, grp, nom_structure, path, ou, siren, uai, log=getLogger()):
        """
        Fonction permettant d'inserer une structure dans Moodle.
        :param grp:
        :param nom_structure:
        :param path:
        :param ou:
        :param siren:
        :param uai:
        :param log:
        :return:
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
        path_etablissement = "/%d" % id_categorie_etablissement
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
        path_contexte_etablissement = "%s/%d" % (path, id_contexte_etablissement)
        self.__db.update_context_path(id_contexte_etablissement, path_contexte_etablissement)

        #########################
        # PARTIE ZONE PRIVEE
        #########################
        # Insertion du cours pour le forum de discussion
        id_zone_privee = self.__db.insert_zone_privee(id_categorie_etablissement, siren, ou, now)

        # Insertion du contexte associe
        id_contexte_zone_privee = self.__db.insert_zone_privee_context(id_zone_privee)

        # Mise a jour du path du contexte
        path_contexte_zone_privee = "%s/%d" % (path_contexte_etablissement, id_contexte_zone_privee)
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

        self.__db.insert_moodle_course_module(course, module, instance, added)
        id_course_module = self.__db.get_id_course_module(course)

        # Insertion du contexte pour le module de cours (forum)
        self.__db.insert_moodle_context(self.__config.constantes.niveau_ctx_forum,
                                        PROFONDEUR_CTX_MODULE_ZONE_PRIVEE,
                                        id_course_module)
        id_contexte_module = self.__db.get_id_context(self.__config.constantes.niveau_ctx_forum,
                                                      PROFONDEUR_CTX_MODULE_ZONE_PRIVEE,
                                                      id_course_module)

        # Mise a jour du path du contexte
        path_contexte_module = "%s/%d" % (path_contexte_zone_privee, id_contexte_module)
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

        self.__db.insert_moodle_block(block_name, parent_context_id, show_in_subcontexts, page_type_pattern,
                                      sub_page_pattern, default_region, default_weight)
        id_block = self.__db.get_id_block(parent_context_id)

        # Insertion du contexte pour le bloc
        self.__db.insert_moodle_context(self.__config.constantes.niveau_ctx_bloc,
                                        PROFONDEUR_CTX_BLOCK_ZONE_PRIVEE,
                                        id_block)
        id_contexte_bloc = self.__db.get_id_context(self.__config.constantes.niveau_ctx_bloc,
                                                    PROFONDEUR_CTX_BLOCK_ZONE_PRIVEE,
                                                    id_block)

        # Mise a jour du path du contexte
        path_contexte_bloc = "%s/%d" % (path_contexte_zone_privee, id_contexte_bloc)
        self.__db.update_context_path(id_contexte_bloc, path_contexte_bloc)

        log.info('  |_ Insertion de %s %s' % (siren, ou.encode("utf-8")))