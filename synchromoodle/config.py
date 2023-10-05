# coding: utf-8
# pylint: disable=too-few-public-methods, too-many-instance-attributes
"""
Configuration
"""
from logging import getLogger
from typing import List, Dict, Union
from ruamel import yaml

log = getLogger('config')


class _BaseConfig:
    def __init__(self, **entries):
        self.update(**entries)

    def update(self, **entries):
        """
        Met à jour les données de l'objet de configuration.

        :param entries:
        """
        self.__dict__.update(entries)


class WebServiceConfig(_BaseConfig):
    """
    Configuration du Webservice Moodle
    """

    def __init__(self, **entries):
        self.token = ""  # type: str
        """Token d'accès au webservice Moodle"""

        self.moodle_host = ""  # type: str
        """Host HTTP cible pour accéder au webservice Moodle"""

        self.user_delete_pagesize = 50 # type: int
        """Nombre d'utilisateurs qu'on supprime en 1 seul appel au web service"""

        super().__init__(**entries)


class DeleteConfig(_BaseConfig):
    """
    Configuration des valeurs pour l'anonymisation/suppression
    """

    def __init__(self, **entries):
        self.ids_users_undeletable = [1, 2, 3]  # type: list[int]
        """Ids des utilisateurs qui ne doivent en aucun cas être supprimés"""

        self.ids_roles_teachers = [2]  # type: list[int]
        """Ids des roles considérés comme enseignants pour la suppression"""

        self.delay_anonymize_student = 60  # type: int
        """Délai, en jours, avant de anonymiser un élève qui n'est plus présent dans l'annuaire LDAP"""

        self.delay_delete_student = 90  # type: int
        """Délai, en jours, avant de supprimer un élève qui n'est plus présent dans l'annuaire LDAP"""

        self.delay_anonymize_teacher = 90  # type: int
        """Délai, en jours, avant d'anonymiser un enseignant qui n'est plus présent dans l'annuaire LDAP"""

        self.delay_delete_teacher = 395  # type: int
        """Délai, en jours, avant de supprimer un enseignant qui n'est plus présent dans l'annuaire LDAP"""

        self.delay_backup_course = 365  # type: int
        """Délai, en jours, avant de sauvegarder un cours inutilisé"""

        self.delay_unused_course = 360  # type: int
        """Délai, en jours, avant de sauvegarder un cours non accédé"""

        self.delay_force_delete = 1095  # type: int
        """Délai, en jours, avant de supprimer un compte qui n'est plus présent
         dans l'annuaire LDAP peu importe ses références"""

        self.purge_cohorts = False  # type: bool
        """Booléen indiquant si on purge les cohortes s'il y a une action de suppression"""

        self.purge_zones_privees = False  # type: bool
        """Booléen indiquant si on purge les zones privées s'il y a une action de suppression"""

        super().__init__(**entries)


