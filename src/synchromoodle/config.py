import ruamel.yaml as yaml


class ConstantesConfig:
    def __init__(self, **entries):
        self.__dict__.update(entries)

    default_moodle_theme = "netocentre"
    """Thèmes par défault pour les utilisateurs inter-etabs"""

    #######################################
    # MAIL
    #######################################
    default_mail_display = 2
    """Par défaut, les mails sont uniquement affichés aux participants du cours"""

    default_mail = 'non_renseigne@netocentre.fr'
    """Email utilise lorsque les personnes n'ont pas d'email dans le LDAP"""

    default_domain = "lycees.netocentre.fr"
    """Domaine par défaut"""

    #######################################
    # CLES UTILISE POUR STOCKER LES TIMESTAMP
    #######################################
    cle_trt_inter_etab = "INTER_ETAB"
    """Cle pour pour stocker le timestamp dud dernier traitement inter-etablissements"""

    cle_trt_mahara = "MAHARA"
    """Cle pour stocker le timestamp dernier traitement mahara"""

    #######################################
    # NIVEAUX DE CONTEXTES
    #######################################
    id_instance_moodle = 1
    """Id de l'instance concernant Moodle"""

    niveau_ctx_cours = 50
    """Niveau de contexte pour un cours"""

    #######################################
    # ID ROLES
    #######################################
    id_role_createur_cours = 2
    """Id pour le role createur de cours"""

    id_role_enseignant = 3
    """Id pour le role enseignant"""

    id_role_eleve = 5
    """Id pour le role eleve"""

    id_role_inspecteur = 9
    """Id pour le role inspecteur"""

    id_role_directeur = 18
    """Id pour le role directeur"""

    # Id pour le role d'utilisateur avec droits limites
    id_role_utilisateur_limite = 14

    #######################################
    # LDAP
    #######################################
    type_structure_cfa = "CFA"
    """Type de structure d'un CFA"""

    type_structure_clg = "COLLEGE"
    """Type de structure d'un college"""


class DatabaseConfig:
    def __init__(self, **entries):
        self.__dict__.update(entries)

    database = "moodle"
    """Nom de la base de données"""

    user = "moodle"

    """Nom de l'utilisateur moodle"""

    password = "moodle"
    """Mot de passe de l'utilisateur moodle"""

    host = "192.168.1.100"
    """Adresse IP ou nom de domaine de la base de données"""

    port = 9806
    """Port TCP"""

    entete = "mdl_"
    """Entêtes des tables"""

    charset = "utf8"
    """Charset à utiliser pour la connection"""


class LdapConfig:
    def __init__(self, **entries):
        self.__dict__.update(entries)

    uri = "ldap://192.168.1.100:9889"
    """URI du serveur LDAP"""

    username = "cn=admin,ou=administrateurs,dc=esco-centre,dc=fr"
    """Utilisateur"""

    password = "admin"
    """Mot de passe"""

    baseDN = "dc=esco-centre,dc=fr"

    structuresOU = "ou=structures"
    """OU pour les structures"""

    personnesOU = "ou=people"
    """OU pour les personnes"""

    adminOU = "administrateurs"
    """OU pour les administrateurs"""

    prefixAdminMoodleLocal = "(esco|clg37):admin:Moodle:local:"
    """Préfixe de l'attribut "isMemberOf" indiquant que l'utilisateur est un administrateur local de Moodle"""

    prefixAdminLocal = "(esco|clg37):admin:local:"
    """Prefix de l'attribut "isMemberOf" indiquant que l'utilisateur est un administrateur local"""

    @property
    def structuresDN(self):
        """
        DN pour les structures
        """
        return self.structuresOU + ',' + self.baseDN

    @property
    def personnesDN(self):
        """
        DN pour les personnes
        """
        return self.personnesOU + ',' + self.baseDN

    @property
    def adminDN(self):
        """
        DN pour les admins
        """
        return self.adminOU + ',' + self.baseDN


class EtablissementsConfig:
    def __init__(self, **entries):
        self.__dict__.update(entries)

    NomEtabRgp = "nomEtabRgp"
    """???"""

    UaiRgp = "uai"
    """???"""

    EtabRgp = []
    """???"""

    listeEtab = []
    """Liste des établissements"""

    listeEtabSansAdmin = []
    """Etablissements sans administrateurs"""

    listeEtabSansMail = []
    """Etablissements dont le mail des professeurs n'est pas synchronise"""

    fileTrtPrecedent = "trtPrecedent_academique.txt"
    """Nom du fichier"""

    fileSeparator = "-"
    """Séparateur du fichier"""


class Config:
    constantes: ConstantesConfig = ConstantesConfig()
    database: DatabaseConfig = DatabaseConfig()
    ldap: LdapConfig = LdapConfig()
    etablissements: EtablissementsConfig = EtablissementsConfig()


class ConfigLoader:
    def load(self) -> Config:
        with open('config.yml') as fp:
            data = yaml.safe_load(fp)

            config = Config()

            if 'constantes' in data:
                config.constantes = ConstantesConfig(**data['constantes'])
            if 'database' in data:
                config.database = DatabaseConfig(**data['database'])
            if 'ldap' in data:
                config.ldap = LdapConfig(**data['ldap'])
            if 'etablissements' in data:
                config.etablissements = EtablissementsConfig(**data['etablissements'])

            return config
