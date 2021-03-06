# coding: utf-8
"""
Configuration
"""
from logging import getLogger
from typing import List, Dict, Union

import ruamel.yaml as yaml

log = getLogger('config')


class _BaseConfig:
    def __init__(self, **entries):
        self.update(**entries)

    def update(self, **entries):
        """
        Met à jour les données de l'objet de configuration.
        :param entries:
        :return:
        """
        self.__dict__.update(entries)


class WebServiceConfig(_BaseConfig):
    """
    Configuration du Webservice Moodle
    """

    def __init__(self, **entries):
        self.token = ""
        """Token d'accès au webservice Moodle"""

        self.moodle_host = ""
        """Host HTTP cible pour accéder au webservice Moodle"""

        self.backup_cmd = "php backup.php --courseid=%courseid% --destination=/MoodleBackups"
        """Commande à executer pour lancer la backup d'un cours"""

        self.backup_success_re = "Backup completed"
        """Expression Reguliere à appliquer sur le retour de la sortie standard de backup_cmd pour vérifier le 
        succès de l'opération"""

        super().__init__(**entries)


class DeleteConfig(_BaseConfig):
    """
    Configuration des valeurs pour l'anonymisation/suppression
    """

    def __init__(self, **entries):
        self.ids_users_undeletable = [1, 2]
        """Ids des utilisateurs qui ne doivent en aucun cas être supprimés"""

        self.ids_roles_teachers = [2]
        """Ids des roles considérés comme enseignants pour la suppression"""

        self.delay_anonymize_student = 60
        """Délai, en jours, avant de anonymiser un élève qui n'est plus présent dans l'annuaire LDAP"""

        self.delay_delete_student = 90
        """Délai, en jours, avant de supprimer un élève qui n'est plus présent dans l'annuaire LDAP"""

        self.delay_anonymize_teacher = 90
        """Délai, en jours, avant d'anonymiser un enseignant qui n'est plus présent dans l'annuaire LDAP"""

        self.delay_delete_teacher = 365
        """Délai, en jours, avant de supprimer un enseignant qui n'est plus présent dans l'annuaire LDAP"""

        self.delay_backup_course = 365
        """Délai, en jours, avant de sauvegarder un cours inutilisé"""

        super().__init__(**entries)


class ConstantesConfig(_BaseConfig):
    """
    Configuration des contstantes
    """

    def __init__(self, **entries):
        self.anonymous_phone = "0606060606"
        """Valeur assignée aux numeros de telephones des utilisateurs anonymisés"""

        self.anonymous_name = "Anonyme"
        """Valeur assignée aux champs divers du profil des utilisateurs anonymisés"""

        self.anonymous_mail = "anonyme@email.com"
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

        self.id_role_admin = 1  # type: int
        """Id pour le role admin"""

        self.id_role_createur_cours = 2  # type: int
        """Id pour le role createur de cours"""

        self.id_role_proprietaire_cours = 11  # type: int
        """Id pour le role propriétaire de cours"""

        self.id_role_enseignant = 3  # type: int
        """Id pour le role enseignant"""

        self.id_role_eleve = 5  # type: int
        """Id pour le role eleve"""

        self.id_role_inspecteur = 9  # type: int
        """Id pour le role inspecteur"""

        self.id_role_directeur = 18  # type: int
        """Id pour le role directeur"""

        self.id_role_utilisateur_limite = 14  # type: int
        """Id pour le role d'utilisateur avec droits limites"""

        self.type_structure_cfa = "CFA"  # type: str
        """Type de structure d'un CFA"""

        self.type_structure_clg = "COLLEGE"  # type: str
        """Type de structure d'un college"""

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

        self.baseDN = "dc=esco-centre,dc=fr"  # type: str
        """DN de base"""

        self.structuresRDN = "ou=structures"  # type: str
        """OU pour les structures"""

        self.personnesRDN = "ou=people"  # type: str
        """OU pour les personnes"""

        self.groupsRDN = "ou=groups"  # type: str
        """OU pour les groupes"""

        self.adminRDN = "ou=administrateurs"  # type: str
        """OU pour les administrateurs"""

        super().__init__(**entries)

    @property
    def structuresDN(self) -> str:
        """
        DN pour les structures
        """
        return self.structuresRDN + ',' + self.baseDN

    @property
    def personnesDN(self) -> str:
        """
        DN pour les personnes
        """
        return self.personnesRDN + ',' + self.baseDN

    @property
    def groupsDN(self) -> str:
        """
        DN pour les personnes
        """
        return self.groupsRDN + ',' + self.baseDN

    @property
    def adminDN(self) -> str:
        """
        DN pour les admins
        """
        return self.adminRDN + ',' + self.baseDN


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
        self.etabRgp = []  # type: List[EtablissementRegroupement]
        """Regroupement d'etablissements"""

        self.inter_etab_categorie_name = 'Catégorie Inter-Établissements'  # type: str
        """Nom de la catégorie inter-etablissement"""

        self.inter_etab_categorie_name_cfa = 'Catégorie Inter-CFA'  # type: str
        """Nom de la catégorie inter-etablissement pour les CFA"""

        self.listeEtab = []  # type: List[str]
        """Liste des établissements"""

        self.listeEtabSansAdmin = []  # type: List[str]
        """Etablissements sans administrateurs"""

        self.listeEtabSansMail = []  # type: List[str]
        """Etablissements dont le mail des professeurs n'est pas synchronise"""

        self.prefixAdminMoodleLocal = "(esco|clg37):admin:Moodle:local:"  # type: str
        """Préfixe de l'attribut "isMemberOf" indiquant que l'utilisateur est un administrateur local de Moodle"""

        self.prefixAdminLocal = "(esco|clg37):admin:local:"  # type: str
        """Prefix de l'attribut "isMemberOf" indiquant que l'utilisateur est un administrateur local"""

        super().__init__(**entries)

    def update(self, **entries):
        if 'etabRgp' in entries:
            entries['etabRgp'] = list(map(lambda d: EtablissementRegroupement(**d), entries['etabRgp']))

        super().update(**entries)


class InterEtablissementsConfig(_BaseConfig):
    """
    Configuration de l'inter-établissement
    """

    def __init__(self, **entries):
        self.cohorts = {}  # type: Dict[str, str]
        """Cohortes à synchroniser"""

        self.categorie_name = '%%Cat%%gorie inter%%tablissements'  # type: str
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
        self.id = None
        self.type = "default"
        self.timestamp_store = TimestampStoreConfig()  # type: TimestampStoreConfig
        self.etablissements = EtablissementsConfig()  # type: EtablissementsConfig
        self.inter_etablissements = InterEtablissementsConfig()  # type: InterEtablissementsConfig
        self.inspecteurs = InspecteursConfig()  # type: InspecteursConfig

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

        super().update(**entries)

    def __str__(self):
        return self.type + " (id=%s)" % self.id if self.id else ""


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
        :return:
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
        :param config:
        :param config_fp:
        :param silent:
        :return:
        """
        for config_item in config_fp:
            try:
                with open(config_item) as fp:
                    data = yaml.safe_load(fp)
                    config.update(**data)
            except FileNotFoundError as e:
                message = "Le fichier de configuration n'a pas été chargé: " + str(e)
                if silent:
                    log.debug(message)
                else:
                    log.warning(message)
        return config

    def load(self, config: List[str], silent=False) -> Config:
        """
        Charge une configuration à partir d'une liste de fichier de configuration.
        :param config:
        :param silent:
        :return:
        """
        loaded_config = Config()
        loaded_config = self.update(loaded_config, config, silent)
        return loaded_config
