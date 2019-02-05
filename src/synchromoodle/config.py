# coding: utf-8
import logging
from typing import List, Dict

import ruamel.yaml as yaml

log = logging.getLogger('config')


class _BaseConfig:
    def __init__(self, **entries):
        self.update(**entries)

    def update(self, **entries):
        self.__dict__.update(entries)


class ConstantesConfig(_BaseConfig):
    def __init__(self, **entries):
        super().__init__(**entries)

    default_moodle_theme = "netocentre"  # type: str
    """Thèmes par défault pour les utilisateurs inter-etabs"""

    default_mail_display = 2  # type: int
    """Par défaut, les mails sont uniquement affichés aux participants du cours"""

    default_mail = 'non_renseigne@netocentre.fr'  # type: str
    """Email utilise lorsque les personnes n'ont pas d'email dans le LDAP"""

    default_domain = "lycees.netocentre.fr"  # type: str
    """Domaine par défaut"""

    id_instance_moodle = 1  # type: int
    """Id de l'instance concernant Moodle"""

    niveau_ctx_categorie = 40  # type: int
    """Niveau de contexte pour une categorie"""

    niveau_ctx_cours = 50  # type: int
    """Niveau de contexte pour un cours"""

    niveau_ctx_forum = 70  # type: int
    """Niveau de contexte pour un forum"""

    niveau_ctx_bloc = 80  # type: int
    """Niveau de contexte pour un bloc"""

    id_role_admin = 1  # type: int
    """Id pour le role admin"""

    id_role_createur_cours = 2  # type: int
    """Id pour le role createur de cours"""

    id_role_enseignant = 3  # type: int
    """Id pour le role enseignant"""

    id_role_eleve = 5  # type: int
    """Id pour le role eleve"""

    id_role_inspecteur = 9  # type: int
    """Id pour le role inspecteur"""

    id_role_directeur = 18  # type: int
    """Id pour le role directeur"""

    id_role_utilisateur_limite = 14  # type: int
    """Id pour le role d'utilisateur avec droits limites"""

    type_structure_cfa = "CFA"  # type: str
    """Type de structure d'un CFA"""

    type_structure_clg = "COLLEGE"  # type: str
    """Type de structure d'un college"""


class DatabaseConfig(_BaseConfig):
    def __init__(self, **entries):
        super().__init__(**entries)

    database = "moodle"  # type: str
    """Nom de la base de données"""

    user = "moodle"  # type: str

    """Nom de l'utilisateur moodle"""

    password = "moodle"  # type: str
    """Mot de passe de l'utilisateur moodle"""

    host = "192.168.1.100"  # type: str
    """Adresse IP ou nom de domaine de la base de données"""

    port = 9806  # type: int
    """Port TCP"""

    entete = "mdl_"  # type: str
    """Entêtes des tables"""

    charset = "utf8"  # type: str
    """Charset à utiliser pour la connection"""


class LdapConfig(_BaseConfig):
    def __init__(self, **entries):
        super().__init__(**entries)

    uri = "ldap://192.168.1.100:9889"  # type: str
    """URI du serveur LDAP"""

    username = "cn=admin,ou=administrateurs,dc=esco-centre,dc=fr"  # type: str
    """Utilisateur"""

    password = "admin"  # type: str
    """Mot de passe"""

    baseDN = "dc=esco-centre,dc=fr"  # type: str
    """DN de base"""

    structuresRDN = "ou=structures"  # type: str
    """OU pour les structures"""

    personnesRDN = "ou=people"  # type: str
    """OU pour les personnes"""

    groupsRDN = "ou=groups"  # type: str
    """OU pour les groupes"""

    adminRDN = "ou=administrateurs"  # type: str
    """OU pour les administrateurs"""

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


class EtablissementRegroupement:
    nom = ""  # type: str
    """Nom du regroupement d'etablissements"""

    uais = []  # type: List[str]
    """Liste des UAI consituant le regroupement"""


