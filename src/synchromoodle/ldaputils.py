# coding: utf-8
"""
Accès LDAP
"""
from typing import List, Dict, Union

import ldap
from collections.abc import Iterable

from synchromoodle.config import LdapConfig


def extraire_classes_ldap(classes_ldap: List[str]):
    """
    Extrait le nom des classes à partir de l'entrée issue de l'annuaire ldap.

    :param classes_ldap:  entrée issue du LDAP.
    :return
    """
    classes = []
    for classe_ldap in classes_ldap:
        split = classe_ldap.rsplit("$")
        if len(split) > 1:
            classes.append(split[1])
    return classes


class StructureLdap:
    """
    Représente une structure issu du LDAP.
    """

    def __init__(self, data):

        # TODO: Replace devrait supporter toutes les acamédies ?
        self.nom = data['ou'][0].decode("utf-8").replace("-ac-ORL._TOURS", "")
        self.type = data['ENTStructureTypeStruct'][0].decode("utf-8")
        self.code_postal = data['postalCode'][0][:2].decode("utf-8")
        self.siren = data['ENTStructureSIREN'][0].decode("utf-8")
        self.uai = data['ENTStructureUAI'][0].decode("utf-8")
        self.domaines = [x.decode('utf8') for x in data["ESCODomaines"]]


class PeopleLdap:
    """
    Représente une personne issu du LDAP.
    """

    def __init__(self, data):
        self.uid = data['uid'][0].decode('utf8')
        self.sn = data['sn'][0].decode('utf8')
        self.given_name = data['givenName'][0].decode('utf8')
        self.domaines = [x.decode('utf8') for x in data['ESCODomaines']]
        self.uai_courant = data['ESCOUAICourant'][0].decode('utf8')
        self.mail = None
        if 'mail' in data:
            self.mail = data['mail'][0].decode('utf8')

        self.is_member_of = None
        if 'isMemberOf' in data:
            self.is_member_of = [x.decode('utf8') for x in data['isMemberOf']]


class StudentLdap(PeopleLdap):
    """
    Représente un élève issu du LDAP.
    """

    def __init__(self, data):
        super().__init__(data)
        self.niveau_formation = data['ENTEleveNivFormation'][0].decode('utf8')

        self.classes = None  # type: List[str]
        self.classe = None  # type: str

        if 'ENTEleveClasses' in data:
            self.classes = extraire_classes_ldap([x.decode('utf8') for x in data['ENTEleveClasses']])
            if len(self.classes) > 1:
                self.classe = self.classes[0]


class TeacherLdap(PeopleLdap):
    """
    Représente un enseignant.
    """

    def __init__(self, data):
        super().__init__(data)
        self.structure_rattachement = data['ENTPersonStructRattach'][0].decode('utf8')

        self.profils = None
        if 'ENTPersonProfils' in data:
            self.profils = [x.decode('utf8') for x in data['ENTPersonProfils']]

        # Mise ajour des droits sur les anciens etablissement
        self.uais = None
        if 'ESCOUAI' in data:
            self.uais = [x.decode('utf8') for x in data['ESCOUAI']]


ATTRIBUTES_STRUCTURE = ['ou', 'ENTStructureSIREN', 'ENTStructureTypeStruct', 'postalCode', 'ENTStructureUAI',
                        'ESCODomaines', '+']

# Attributs retournes pour une personne
ATTRIBUTES_PEOPLE = ['objectClass', 'uid', 'sn', 'givenName', 'mail', 'ESCODomaines', 'ESCOUAICourant',
                     'ENTPersonStructRattach', 'isMemberOf', '+']

# Attributs retournes pour un eleve
ATTRIBUTES_STUDENT = ['uid', 'sn', 'givenName', 'mail', 'ENTEleveClasses', 'ENTEleveNivFormation', 'ESCODomaines',
                      'ESCOUAICourant', '+']

# Attributs retournes pour un enseignant
ATTRIBUTES_TEACHER = ['objectClass', 'uid', 'sn', 'givenName', 'mail', 'ESCOUAI', 'ESCODomaines', 'ESCOUAICourant',
                      'ENTPersonStructRattach', 'ENTPersonProfils', 'isMemberOf', '+']


