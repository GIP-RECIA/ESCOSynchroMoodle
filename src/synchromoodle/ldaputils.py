# coding: utf-8
"""
Accès LDAP
"""
import datetime
from collections.abc import Iterable
from typing import List, Dict, Union

from ldap3 import Server, Connection, LEVEL

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
    Représente une structure issue du LDAP.
    """

    def __init__(self, data):
        # TODO: Replace devrait supporter toutes les acamédies ?
        self.nom = data.ou.value.replace("-ac-ORL._TOURS", "")
        self.type = data.ENTStructureTypeStruct.value
        self.code_postal = data.postalCode.value[:2]
        self.siren = data.ENTStructureSIREN.value
        self.uai = data.ENTStructureUAI.value
        self.domaine = data.ESCODomaines.value
        self.domaines = data.ESCODomaines.values


class PersonneLdap:
    """
    Représente une personne issue du LDAP.
    """

    def __init__(self, data):
        self.uid = data.uid.value
        self.sn = data.sn.value
        self.given_name = data.givenName.value
        self.domaine = data.ESCODomaines.value
        self.domaines = data.ESCODomaines.values
        self.uai_courant = data.ESCOUAICourant.value
        self.mail = None
        if 'mail' in data:
            self.mail = data.mail.value

        self.is_member_of = None
        if 'isMemberOf' in data:
            self.is_member_of = data.isMemberOf.values


class EleveLdap(PersonneLdap):
    """
    Représente un élève issu du LDAP.
    """

    def __init__(self, data):
        super().__init__(data)
        self.niveau_formation = data.ENTEleveNivFormation.value

        self.classes = None  # type: List[str]
        self.classe = None  # type: str

        if 'ENTEleveClasses' in data:
            self.classes = extraire_classes_ldap(data.ENTEleveClasses.values)
            if len(self.classes) > 0:
                self.classe = self.classes[0]


class EnseignantLdap(PersonneLdap):
    """
    Représente un enseignant issu du LDAP.
    """

    def __init__(self, data):
        super().__init__(data)
        self.structure_rattachement = data.ENTPersonStructRattach.value

        self.profils = None
        if 'ENTPersonProfils' in data:
            self.profils = data.ENTPersonProfils.values

        self.uais = None
        if 'ESCOUAI' in data:
            self.uais = data.ESCOUAI.values


class Ldap:
    """
    Couche d'accès aux données du LDAP.
    """
    config = None  # type: LdapConfig
    connection = None  # type: Connection

    def __init__(self, config: LdapConfig):
        self.config = config

    def connect(self):
        """
        Etablit la connection au LDAP.
        """
        server = Server(host=self.config.uri)
        self.connection = Connection(server,
                                     user=self.config.username,
                                     password=self.config.password,
                                     auto_bind=True,
                                     raise_exceptions=True)

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
        self.connection.search(self.config.structuresDN, ldap_filter,
                               search_scope=LEVEL, attributes=
                               ['ou', 'ENTStructureSIREN', 'ENTStructureTypeStruct', 'postalCode', 'ENTStructureUAI',
                                'ESCODomaines', '+'])
        return [StructureLdap(entry) for entry in self.connection.entries]

    def search_personne(self, since_timestamp: datetime.datetime = None, **filters) -> List[PersonneLdap]:
        """
        Recherche de personnes.
        :param since_timestamp: datetime.datetime
        :param filters: Filtres à appliquer
        :return: Liste des personnes
        """
        ldap_filter = _get_filtre_personnes(since_timestamp, **filters)
        self.connection.search(self.config.personnesDN, ldap_filter,
                               search_scope=LEVEL, attributes=
                               ['objectClass', 'uid', 'sn', 'givenName', 'mail', 'ESCODomaines', 'ESCOUAICourant',
                                'ENTPersonStructRattach', 'isMemberOf', '+'])
        return [PersonneLdap(entry) for entry in self.connection.entries]

    def search_eleve(self, since_timestamp: datetime.datetime = None, uai: str = None) -> List[EleveLdap]:
        """
        Recherche d'étudiants.
        :param since_timestamp: datetime.datetime
        :param uai: code établissement
        :return: Liste des étudiants correspondant
        """
        ldap_filter = _get_filtre_eleves(since_timestamp, uai)
        self.connection.search(self.config.personnesDN, ldap_filter,
                               search_scope=LEVEL, attributes=
                               ['uid', 'sn', 'givenName', 'mail', 'ENTEleveClasses', 'ENTEleveNivFormation',
                                'ESCODomaines', 'ESCOUAICourant', '+'])
        return [EleveLdap(entry) for entry in self.connection.entries]

    def search_enseignant(self, since_timestamp: datetime.datetime = None, uai=None, tous=False) -> List[
        EnseignantLdap]:
        """
        Recherche d'enseignants.
        :param since_timestamp: datetime.datetime
        :param uai: code etablissement
        :param tous: Si True, retourne également le personnel non enseignant
        :return: Liste des enseignants
        """
        ldap_filter = get_filtre_enseignants(since_timestamp, uai, tous)
        self.connection.search(self.config.personnesDN,
                               ldap_filter, LEVEL, attributes=
                               ['objectClass', 'uid', 'sn', 'givenName', 'mail', 'ESCOUAI', 'ESCODomaines',
                                'ESCOUAICourant', 'ENTPersonStructRattach', 'ENTPersonProfils', 'isMemberOf', '+'])
        return [EnseignantLdap(entry) for entry in self.connection.entries]

    def get_domaines_etabs(self) -> Dict[str, List[str]]:
        """
        Obtient la liste des "ESCOUAICourant : Domaine" des établissements
        :return: Dictionnaire uai/list de domaines
        """
        structures = self.search_structure()

        etabs_ldap = {}

        for structure in structures:
            etabs_ldap[structure.uai] = structure.domaines
        return etabs_ldap


def _get_filtre_eleves(since_timestamp: datetime.datetime = None, uai: str = None) -> str:
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
        filtre += "(modifyTimeStamp>={since_timestamp})".format(since_timestamp=since_timestamp.isoformat())
    filtre = filtre + ")"
    return filtre


def get_filtre_enseignants(since_timestamp: datetime.datetime = None, uai=None, tous=False) -> str:
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
        filtre += "(modifyTimeStamp>={since_timestamp})".format(since_timestamp=since_timestamp.isoformat())

    filtre = filtre + ")"

    return filtre


def _get_filtre_personnes(since_timestamp: datetime.datetime = None, **filters: Union[str, List[str]]) -> str:
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
    if filters:
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
        filtre = filtre % since_timestamp.isoformat()
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