class EtablissementsConfig(_BaseConfig):
    def __init__(self, **entries):
        super().__init__(**entries)

    etabRgp = []  # type: List[EtablissementRegroupement]
    """Regroupement d'etablissements"""

    inter_etab_categorie_name = 'Catégorie Inter-Établissements'  # type: str
    """Nom de la catégorie inter-etablissement"""

    inter_etab_categorie_name_cfa = 'Catégorie Inter-CFA'  # type: str
    """Nom de la catégorie inter-etablissement pour les CFA"""

    listeEtab = []  # type: List[str]
    """Liste des établissements"""

    listeEtabSansAdmin = []  # type: List[str]
    """Etablissements sans administrateurs"""

    listeEtabSansMail = []  # type: List[str]
    """Etablissements dont le mail des professeurs n'est pas synchronise"""

    prefixAdminMoodleLocal = "(esco|clg37):admin:Moodle:local:"  # type: str
    """Préfixe de l'attribut "isMemberOf" indiquant que l'utilisateur est un administrateur local de Moodle"""

    prefixAdminLocal = "(esco|clg37):admin:local:"  # type: str
    """Prefix de l'attribut "isMemberOf" indiquant que l'utilisateur est un administrateur local"""


class InterEtablissementsConfig(_BaseConfig):
    def __init__(self, **entries):
        super().__init__(**entries)

    cohorts = {}  # type: Dict[str, str]
    """Cohortes à synchroniser"""

    categorie_name = '%%Cat%%gorie inter%%tablissements'  # type: str
    """Nom de la catégorie inter-etablissement"""

    ldap_attribut_user = "isMemberOf"  # type: str
    """Attribut utilisé pour determiner les utilisateurs inter-établissement"""

    ldap_valeur_attribut_user = ["cfa:Applications:Espace_Moodle:Inter_etablissements"]  # type: str
    """Valeurs possibles de l'attribut pour déterminer si l'utilisateur est un utilisateur inter-établissement"""

    ldap_valeur_attribut_admin = "cfa:admin:Moodle:local:Inter_etablissements"  # type: str
    """Utilisateurs administrateurs de la section inter-etablissement"""

    cle_timestamp = "INTER_ETAB"  # type: str
    """Clé pour stocker le timestamp du dernier traitement inter-etablissements"""


class InspecteursConfig(_BaseConfig):
    def __init__(self, **entries):
        super().__init__(**entries)

    ldap_attribut_user = "ESCOPersonProfils"  # type: str
    """Attribut utilisé pour determiner les inspecteurs"""

    ldap_valeur_attribut_user = ["INS"]  # type: str
    """Valeur de l'attribute pour déterminer les inspecteurs"""

    cle_timestamp = "INSPECTEURS"  # type: str
    """Clé pour stocker le timestamp du dernier traitement inter-etablissements"""


class TimestampStoreConfig(_BaseConfig):
    def __init__(self, **entries):
        super().__init__(**entries)

    file = "timestamps.txt"  # type: str
    """Fichier contenant les dates de traitement précedent pour les établissements"""

    separator = "-"  # type: str
    """Séparateur utilisé dans le fichier de traitement pour séparer l'etablissement des date de traitement précedent"""


class Config:
    constantes = ConstantesConfig()  # type: ConstantesConfig
    database = DatabaseConfig()  # type: DatabaseConfig
    ldap = LdapConfig()  # type: LdapConfig
    timestamp_store = TimestampStoreConfig()  # type: TimestampStoreConfig
    etablissements = EtablissementsConfig()  # type: EtablissementsConfig
    inter_etablissements = InterEtablissementsConfig()  # type: InterEtablissementsConfig
    inspecteurs = InspecteursConfig()  # type: InspecteursConfig
    actions = ["default"]  # type: List[str]

    def update(self, data):
        if 'constantes' in data:
            self.constantes.update(**data['constantes'])
        if 'database' in data:
            self.database.update(**data['database'])
        if 'ldap' in data:
            self.ldap.update(**data['ldap'])
        if 'etablissements' in data:
            self.etablissements.update(**data['etablissements'])
        if 'interEtablissements' in data:
            self.inter_etablissements.update(**data['interEtablissements'])
        if 'inspecteurs' in data:
            self.inspecteurs.update(**data['inspecteurs'])
        if 'timestampStore' in data:
            self.timestamp_store.update(**data['timestampStore'])


class ConfigLoader:
    def update(self, config: Config, config_fp: List[str], silent=False) -> Config:
        for config_item in config_fp:
            try:
                with open(config_item) as fp:
                    data = yaml.safe_load(fp)
                    config.update(data)
            except FileNotFoundError as e:
                message = "Le fichier de configuration n'a pas été chargé: " + str(e)
                if silent:
                    log.debug(message)
                else:
                    log.warning(message)
        return config

    def load(self, config: List[str], silent=False) -> Config:
        loaded_config = Config()
        loaded_config = self.update(loaded_config, config, silent)
        return loaded_config
