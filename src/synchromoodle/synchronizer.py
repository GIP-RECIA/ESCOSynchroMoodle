# coding: utf-8
import datetime
import logging
import re
import sys
from typing import Dict, List

from synchromoodle.ldaputils import StructureLdap
from .arguments import default_args
from .config import EtablissementsConfig, Config
from .dbutils import Database
from .ldaputils import Ldap, EleveLdap, EnseignantLdap, PersonneLdap

logging.basicConfig(format='%(levelname)s:%(message)s', stream=sys.stdout, level=logging.INFO)


def est_grp_etab(rne: str, etablissements_config: EtablissementsConfig):
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


class SyncContext:
    timestamp_now_sql = None
    map_etab_domaine = None  # type: Dict[str, List[str]]
    id_context_categorie_inter_etabs = None  # type: int
    id_context_categorie_inter_cfa = None  # type: int
    id_role_extended_teacher = None  # type: int
    id_role_advanced_teacher = None  # type: int
    id_field_classe = None  # type: int
    id_field_domaine = None  # type: int
    utilisateurs_by_cohortes = {}


class EtablissementContext:
    uai = None  # type: str
    id_context_categorie = None
    id_context_course_forum = None
    etablissement_regroupe = None
    structure_ldap = None  # type: StructureLdap
    gere_admin_local = None  # type: bool
    regexp_admin_moodle = None  # type: str
    regexp_admin_local = None  # type: str
    id_zone_privee = None  # type: int
    etablissement_theme = None  # type: str
    eleves_by_cohortes = {}

    def __init__(self, uai: str):
        self.uai = uai