class ConstantesConfig(_BaseConfig):
    """
    Configuration des contstantes
    """

    def __init__(self, **entries):
        self.anonymous_phone = "0606060606"  # type: str
        """Valeur assignée aux numeros de telephones des utilisateurs anonymisés"""

        self.anonymous_name = "Anonyme"  # type: str
        """Valeur assignée aux champs divers du profil des utilisateurs anonymisés"""

        self.anonymous_mail = "anonyme@email.com"  # type: str
        """Adresse email assignée aux utilisateurs anonymisés"""

        self.default_moodle_theme = "netocentre"  # type: str
        """Thèmes par défault pour les utilisateurs inter-etabs"""

        self.default_mail_display = 2  # type: int
        """Par défaut, les mails sont uniquement affichés aux participants du cours"""

        self.default_mail = 'non_renseigne@netocentre.fr'  # type: str
        """Email utilise lorsque les personnes n'ont pas d'email dans le LDAP"""

        self.default_domain = "lycees.netocentre.fr"  # type: str
        """Domaine par défaut"""

        self.id_instance_moodle = 1  # type: int
        """Id de l'instance concernant Moodle"""

        self.niveau_ctx_categorie = 40  # type: int
        """Niveau de contexte pour une categorie"""

        self.niveau_ctx_cours = 50  # type: int
        """Niveau de contexte pour un cours"""

        self.niveau_ctx_forum = 70  # type: int
        """Niveau de contexte pour un forum"""

        self.niveau_ctx_bloc = 80  # type: int
        """Niveau de contexte pour un bloc"""

        self.id_role_createur_cours = 2  # type: int
        """Id pour le role createur de cours"""

        self.id_role_proprietaire_cours = 11  # type: int
        """Id pour le role propriétaire de cours"""

        self.id_role_enseignant = 3  # type: int
        """Id pour le role enseignant"""

        self.id_role_eleve = 5  # type: int
        """Id pour le role eleve"""

        self.id_role_directeur = 18  # type: int
        """Id pour le role directeur"""

        self.id_role_utilisateur_limite = 14  # type: int
        """Id pour le role d'utilisateur avec droits limites"""

        self.id_role_bigbluebutton = 21 # type: int
        """Id pour le role bigbluebutton"""

        self.type_structure_cfa = "CFA"  # type: str
        """Type de structure d'un CFA"""

        self.type_structure_clg = "COLLEGE"  # type: str
        """Type de structure d'un college"""

        self.type_structure_lycee_start_with = "LYCEE "  # type: str
        """Type de structure d'un lycée commence par"""

        self.type_structure_ens_adapte = "ETABLISSEMENT REGIONAL D'ENSEIGNT ADAPTE" # type: str
        """Type de structure pour l'enseignement adapté"""

        self.type_structure_cfa_agricole = "CFA AGRICOLE"
        """Type de structure d'un cfa agricole"""

        self.type_structure_jointure_en_start_with = "AC-ORLEANS-TOURS$"
        """Jointure de type de structure pour l'enseignement national"""

        self.uai_dane = "0450080T"  # type: string
        """Uai de la dane"""

        self.departements = ['18', '28', '36', '37', '41', '45']  # type: list[int]
        """Liste des départements pour les cohortes de la dane"""

        # --- Patterns Eleves Classes --- #

        self.cohortname_pattern_eleves_classe = "Élèves de la Classe %" #type: str
        """Pattern à appliquer pour le nom des cohortes de classes d'élèves"""

        self.cohortidnumber_pattern_eleves_classe = "Classe %" #type: str
        """Pattern à appliquer pour l'idnumber des cohortes de classes d'élèves"""

        self.cohortdesc_pattern_eleves_classe = "Élèves de la Classe %" #type: str
        """Pattern à appliquer pour la description des cohortes de classes d'élèves"""

        # --- Patterns Eleves Niveau formation --- #

        self.cohortname_pattern_eleves_niv_formation = "Élèves du Niveau de formation %" #type: str
        """Pattern à appliquer pour le nom des cohortes de niveau de formation d'élèves"""

        self.cohortidnumber_pattern_eleves_niv_formation = "Élèves du Niveau de formation %" #type: str
        """Pattern à appliquer pour l'idnumber des cohortes de niveau de formation d'élèves"""

        self.cohortdesc_pattern_eleves_niv_formation = "Élèves avec le Niveau de formation %" #type: str
        """Pattern à appliquer pour la description des cohortes de niveau de formation d'élèves"""

        # --- Patterns Enseignants Classes --- #

        self.cohortname_pattern_enseignants_classe = "Profs de la Classe %" #type: str
        """Pattern à appliquer pour le nom des cohortes de classes d'enseignants"""

        self.cohortidnumber_pattern_enseignants_classe = "Profs de la Classe %" #type: str
        """Pattern à appliquer pour l'idnumber des cohortes de classes d'élèves"""

        self.cohortdesc_pattern_enseignants_classe = "Enseignants de la Classe %" #type: str
        """Pattern à appliquer pour la description des cohortes de classes d'élèves"""

        # --- Patterns Enseignants Niveau formation --- #

        self.cohortname_pattern_enseignants_niv_formation = "Profs du niveau de formation %" #type: str
        """Pattern à appliquer pour le nom des cohortes de niveau de formation d'enseignants"""

        self.cohortidnumber_pattern_enseignants_niv_formation = "Profs du niveau de formation %" #type: str
        """Pattern à appliquer pour l'idnumber des cohortes de niveau de formation d'élèves"""

        self.cohortdesc_pattern_enseignants_niv_formation = "Enseignants avec le Niveau de formation %" #type: str
        """Pattern à appliquer pour la description des cohortes de niveau de formation d'élèves"""

        # --- Patterns Enseignants Etablissement --- #

        self.cohortname_pattern_enseignants_etablissement = "Profs de l'établissement %" #type: str
        """Pattern à appliquer pour le nom des cohortes d'établissements d'enseignants"""

        self.cohortidnumber_pattern_enseignants_etablissement = "Profs de l'établissement %" #type: str
        """Pattern à appliquer pour l'idnumber des cohortes de niveau de formation d'élèves"""

        self.cohortdesc_pattern_enseignants_etablissement = "Enseignants de l'établissement %" #type: str
        """Pattern à appliquer pour la description des cohortes de niveau de formation d'élèves"""

        # --- Regex noms des cohortes --- #

        self.cohortname_pattern_re_eleves_classe = r'(Élèves de la Classe )(.*)$' #type: str
        """Regex à appliquer pour le nom des cohortes de classes d'élèves"""

        self.cohortname_pattern_re_eleves_niv_formation = r'(Élèves du Niveau de formation )(.*)$' #type: str
        """Regex à appliquer pour le nom des cohortes de niveau de formation d'élèves"""

        self.cohortname_pattern_re_enseignants_classe = r'(Profs de la Classe )(.*)$' #type: str
        """Regex à appliquer pour le nom des cohortes de classes d'enseignants"""

        self.cohortname_pattern_re_enseignants_niv_formation = r"(Profs du niveau de formation )(.*)$" #type: str
        """Regex à appliquer pour le nom des cohortes de niveau de formation d'enseignants"""

        self.cohortname_pattern_re_enseignants_etablissement = r"(Profs de l'établissement )(.*)$" #type: str
        """Regex à appliquer pour le nom des cohortes d'établissements d'enseignants"""

        self.moodledatadir = "" #type: str
        """Path vers le dossier moodledata"""

        self.backup_destination = "" #type: str
        """Chemin vers la destination des fichiers de backup des cours"""

        super().__init__(**entries)


