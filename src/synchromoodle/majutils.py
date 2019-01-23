# coding: utf-8

import logging
import re
import sys

from synchromoodle.timestamp import TimestampStore

from .dbutils import Database
from .config import EtablissementsConfig, Config
from .ldaputils import Ldap, StudentLdap

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


class EtablissementContext:
    id_context_categorie = None
    id_context_course_forum = None
    etablissement_regroupe = None
    ldap_structure = None
    gereAdminLocal = None
    regexpAdminMoodle = None
    regexpAdminLocal = None
    id_zone_privee = None
    etablissement_theme = None
    eleves_by_cohortes = None

    def __init__(self):
        self.eleves_by_cohortes = {}


class EleveContext:
    pass


class Synchronizer:
    __ldap = None  # type: Ldap
    __db = None  # type: Database
    __config = None  # type: Config

    context = None  # type: SyncContext
    maintenant_sql = None

    def __init__(self, ldap: Ldap, db: Database, config: Config):
        self.__ldap = ldap
        self.__db = db
        self.__config = config
        self.context = SyncContext()
        self.maintenant_sql = db.get_timestamp_now()

    def mise_a_jour_etab(self, uai) -> EtablissementContext:
        """
        Met a jour l'etablissement meme si celui-ci n'a pas ete modifie depuis la derniere synchro
        car des infos doivent etre recuperees dans Moodle dans tous les cas
        :return: EtabContext
        """
        logging.info("  |_ Traitement de l'établissement %s" % uai)
        context = EtablissementContext()
        context.gereAdminLocal = uai not in self.__config.etablissements.listeEtabSansAdmin
        context.etablissement_regroupe = est_grp_etab(uai, self.__config.etablissements)
        # Regex pour savoir si l'utilisateur est administrateur moodle
        context.regexpAdminMoodle = self.__config.users.prefixAdminMoodleLocal + ".*_%s$" % uai
        # Regex pour savoir si l'utilisateur est administrateur local
        context.regexpAdminLocal = self.__config.users.prefixAdminLocal + ".*_%s$" % uai

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
                                                                      etablissement_ou, self.maintenant_sql)

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

        # Ajout du role d'utilisateur avec droits limites
        # Pour les eleves de college
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
                                                                   ldap_student.classes, self.maintenant_sql)
            self.__db.enroll_user_in_cohorts(etablissement_context.id_context_categorie, ids_classes_cohorts,
                                             eleve_id, eleve_infos, self.maintenant_sql)
            eleve_cohorts.extend(ids_classes_cohorts)

        # Inscription dans la cohorte associee au niveau de formation
        if ldap_student.niveau_formation:
            id_formation_cohort = self.__db.create_formation_cohort(etablissement_context.id_context_categorie,
                                                                    ldap_student.niveau_formation,
                                                                    self.maintenant_sql)
            self.__db.enroll_user_in_cohort(id_formation_cohort, eleve_id, eleve_infos, self.maintenant_sql)
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
            self.__db.insert_moodle_user_info_data(eleve_id, self.context.id_user_info_field_classe, ldap_student.classe)
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
