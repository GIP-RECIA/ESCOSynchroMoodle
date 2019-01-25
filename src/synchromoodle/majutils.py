# coding: utf-8

import logging
import re
import sys

from .dbutils import Database
from .config import EtablissementsConfig, Config
from .ldaputils import Ldap, StudentLdap, TeacherLdap

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
    id_user_info_field_classe = None
    map_etab_domaine = None
    id_field_domaine = None
    id_context_categorie_inter_etabs = None
    id_context_categorie_inter_cfa = None
    id_role_extended_teacher = None
    timestamp_now_sql = None


class EtablissementContext:
    uai = None  # type: str
    id_context_categorie = None
    id_context_course_forum = None
    etablissement_regroupe = None
    ldap_structure = None
    gereAdminLocal = None
    regexpAdminMoodle = None
    regexpAdminLocal = None
    id_zone_privee = None
    etablissement_theme = None
    eleves_by_cohortes = {}

    def __init__(self, uai: str):
        self.uai = uai


class EleveContext:
    pass


class Synchronizer:
    __ldap = None  # type: Ldap
    __db = None  # type: Database
    __config = None  # type: Config
    context = None  # type: SyncContext

    def __init__(self, ldap: Ldap, db: Database, config: Config):
        self.__ldap = ldap
        self.__db = db
        self.__config = config
        self.context = SyncContext()

    def load_context(self):
        # Récupération de la liste UAI-Domaine des établissements
        self.context.map_etab_domaine = self.__ldap.get_domaines_etabs()

        # Ids des categories inter etablissements
        self.context.id_context_categorie_inter_etabs = self.__db.get_id_context_inter_etabs()

        id_categorie_inter_cfa = self.__db.get_id_categorie_inter_etabs(
            self.__config.etablissements.inter_etab_categorie_name_cfa)
        self.context.id_context_categorie_inter_cfa = self.__db.get_id_context_categorie(id_categorie_inter_cfa)

        # Recuperation des ids des roles admin local et extended teacher
        self.context.id_role_extended_teacher = self.__db.get_id_role_extended_teacher()

        # Recuperation du timestamp actuel
        self.context.timestamp_now_sql = self.__db.get_timestamp_now()

        # Recuperation de l'id du user info field pour la classe
        self.context.id_user_info_field_classe = self.__db.get_id_user_info_field_classe()
        if self.context.id_user_info_field_classe is None:
            self.__db.insert_moodle_user_info_field_classe()
            self.context.id_user_info_field_classe = self.__db.get_id_user_info_field_classe()

        # Recuperation de l'id du champ personnalisé Domaine
        self.context.id_field_domaine = self.__db.get_field_domaine()

    def mise_a_jour_etab(self, uai) -> EtablissementContext:
        """
        Met a jour l'etablissement meme si celui-ci n'a pas ete modifie depuis la derniere synchro
        car des infos doivent etre recuperees dans Moodle dans tous les cas
        :return: EtabContext
        """
        logging.info("  |_ Traitement de l'établissement %s" % uai)
        context = EtablissementContext(uai)
        context.gereAdminLocal = uai not in self.__config.etablissements.listeEtabSansAdmin
        context.etablissement_regroupe = est_grp_etab(uai, self.__config.etablissements)
        # Regex pour savoir si l'utilisateur est administrateur moodle
        context.regexpAdminMoodle = self.__config.etablissements.prefixAdminMoodleLocal + ".*_%s$" % uai
        # Regex pour savoir si l'utilisateur est administrateur local
        context.regexpAdminLocal = self.__config.etablissements.prefixAdminLocal + ".*_%s$" % uai

        ldap_structure = self.__ldap.get_structure(uai)
        if ldap_structure:
            etablissement_path = "/1"

            # Si l'etablissement fait partie d'un groupement
            if context.etablissement_regroupe:
                etablissement_ou = context.etablissement_regroupe["nom"]
                ldap_structure.uai = context.etablissement_regroupe["uais"][0]
            else:
                etablissement_ou = ldap_structure.nom

            # Recuperation du bon theme
            context.etablissement_theme = ldap_structure.uai.lower()

            # Creation de la structure si elle n'existe pas encore
            id_etab_categorie = self.__db.get_id_course_category_by_theme(context.etablissement_theme)
            if id_etab_categorie is None:
                self.__db.insert_moodle_structure(context.etablissement_regroupe, ldap_structure.nom,
                                                  etablissement_path, etablissement_ou,
                                                  ldap_structure.siren, context.etablissement_theme)
                id_etab_categorie = self.__db.get_id_course_category_by_id_number(ldap_structure.siren)

            # Mise a jour de la description dans la cas d'un groupement d'etablissement
            if context.etablissement_regroupe:
                description = self.__db.get_description_course_category(id_etab_categorie)
                if description.find(ldap_structure.siren) == -1:
                    description = "%s$%s@%s" % (description, ldap_structure.siren, ldap_structure.nom)
                    self.__db.update_course_category_description(id_etab_categorie, description)
                    self.__db.update_course_category_name(id_etab_categorie, etablissement_ou)

            # Recuperation de l'id du contexte correspondant à l'etablissement
            context.id_context_categorie = self.__db.get_id_context_categorie(id_etab_categorie)
            context.id_zone_privee = self.__db.get_id_course_by_id_number("ZONE-PRIVEE-" + ldap_structure.siren)

            # Recreation de la zone privee si celle-ci n'existe plus
            if context.id_zone_privee is None:
                context.id_zone_privee = self.__db.insert_zone_privee(id_etab_categorie, ldap_structure.siren,
                                                                      etablissement_ou, self.context.timestamp_now_sql)

                context.id_context_course_forum = self.__db.get_id_context(self.__config.constantes.niveau_ctx_cours, 3,
                                                                           context.id_zone_privee)
            if context.id_context_course_forum is None:
                context.id_context_course_forum = self.__db.insert_zone_privee_context(context.id_zone_privee)
            context.ldap_structure = ldap_structure
        return context

    def mise_a_jour_eleve(self, etablissement_context: EtablissementContext, ldap_student: StudentLdap):
        #  Recuperation des informations

        eleve_infos = "%s %s %s" % (ldap_student.uid, ldap_student.given_name, ldap_student.sn)

        # Recuperation du mail
        mail_display = self.__config.constantes.default_mail_display
        if not ldap_student.mail:
            ldap_student.mail = self.__config.constantes.default_mail

        # Insertion de l'eleve
        eleve_id = self.__db.get_user_id(ldap_student.uid)
        if not eleve_id:
            self.__db.insert_moodle_user(ldap_student.uid, ldap_student.given_name,
                                         ldap_student.given_name, ldap_student.mail,
                                         mail_display, etablissement_context.etablissement_theme)
            eleve_id = self.__db.get_user_id(ldap_student.uid)
        else:
            self.__db.update_moodle_user(eleve_id, ldap_student.given_name,
                                         ldap_student.given_name, ldap_student.mail, mail_display,
                                         etablissement_context.etablissement_theme)

        # Ajout du role d'utilisateur avec droits limités Pour les eleves de college
        if etablissement_context.ldap_structure.type == self.__config.constantes.type_structure_clg:
            self.__db.add_role_to_user(self.__config.constantes.id_role_utilisateur_limite,
                                       self.__config.constantes.id_instance_moodle, eleve_id)
            logging.info(
                "      |_ Ajout du role d'utilisateur avec des droits limites à l'utilisateur %s %s %s (id = %s)" % (
                    ldap_student.given_name, ldap_student.sn, ldap_student.uid, str(eleve_id)))

        # Inscription dans les cohortes associees aux classes
        eleve_cohorts = []
        if ldap_student.classes:
            ids_classes_cohorts = self.__db.create_classes_cohorts(etablissement_context.id_context_categorie,
                                                                   ldap_student.classes, self.context.timestamp_now_sql)
            self.__db.enroll_user_in_cohorts(etablissement_context.id_context_categorie, ids_classes_cohorts,
                                             eleve_id, eleve_infos, self.context.timestamp_now_sql)
            eleve_cohorts.extend(ids_classes_cohorts)

        # Inscription dans la cohorte associee au niveau de formation
        if ldap_student.niveau_formation:
            id_formation_cohort = self.__db.create_formation_cohort(etablissement_context.id_context_categorie,
                                                                    ldap_student.niveau_formation,
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
        id_user_info_data = self.__db.get_id_user_info_data(eleve_id, self.context.id_user_info_field_classe)
        if id_user_info_data is not None:
            self.__db.update_user_info_data(eleve_id, self.context.id_user_info_field_classe, ldap_student.classe)
            logging.debug("Mise à jour user_info_data")
        else:
            self.__db.insert_moodle_user_info_data(eleve_id, self.context.id_user_info_field_classe,
                                                   ldap_student.classe)
            logging.debug("Insertion user_info_data")

        # Mise a jour du Domaine
        user_domain = self.__config.constantes.default_domain
        if len(ldap_student.domaines) == 1:
            user_domain = ldap_student.domaines[0]
        else:
            if ldap_student.uai_courant and ldap_student.uai_courant in self.context.map_etab_domaine:
                user_domain = self.context.map_etab_domaine[ldap_student.uai_courant][0]
        logging.debug("Insertion du Domaine")
        self.__db.set_user_domain(eleve_id, self.context.id_field_domaine, user_domain)

    def mise_a_jour_enseignant(self, etablissement_context: EtablissementContext, ldap_teacher: TeacherLdap):
        enseignant_infos = "%s %s %s" % (ldap_teacher.uid, ldap_teacher.given_name, ldap_teacher.sn)

        if ldap_teacher.uai_courant and not etablissement_context.etablissement_regroupe:
            etablissement_context.etablissement_theme = ldap_teacher.uai_courant.lower()

        if not ldap_teacher.mail:
            ldap_teacher.mail = self.__config.constantes.default_mail

        # Affichage du mail reserve aux membres de cours
        mail_display = self.__config.constantes.default_mail_display
        if etablissement_context.ldap_structure.uai in self.__config.etablissements.listeEtabSansMail:
            # Desactivation de l'affichage du mail
            mail_display = 0

        # Insertion de l'enseignant
        id_user = self.__db.get_user_id(ldap_teacher.uid)
        if not id_user:
            self.__db.insert_moodle_user(ldap_teacher.uid, ldap_teacher.given_name, ldap_teacher.sn, ldap_teacher.mail,
                                         mail_display, etablissement_context.etablissement_theme)
            id_user = self.__db.get_user_id(ldap_teacher.uid)
        else:
            self.__db.update_moodle_user(id_user, ldap_teacher.given_name, ldap_teacher.sn, ldap_teacher.mail,
                                         mail_display, etablissement_context.etablissement_theme)

        # Mise ajour des droits sur les anciens etablissement
        if ldap_teacher.uais is not None and not etablissement_context.etablissement_regroupe:
            # Recuperation des uais des etablissements dans lesquels l'enseignant est autorise
            self.mettre_a_jour_droits_enseignant(enseignant_infos, etablissement_context.gereAdminLocal,
                                                 etablissement_context.id_context_categorie,
                                                 etablissement_context.id_context_course_forum,
                                                 id_user, ldap_teacher.uais)

            # Ajout du role de createur de cours au niveau de la categorie inter-etablissement Moodle
            self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                       self.context.id_context_categorie_inter_etabs, id_user)
        logging.info("        |_ Ajout du role de createur de cours dans la categorie inter-etablissements")

        # Si l'enseignant fait partie d'un CFA
        # Ajout du role createur de cours au niveau de la categorie inter-cfa
        if etablissement_context.ldap_structure.type == self.__config.constantes.type_structure_cfa:
            self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                       self.context.id_context_categorie_inter_cfa, id_user)
            logging.info("        |_ Ajout du role de createur de cours dans la categorie inter-cfa")

            # ajout du role de createur de cours dans l'etablissement
            self.__db.add_role_to_user(self.__config.constantes.id_role_createur_cours,
                                       etablissement_context.id_context_categorie, id_user)

        # Ajouts des autres roles pour le personnel établissement
        if 'National_3' in ldap_teacher.profils or 'National_5' in ldap_teacher.profils or 'National_6' in \
                ldap_teacher.profils or 'National_4' in ldap_teacher.profils:
            # Ajout des roles sur le contexte forum
            self.__db.add_role_to_user(self.__config.constantes.id_role_eleve,
                                       etablissement_context.id_context_course_forum, id_user)
            # Inscription à la Zone Privée
            self.__db.enroll_user_in_course(self.__config.constantes.id_role_eleve,
                                            etablissement_context.id_zone_privee, id_user)

            if 'National_3' in ldap_teacher.profils or 'National_5' in \
                    ldap_teacher.profils or 'National_6' in ldap_teacher.profils:
                if not etablissement_context.gereAdminLocal:
                    self.__db.add_role_to_user(self.context.id_role_extended_teacher,
                                               etablissement_context.id_context_categorie,
                                               id_user)
            elif 'National_4' in ldap_teacher.profils:
                self.__db.add_role_to_user(self.__config.constantes.id_role_directeur,
                                           etablissement_context.id_context_categorie, id_user)

        # Ajout des droits d'administration locale pour l'etablissement
        if etablissement_context.gereAdminLocal:
            for member in ldap_teacher.is_member_of:
                # L'enseignant est il administrateur Moodle ?
                adminMoodle = re.match(etablissement_context.regexpAdminMoodle, member, flags=re.IGNORECASE)
                if adminMoodle:
                    insert = self.__db.insert_moodle_local_admin(etablissement_context.id_context_categorie, id_user)
                    if insert:
                        logging.info("      |_ Insertion d'un admin  local %s %s %s" % (
                            ldap_teacher.uid, ldap_teacher.given_name, ldap_teacher.sn))
                    # Si il est adminin local on en fait un utilisateur avancé par default
                    if not self.__db.is_enseignant_avance(id_user, self.context.id_role_advanced_teacher):
                        self.__db.add_role_to_user(self.context.id_role_advanced_teacher, 1, id_user)
                    break
                else:
                    delete = self.__db.delete_moodle_local_admin(self.context.id_context_categorie_inter_etabs, id_user)
                    if delete:
                        logging.info("      |_ Suppression d'un admin local %s %s %s" % (
                            ldap_teacher.uid, ldap_teacher.given_name, ldap_teacher.sn))

        # Mise a jour du Domaine
        user_domain = self.__config.constantes.default_domain
        if len(ldap_teacher.domaines) == 1:
            user_domain = ldap_teacher.domaines[0]
        else:
            if ldap_teacher.uai_courant and ldap_teacher.uai_courant in self.context.map_etab_domaine:
                user_domain = self.context.map_etab_domaine[ldap_teacher.uai_courant][0]
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

    def create_profs_etabs_cohorts(self, etablissement_context: EtablissementContext, since_timestamp):
        self.__db.create_profs_etabs_cohorts(etablissement_context.id_context_categorie,
                                             etablissement_context.uai,
                                             self.context.timestamp_now_sql,
                                             since_timestamp,
                                             self.__ldap)