class DatabaseConfig(_BaseConfig):
    """
    Configuration de la base de données Moodle
    """

    def __init__(self, **entries):
        self.database = "moodle"  # type: str
        """Nom de la base de données"""

        self.user = "moodle"  # type: str
        """Nom de l'utilisateur moodle"""

        self.password = "moodle"  # type: str
        """Mot de passe de l'utilisateur moodle"""

        self.host = "192.168.1.100"  # type: str
        """Adresse IP ou nom de domaine de la base de données"""

        self.port = 9806  # type: int
        """Port TCP"""

        self.entete = "mdl_"  # type: str
        """Entêtes des tables"""

        self.charset = "utf8"  # type: str
        """Charset à utiliser pour la connexion"""

        super().__init__(**entries)


class LdapConfig(_BaseConfig):
    """
    Configuration de l'annuaire LDAP.
    """

    def __init__(self, **entries):
        self.uri = "ldap://192.168.1.100:9889"  # type: str
        """URI du serveur LDAP"""

        self.username = "cn=admin,ou=administrateurs,dc=esco-centre,dc=fr"  # type: str
        """Utilisateur"""

        self.password = "admin"  # type: str
        """Mot de passe"""

        self.base_dn = "dc=esco-centre,dc=fr"  # type: str
        """DN de base"""

        self.structures_rdn = "ou=structures"  # type: str
        """OU pour les structures"""

        self.personnes_rdn = "ou=people"  # type: str
        """OU pour les personnes"""

        self.groups_rdn = "ou=groups"  # type: str
        """OU pour les groupes"""

        self.admin_rdn = "ou=administrateurs"  # type: str
        """OU pour les administrateurs"""

        self.page_size = 10000 # type: int
        """Taille d'une page pour les grandes requêtes"""

        self.modify_timestamp_delay = 0 # type: int
        """Nombre d'heures de marge si désynchro du LDAP"""

        super().__init__(**entries)

    @property
    def structures_dn(self) -> str:
        """
        DN pour les structures
        """
        return self.structures_rdn + ',' + self.base_dn

    @property
    def personnes_dn(self) -> str:
        """
        DN pour les personnes
        """
        return self.personnes_rdn + ',' + self.base_dn

    @property
    def groups_dn(self) -> str:
        """
        DN pour les personnes
        """
        return self.groups_rdn + ',' + self.base_dn

    @property
    def admin_dn(self) -> str:
        """
        DN pour les admins
        """
        return self.admin_rdn + ',' + self.base_dn


class DaneConfig(_BaseConfig):
    """
    Configuration de la dane
    """

    def __init__(self, **entries):
        self.dane_attribut = "isMemberOf" # type: str
        """Valeur de l'attribut de la dane"""

        self.dane_user = "acad:Services_Academique:ACADEMIE D ORLEANS-TOURS_0450080T:Groupes locaux:DANE"  # type: str
        """Valeur du filtre pour les utilisateurs de la dane dans le ldap"""

        self.dane_user_medic = "acad:Services_Academique:ACADEMIE D ORLEANS-TOURS_0450080T:PERSONNELS MEDICO-SOCIAUX" #type: str
        """Valeur du filtre pour les utilisateurs médicaux-sociaux de la dane"""

        self.cohort_medic_dane_name = "Personnels medico-sociaux"  #type: str
        """Nom de la cohorte dane des personnels médico-sociaux"""

        super().__init__(**entries)