class Synchronizer:
    __ldap = None  # type: Ldap
    __db = None  # type: Database
    __config = None  # type: Config
    __arguments = None
    context = None  # type: SyncContext

    def __init__(self, ldap: Ldap, db: Database, config: Config, arguments=default_args):
        self.__ldap = ldap
        self.__db = db
        self.__config = config
        self.__arguments = arguments

    def initialize(self):
        self.context = SyncContext()

        # Recuperation du timestamp actuel
        self.context.timestamp_now_sql = self.__db.get_timestamp_now()

        # Récupération de la liste UAI-Domaine des établissements
        self.context.map_etab_domaine = self.__ldap.get_domaines_etabs()

        # Ids des categories inter etablissements
        id_categorie_inter_etabs = self.__db.get_id_categorie(self.__config.etablissements.inter_etab_categorie_name)
        self.context.id_context_categorie_inter_etabs = self.__db.get_id_context_categorie(id_categorie_inter_etabs)

        id_categorie_inter_cfa = self.__db.get_id_categorie(self.__config.etablissements.inter_etab_categorie_name_cfa)
        self.context.id_context_categorie_inter_cfa = self.__db.get_id_context_categorie(id_categorie_inter_cfa)

        # Recuperation des ids des roles
        self.context.id_role_extended_teacher = self.__db.get_id_role_by_shortname('extendedteacher')
        self.context.id_role_advanced_teacher = self.__db.get_id_role_by_shortname('advancedteacher')

        # Recuperation de l'id du user info field pour la classe
        self.context.id_field_classe = self.__db.get_id_user_info_field_by_shortname('classe')

        # Recuperation de l'id du champ personnalisé Domaine
        self.context.id_field_domaine = self.__db.get_id_user_info_field_by_shortname('Domaine')

    def handle_etablissement(self, uai) -> EtablissementContext:
        """
        Met a jour l'etablissement meme si celui-ci n'a pas ete modifie depuis la derniere synchro
        car des infos doivent etre recuperees dans Moodle dans tous les cas
        :return: EtabContext
        """
        logging.info("  |_ Traitement de l'établissement %s" % uai)
        context = EtablissementContext(uai)
        context.gere_admin_local = uai not in self.__config.etablissements.listeEtabSansAdmin
        context.etablissement_regroupe = est_grp_etab(uai, self.__config.etablissements)
        # Regex pour savoir si l'utilisateur est administrateur moodle
        context.regexp_admin_moodle = self.__config.etablissements.prefixAdminMoodleLocal + ".*_%s$" % uai
        # Regex pour savoir si l'utilisateur est administrateur local
        context.regexp_admin_local = self.__config.etablissements.prefixAdminLocal + ".*_%s$" % uai

        structure_ldap = self.__ldap.get_structure(uai)
        if structure_ldap:
            etablissement_path = "/1"

            # Si l'etablissement fait partie d'un groupement
            if context.etablissement_regroupe:
                etablissement_ou = context.etablissement_regroupe["nom"]
                structure_ldap.uai = context.etablissement_regroupe["uais"][0]
            else:
                etablissement_ou = structure_ldap.nom

            # Recuperation du bon theme
            context.etablissement_theme = structure_ldap.uai.lower()

            # Creation de la structure si elle n'existe pas encore
            id_etab_categorie = self.__db.get_id_course_category_by_theme(context.etablissement_theme)
            if id_etab_categorie is None:
                self.__db.insert_moodle_structure(context.etablissement_regroupe, structure_ldap.nom,
                                                  etablissement_path, etablissement_ou,
                                                  structure_ldap.siren, context.etablissement_theme)
                id_etab_categorie = self.__db.get_id_course_category_by_id_number(structure_ldap.siren)

            # Mise a jour de la description dans la cas d'un groupement d'etablissement
            if context.etablissement_regroupe:
                description = self.__db.get_description_course_category(id_etab_categorie)
                if description.find(structure_ldap.siren) == -1:
                    description = "%s$%s@%s" % (description, structure_ldap.siren, structure_ldap.nom)
                    self.__db.update_course_category_description(id_etab_categorie, description)
                    self.__db.update_course_category_name(id_etab_categorie, etablissement_ou)

            # Recuperation de l'id du contexte correspondant à l'etablissement
            context.id_context_categorie = self.__db.get_id_context_categorie(id_etab_categorie)
            context.id_zone_privee = self.__db.get_id_course_by_id_number("ZONE-PRIVEE-" + structure_ldap.siren)

            # Recreation de la zone privee si celle-ci n'existe plus
            if context.id_zone_privee is None:
                context.id_zone_privee = self.__db.insert_zone_privee(id_etab_categorie, structure_ldap.siren,
                                                                      etablissement_ou, self.context.timestamp_now_sql)

            context.id_context_course_forum = self.__db.get_id_context(self.__config.constantes.niveau_ctx_cours, 3,
                                                                       context.id_zone_privee)
            if context.id_context_course_forum is None:
                context.id_context_course_forum = self.__db.insert_zone_privee_context(context.id_zone_privee)
            context.structure_ldap = structure_ldap
        return context

    def handle_eleve(self, etablissement_context: EtablissementContext, eleve_ldap: EleveLdap):
        #  Recuperation des informations

        eleve_infos = "%s %s %s" % (eleve_ldap.uid, eleve_ldap.given_name, eleve_ldap.sn)

        # Recuperation du mail
        mail_display = self.__config.constantes.default_mail_display
        if not eleve_ldap.mail:
            eleve_ldap.mail = self.__config.constantes.default_mail

        # Insertion de l'eleve
        eleve_id = self.__db.get_user_id(eleve_ldap.uid)
        if not eleve_id:
            self.__db.insert_moodle_user(eleve_ldap.uid, eleve_ldap.given_name,
                                         eleve_ldap.given_name, eleve_ldap.mail,
                                         mail_display, etablissement_context.etablissement_theme)
            eleve_id = self.__db.get_user_id(eleve_ldap.uid)
        else:
            self.__db.update_moodle_user(eleve_id, eleve_ldap.given_name,
                                         eleve_ldap.given_name, eleve_ldap.mail, mail_display,
                                         etablissement_context.etablissement_theme)

        # Ajout du role d'utilisateur avec droits limités Pour les eleves de college
        if etablissement_context.structure_ldap.type == self.__config.constantes.type_structure_clg:
            self.__db.add_role_to_user(self.__config.constantes.id_role_utilisateur_limite,
                                       self.__config.constantes.id_instance_moodle, eleve_id)
            logging.info(
                "      |_ Ajout du role d'utilisateur avec des droits limites à l'utilisateur %s %s %s (id = %s)" % (
                    eleve_ldap.given_name, eleve_ldap.sn, eleve_ldap.uid, str(eleve_id)))

        # Inscription dans les cohortes associees aux classes
        eleve_cohorts = []
        if eleve_ldap.classes:
            ids_classes_cohorts = self.__db.create_classes_cohorts(etablissement_context.id_context_categorie,
                                                                   eleve_ldap.classes, self.context.timestamp_now_sql)
            self.__db.enroll_user_in_cohorts(etablissement_context.id_context_categorie, ids_classes_cohorts,
                                             eleve_id, eleve_infos, self.context.timestamp_now_sql)
            eleve_cohorts.extend(ids_classes_cohorts)

        # Inscription dans la cohorte associee au niveau de formation
        if eleve_ldap.niveau_formation:
            id_formation_cohort = self.__db.create_formation_cohort(etablissement_context.id_context_categorie,
                                                                    eleve_ldap.niveau_formation,
                                                                    self.context.timestamp_now_sql)
            self.__db.enroll_user_in_cohort(id_formation_cohort, eleve_id, eleve_infos, self.context.timestamp_now_sql)
            eleve_cohorts.append(id_formation_cohort)

            # Desinscription des anciennes cohortes
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
            logging.debug("Mise à jour user_info_data")
        else:
            self.__db.insert_moodle_user_info_data(eleve_id, self.context.id_field_classe,
                                                   eleve_ldap.classe)
            logging.debug("Insertion user_info_data")

        # Mise a jour du Domaine
        user_domain = self.__config.constantes.default_domain
        if len(eleve_ldap.domaines) == 1:
            user_domain = eleve_ldap.domaines[0]
        else:
            if eleve_ldap.uai_courant and eleve_ldap.uai_courant in self.context.map_etab_domaine:
                user_domain = self.context.map_etab_domaine[eleve_ldap.uai_courant][0]
        logging.debug("Insertion du Domaine")
        self.__db.set_user_domain(eleve_id, self.context.id_field_domaine, user_domain)

    def handle_enseignant(self, etablissement_context: EtablissementContext, enseignant_ldap: EnseignantLdap):
        enseignant_infos = "%s %s %s" % (enseignant_ldap.uid, enseignant_ldap.given_name, enseignant_ldap.sn)

        if enseignant_ldap.uai_courant and not etablissement_context.etablissement_regroupe:
            etablissement_context.etablissement_theme = enseignant_ldap.uai_courant.lower()

        if not enseignant_ldap.mail:
            enseignant_ldap.mail = self.__config.constantes.default_mail

        # Affichage du mail reserve aux membres de cours
        mail_display = self.__config.constantes.default_mail_display
        if etablissement_context.structure_ldap.uai in self.__config.etablissements.listeEtabSansMail:
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
                                                 id_user, enseignant_ldap.uais)

        # Ajout du role de createur de cours au niveau de la categorie inter-etablissement Moodle
        self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                   self.context.id_context_categorie_inter_etabs, id_user)
        logging.info("        |_ Ajout du role de createur de cours dans la categorie inter-etablissements")

        # Si l'enseignant fait partie d'un CFA
        # Ajout du role createur de cours au niveau de la categorie inter-cfa
        if etablissement_context.structure_ldap.type == self.__config.constantes.type_structure_cfa:
            self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                       self.context.id_context_categorie_inter_cfa, id_user)
            logging.info("        |_ Ajout du role de createur de cours dans la categorie inter-cfa")

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
                    logging.info("      |_ Insertion d'un admin  local %s %s %s" % (
                        enseignant_ldap.uid, enseignant_ldap.given_name, enseignant_ldap.sn))
                    # Si il est admin local on en fait un utilisateur avancé par default
                    if not self.__db.is_enseignant_avance(id_user, self.context.id_role_advanced_teacher):
                        self.__db.add_role_to_user(self.context.id_role_advanced_teacher, 1, id_user)
                    break
                else:
                    delete = self.__db.delete_moodle_local_admin(self.context.id_context_categorie_inter_etabs, id_user)
                    if delete:
                        logging.info("      |_ Suppression d'un admin local %s %s %s" % (
                            enseignant_ldap.uid, enseignant_ldap.given_name, enseignant_ldap.sn))

        # Mise a jour du Domaine
        user_domain = self.__config.constantes.default_domain
        if len(enseignant_ldap.domaines) == 1:
            user_domain = enseignant_ldap.domaines[0]
        else:
            if enseignant_ldap.uai_courant and enseignant_ldap.uai_courant in self.context.map_etab_domaine:
                user_domain = self.context.map_etab_domaine[enseignant_ldap.uai_courant][0]
        logging.debug("Insertion du Domaine")
        self.__db.set_user_domain(id_user, self.context.id_field_domaine, user_domain)

    def handle_user_interetab(self, personne_ldap: PersonneLdap):
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
            admin = re.match(self.__config.inter_etablissements.ldap_valeur_attribut_admin, member, flags=re.IGNORECASE)
            if admin:
                insert = self.__db.insert_moodle_local_admin(self.context.id_context_categorie_inter_etabs, id_user)
                if insert:
                    logging.info(
                        "      |_ Insertion d'un admin local %s %s %s" % (
                            personne_ldap.uid, personne_ldap.given_name, personne_ldap.sn))
                break
            else:
                delete = self.__db.delete_moodle_local_admin(self.context.id_context_categorie_inter_etabs, id_user)
                if delete:
                    logging.info("      |_ Suppression d'un admin local %s %s %s" % (
                        personne_ldap.uid, personne_ldap.given_name, personne_ldap.sn))

    def handle_inspecteur(self, personne_ldap: PersonneLdap):
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
        logging.info("        |_ Ajout du role de createur de cours dans la categorie inter-etablissements")

        # Mise a jour du Domaine
        user_domain = self.__config.constantes.default_domain
        if len(personne_ldap.domaines) == 1:
            user_domain = personne_ldap.domaines[0]
        else:
            if personne_ldap.uai_courant and personne_ldap.uai_courant in self.context.map_etab_domaine:
                user_domain = self.context.map_etab_domaine[personne_ldap.uai_courant][0]
        logging.debug("Insertion du Domaine")
        self.__db.set_user_domain(id_user, self.context.id_field_domaine, user_domain)

    def mettre_a_jour_droits_enseignant(self, enseignant_infos, gereAdminLocal, id_enseignant, id_context_categorie,
                                        id_context_course_forum, uais_autorises):
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
        :return:
        """
        # Recuperation des themes autorises pour l'enseignant
        themes_autorises = [uai_autorise.lower() for uai_autorise in uais_autorises]
        logging.debug(
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
            logging.info("      |_ Suppression des rôles d'enseignant pour %s dans les établissements %s" % (
                enseignant_infos, str(ids_themes_non_autorises)))
            logging.info(
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
            logging.info("      |_ Suppression des rôles d'enseignant pour %s sur les forum '%s' " % (
                enseignant_infos, str(forums_summaries)))
            logging.info("         Les seuls établissements autorisés pour cet enseignant sont '%s'" % themes_autorises)

    def purge_eleve_cohorts(self, etablissement_context):
        self.__db.purge_cohorts(etablissement_context.eleves_by_cohortes)

    def create_profs_etabs_cohorts(self, etablissement_context: EtablissementContext,
                                   since_timestamp: datetime.datetime):
        self.__db.create_profs_etabs_cohorts(etablissement_context.id_context_categorie,
                                             etablissement_context.uai,
                                             self.context.timestamp_now_sql,
                                             since_timestamp,
                                             self.__ldap)

    def mise_a_jour_cohorte_interetab(self, is_member_of, cohort_name, since_timestamp: datetime.datetime):
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
            infos_personne = "%s %s %s" % (personne_ldap.uid, personne_ldap.given_name, personne_ldap.sn)

            user_id = self.__db.get_user_id(personne_ldap.uid)
            if user_id:
                self.__db.enroll_user_in_cohort(id_cohort, user_id, infos_personne, self.context.timestamp_now_sql)
                # Mise a jour des utilisateurs de la cohorte
                self.context.utilisateurs_by_cohortes[id_cohort].append(user_id)
            else:
                message = "      |_ Impossible d'inserer l'utilisateur %s dans la cohorte %s, " \
                          "car il n'est pas connu dans Moodle"
                message = message % (infos_personne, cohort_name.decode("utf-8"))
                logging.warning(message)