class Ldap:
    """
    Couche d'accès aux données du LDAP.
    """
    config = None  # type: LdapConfig
    connection = None  # type: ldap.ldapobject.SimpleLDAPObject

    def __init__(self, config: LdapConfig):
        self.config = config
        self.connect()

    def connect(self):
        """
        Etablit la connection au LDAP.
        """
        self.connection = ldap.initialize(self.config.uri)
        self.connection.simple_bind_s(self.config.username, self.config.password)

    def disconnect(self):
        """
        Ferme la connection au LDAP.
        """
        if self.connection:
            self.connection.unbind()
            self.connection = None

    def get_structure(self, uai: str) -> StructureLdap:
        """
        Recherche de structures.
        :param uai: code établissement
        :return: L'établissement trouvé, ou None si non trouvé.
        """
        structures = self.search_structure(uai)
        return structures[0] if structures else None

    def search_structure(self, uai: str = None) -> List[StructureLdap]:
        """
        Recherche de structures.
        :param uai: code établissement
        :return: Liste des structures trouvées
        """
        ldap_filter = _get_filtre_etablissement(uai)
        search_id = self.connection.search(self.config.structuresDN, ldap.SCOPE_ONELEVEL, ldap_filter,
                                           ATTRIBUTES_STRUCTURE)
        return [StructureLdap(entry[0][1]) for entry in self._get_result(search_id)]

    def search_people(self, since_timestamp, **filters) -> List[PeopleLdap]:
        """
        Recherche de personnes.
        :param since_timestamp: Timestamp
        :param filters: Filtres à appliquer
        :return: Liste des personnes
        """
        ldap_filter = _get_filtre_personnes(since_timestamp, **filters)
        search_id = self.connection.search(self.config.personnesDN, ldap.SCOPE_ONELEVEL, ldap_filter, ATTRIBUTES_PEOPLE)
        return [PeopleLdap(entry[0][1]) for entry in self._get_result(search_id)]

    def search_student(self, since_timestamp, uai) -> List[StudentLdap]:
        """
        Recherche d'étudiants.
        :param since_timestamp: Timestamp
        :param uai: code établissement
        :return: Liste des étudiants correspondant
        """
        ldap_filter = _get_filtre_eleves(since_timestamp, uai)
        search_id = self.connection.search(self.config.personnesDN, ldap.SCOPE_ONELEVEL, ldap_filter,
                                           ATTRIBUTES_STUDENT)
        return [StudentLdap(entry[0][1]) for entry in self._get_result(search_id)]

    def search_teacher(self, since_timestamp=None, uai=None, tous=False) -> List[TeacherLdap]:
        """
        Recherche d'enseignants.
        :param since_timestamp: Timestamp
        :param uai: code etablissement
        :param tous: Si True, retourne également le personnel non enseignant
        :return: Liste des enseignants
        """
        ldap_filter = get_filtre_enseignants(since_timestamp, uai, tous)
        search_id = self.connection.search(self.config.personnesDN, ldap.SCOPE_ONELEVEL, ldap_filter,
                                           ATTRIBUTES_TEACHER)
        return [TeacherLdap(entry[0][1]) for entry in self._get_result(search_id)]

    def get_domaines_etabs(self) -> Dict[str, List[str]]:
        """
        Obtient la liste des "ESCOUAICourant : Domaine" des établissements
        :return: Dictionnaire uai/list de domaines
        """
        ldap_structures = self.search_structure()

        etabs_ldap = {}

        for ldap_structure in ldap_structures:
            etabs_ldap[ldap_structure.uai] = ldap_structure.domaines
        return etabs_ldap

    def _get_result(self, result_id) -> list:
        """
        Retourne le résultat d'une recherche.
        :param result_id: identifiant de la recherche
        :return: résultats
        """
        result_entries = []
        result_data = [0]
        while result_data:
            result_type, result_data = self.connection.result(result_id, 0)
            if result_data and result_type == ldap.RES_SEARCH_ENTRY:
                result_entries.append(result_data)
        return result_entries


def _get_filtre_eleves(since_timestamp: str = None, uai: str = None) -> str:
    """
    Construit le filtre pour récupérer les élèves au sein du LDAP

    :param since_timestamp:
    :param uai: code établissement
    :return: Le filtre
    """
    filtre = "(&(objectClass=ENTEleve)"
    if uai:
        filtre += "(ESCOUAI={uai})".format(uai=uai)
    if since_timestamp:
        filtre += "(modifyTimeStamp>={since_timestamp})".format(since_timestamp=since_timestamp)
    filtre = filtre + ")"
    return filtre


def get_filtre_enseignants(since_timestamp=None, uai=None, tous=False) -> str:
    """
    Construit le filtre pour récupérer les enseignants au sein du LDAP.

    :param since_timestamp:
    :param uai: code établissement
    :param tous:
    :return: Le filtre
    """
    filtre = "(&"
    if tous:
        filtre += "(|(objectClass=ENTDirecteur)" \
                  "(objectClass=ENTAuxEnseignant)" \
                  "(objectClass=ENTAuxNonEnsEtab)" \
                  "(objectClass=ENTAuxNonEnsCollLoc)" \
                  ")"
    else:
        filtre += "(objectClass=ENTAuxEnseignant)"

    filtre += "(!(uid=ADM00000))"

    if uai:
        filtre += "(ESCOUAI={uai})".format(uai=uai)
    if since_timestamp:
        filtre += "(modifyTimeStamp>={since_timestamp})".format(since_timestamp=since_timestamp)

    filtre = filtre + ")"

    return filtre


def _get_filtre_personnes(since_timestamp=None, **filters: Union[str, List[str]]) -> str:
    """
    Construit le filtre pour récupérer les personnes
    :param modify_time_stamp:
    :param filters: Filtres spécifiques à appliquer
    :return: Le filtre
    """
    filtre = "(&(|" \
             + "(objectClass=ENTPerson)" \
             + ")" \
             + "(!(uid=ADM00000))"
    filtre = filtre + "(|"
    for k, v in filters.items():
        if not isinstance(v, Iterable) or isinstance(v, str):
            v = [v]
        for item in v:
            attribute_filtre = "(%s=%s)" % (k, item)
            filtre = filtre + attribute_filtre
    filtre = filtre + ")"
    if since_timestamp:
        filtre = filtre + "(modifyTimeStamp>=%s)"
        filtre = filtre % since_timestamp
    filtre = filtre + ")"
    return filtre


def _get_filtre_etablissement(uai=None):
    """Construit le filtre pour les établissements."""
    filtre = "(&(ObjectClass=ENTEtablissement)" \
             "(!(ENTStructureSiren=0000000000000A))"

    if uai:
        filtre += "(ENTStructureUAI={uai})".format(uai=uai)

    filtre += ")"

    return filtre