class EtablissementRegroupement(_BaseConfig):
    """
    Configuration d'un regroupement d'établissement
    """

    def __init__(self, **entries):
        self.nom = ""  # type: str
        """Nom du regroupement d'etablissements"""

        self.uais = []  # type: List[str]
        """Liste des UAI consituant le regroupement"""

        super().__init__(**entries)


class EtablissementsConfig(_BaseConfig):
    """
    Configuration des établissements
    """

    def __init__(self, **entries):
        self.etab_rgp = []  # type: List[EtablissementRegroupement]
        """Regroupement d'etablissements"""

        self.inter_etab_categorie_name = 'Catégorie Inter-Établissements'  # type: str
        """Nom de la catégorie inter-etablissement"""

        self.inter_etab_categorie_name_cfa = 'Catégorie Inter-CFA'  # type: str
        """Nom de la catégorie inter-etablissement pour les CFA"""

        self.liste_etab = []  # type: List[str]
        """Liste des établissements"""

        self.liste_etab_sans_admin = []  # type: List[str]
        """Etablissements sans administrateurs"""

        self.liste_etab_sans_mail = []  # type: List[str]
        """Etablissements dont le mail des professeurs n'est pas synchronise"""

        self.prefix_admin_moodle_local = "(esco|clg37):admin:Moodle:local:"  # type: str
        """Préfixe de l'attribut "isMemberOf" indiquant que l'utilisateur est un administrateur local de Moodle"""

        self.prefix_admin_local = "(esco|clg37):admin:local:"  # type: str
        """Prefix de l'attribut "isMemberOf" indiquant que l'utilisateur est un administrateur local"""

        super().__init__(**entries)

    def update(self, **entries):
        if 'etab_rgp' in entries:
            entries['etab_rgp'] = list(map(lambda d: EtablissementRegroupement(**d), entries['etab_rgp']))

        super().update(**entries)

class SpecificCohortsConfig(_BaseConfig):
    """
    Configuration des cohortes spécifiques à un établissement
    """

    def __init__(self, **entries):
        self.cohorts = {}  # type: Dict[str, Dict[str,str]]
        """Cohortes spécifiques à syncrhoniser"""

        super().__init__(**entries)

class InterEtablissementsConfig(_BaseConfig):
    """
    Configuration de l'inter-établissement
    """

    def __init__(self, **entries):
        self.cohorts = {}  # type: Dict[str, str]
        """Cohortes à synchroniser"""

        self.categorie_name = 'Catégorie Inter-Établissements'  # type: str
        """Nom de la catégorie inter-etablissement"""

        self.ldap_attribut_user = "isMemberOf"  # type: str
        """Attribut utilisé pour determiner les utilisateurs inter-établissement"""

        self.ldap_valeur_attribut_user = ["cfa:Applications:Espace_Moodle:Inter_etablissements"]  # type: List[str]
        """Valeurs possibles de l'attribut pour déterminer si l'utilisateur est un utilisateur inter-établissement"""

        self.ldap_valeur_attribut_admin = "cfa:admin:Moodle:local:Inter_etablissements"  # type: str
        """Utilisateurs administrateurs de la section inter-etablissement"""

        self.cle_timestamp = "INTER_ETAB"  # type: str
        """Clé pour stocker le timestamp du dernier traitement inter-etablissements"""

        super().__init__(**entries)


class InspecteursConfig(_BaseConfig):
    """
    Configuration des inspecteurs
    """

    def __init__(self, **entries):
        self.ldap_attribut_user = "ESCOPersonProfils"  # type: str
        """Attribut utilisé pour determiner les inspecteurs"""

        self.ldap_valeur_attribut_user = ["INS"]  # type: List[str]
        """Valeur de l'attribute pour déterminer les inspecteurs"""

        self.cle_timestamp = "INSPECTEURS"  # type: str
        """Clé pour stocker le timestamp du dernier traitement inter-etablissements"""

        super().__init__(**entries)


class TimestampStoreConfig(_BaseConfig):
    """
    Configuration des timestamp de traitement précédent
    """

    def __init__(self, **entries):
        self.file = "timestamps.txt"  # type: str
        """Fichier contenant les dates de traitement précedent pour les établissements"""

        self.separator = "-"  # type: str
        """Séparateur utilisé dans le fichier de traitement pour séparer l'etablissement des date de traitement
        précedent"""

        super().__init__(**entries)


class ActionConfig(_BaseConfig):
    """
    Configuration d'une action
    """

    def __init__(self, **entries):
        self.id = None  # type: str
        self.type = "default"  # type: str
        self.timestamp_store = TimestampStoreConfig()  # type: TimestampStoreConfig
        self.etablissements = EtablissementsConfig()  # type: EtablissementsConfig
        self.inter_etablissements = InterEtablissementsConfig()  # type: InterEtablissementsConfig
        self.inspecteurs = InspecteursConfig()  # type: InspecteursConfig
        self.specific_cohorts = SpecificCohortsConfig() #type: SpecificCohortsConfig

        super().__init__(**entries)

    def update(self, **entries):
        if 'etablissements' in entries:
            self.etablissements.update(**entries['etablissements'])
            entries['etablissements'] = self.etablissements
        if 'interEtablissements' in entries:
            self.inter_etablissements.update(**entries['interEtablissements'])
            entries['interEtablissements'] = self.inter_etablissements
        if 'inspecteurs' in entries:
            self.inspecteurs.update(**entries['inspecteurs'])
            entries['inspecteurs'] = self.inspecteurs
        if 'timestampStore' in entries:
            self.timestamp_store.update(**entries['timestampStore'])
            entries['timestampStore'] = self.timestamp_store
        if 'specificCohorts' in entries:
            self.specific_cohorts.update(**entries['specificCohorts'])
            entries['specificCohorts'] = self.specific_cohorts

        super().update(**entries)

    def __str__(self):
        return self.type + f" (id={self.id})" if self.id else ""


class Config(_BaseConfig):
    """
    Configuration globale.
    """

    def __init__(self, **entries):
        super().__init__(**entries)

        self.delete = DeleteConfig()  # type: DeleteConfig
        self.webservice = WebServiceConfig()  # type: WebServiceConfig
        self.constantes = ConstantesConfig()  # type: ConstantesConfig
        self.database = DatabaseConfig()  # type: DatabaseConfig
        self.ldap = LdapConfig()  # type: LdapConfig
        self.dane = DaneConfig()  # type: DaneConfig
        self.actions = []  # type: List[ActionConfig]
        self.logging = True  # type: Union[dict, str, bool]

    def update(self, **entries):
        if 'delete' in entries:
            self.delete.update(**entries['delete'])
            entries['delete'] = self.delete
        if 'webservice' in entries:
            self.webservice.update(**entries['webservice'])
            entries['webservice'] = self.webservice
        if 'constantes' in entries:
            self.constantes.update(**entries['constantes'])
            entries['constantes'] = self.constantes
        if 'database' in entries:
            self.database.update(**entries['database'])
            entries['database'] = self.database
        if 'ldap' in entries:
            self.ldap.update(**entries['ldap'])
            entries['ldap'] = self.ldap
        if 'dane' in entries:
            self.dane.update(**entries['dane'])
            entries['dane'] = self.dane
        if 'actions' in entries:
            actions = entries['actions']
            for action in actions:
                existing_action = next((x for x in self.actions if 'id' in action and x.id == action['id']), None)
                if existing_action:
                    existing_action.update(**action)
                else:
                    self.actions.append(ActionConfig(**action))
            entries['actions'] = self.actions

        super().update(**entries)

    def validate(self):
        """
        Valide la configuration.

        :raises ValueError: Si aucune action n'est définie dans la configuration
        """
        if not self.actions:
            raise ValueError("Au moins une action doit être définie dans la configuration.")


class ConfigLoader:
    """
    Chargement de la configuration
    """

    def update(self, config: Config, config_fp: List[str], silent=False) -> Config:
        """
        Met à jour la configuration avec le chargement d'une une liste de fichier de configuration.

        :param config: L'objet représentant la configuration
        :param config_fp: La liste des noms de fichier pour la configuration
        :param silent: Afficher les excepetion en tant que debug ou warning dans les logs
        :raises FileNotFoundError: Si un des fichiers spécifiés n'existe pas
        :return: La configuration mise à jour
        """
        for config_item in config_fp:
            try:
                with open(config_item, encoding="utf-8") as config_file:
                    yaml_config = yaml.YAML(typ='unsafe', pure=True)
                    data = yaml_config.load(config_file)
                    config.update(**data)
            except FileNotFoundError as exception:
                message = "Le fichier de configuration n'a pas été chargé: " + str(exception)
                if silent:
                    log.debug(message)
                else:
                    log.warning(message)
        return config

    def load(self, config: List[str], silent=False) -> Config:
        """
        Charge une configuration à partir d'une liste de fichier de configuration.

        :param config: La liste des noms de fichier pour la configuration
        :param silent: Afficher les excepetion en tant que debug ou warning dans les logs
        :return: La configuration créée
        """
        loaded_config = Config()
        loaded_config = self.update(loaded_config, config, silent)
        return loaded_config
