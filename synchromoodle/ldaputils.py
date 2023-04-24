# coding: utf-8
"""
Accès LDAP
"""
import datetime
from collections.abc import Iterable
from typing import List, Dict, Union

from ldap3 import Server, Connection, LEVEL

from synchromoodle.config import LdapConfig

class ClasseLdap:
    def __init__(self, etab_dn: str, classe: str):
        self.etab_dn = etab_dn
        self.classe = classe

def extraire_classes_ldap(classes_ldap: List[str]):
    """
    Extrait le nom des classes à partir de l'entrée issue de l'annuaire ldap.

    :param classes_ldap:  entrée issue du LDAP.
    :return
    """
    classes = []
    for classe_ldap in classes_ldap:
        split = classe_ldap.split("$")
        if len(split) > 1:
            classes.append(ClasseLdap(split[0], split[-1]))
    return classes


def ldap_escape(ldapstr: str) -> str:
    """
    Echappe les caractères specifiques pour les filtres LDAP
    :param ldapstr:
    :return:
    """
    if ldapstr is None:
        return ""
    return ldapstr\
        .replace("\\", "\\5C")\
        .replace("*", "\\2A")\
        .replace("(", "\\28")\
        .replace(")", "\\29")\
        .replace("\000", "\\00")


class StructureLdap:
    """
    Représente une structure issue du LDAP.
    """

    def __init__(self, data):
        self.nom = data.ou.value.split("-ac")[0]
        self.type = data.ENTStructureTypeStruct.value
        self.code_postal = data.postalCode.value[:2]
        self.siren = data.ENTStructureSIREN.value
        self.uai = data.ENTStructureUAI.value
        self.domaine = data.ESCODomaines.value
        self.domaines = data.ESCODomaines.values
        self.dn = data.entry_dn
        self.jointure = data.ENTStructureJointure.value

    def __str__(self):
        return "uai=%s, siren=%s, nom=%s" % (self.uai, self.siren, self.nom)

    def __repr__(self):
        return "[%s] %s" % (self.__class__.__name__, str(self))


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
        self.classes = None  # type: List[ClasseLdap]
        if 'mail' in data:
            self.mail = data.mail.value

        self.is_member_of = None
        if 'isMemberOf' in data:
            self.is_member_of = data.isMemberOf.values

    def __str__(self):
        return "uid=%s, given_name=%s, sn=%s" % (self.uid, self.given_name, self.sn)

    def __repr__(self):
        return "[%s] %s" % (self.__class__.__name__, str(self))


class EleveLdap(PersonneLdap):
    """
    Représente un élève issu du LDAP.
    """

    def __init__(self, data):
        super().__init__(data)
        self.niveau_formation = data.ENTEleveNivFormation.value

        self.classe = None  # type: ClasseLdap

        if 'ENTEleveClasses' in data:
            self.classes = extraire_classes_ldap(data.ENTEleveClasses.values)
            if self.classes:
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

        if 'ENTAuxEnsClasses' in data:
            self.classes = extraire_classes_ldap(data.ENTAuxEnsClasses.values)



class PersonnelDirection(PersonneLdap):
    """
    Représente un personnel de direction issu du LDAP.
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

    def search_dane(self, uai: str) -> StructureLdap:
        """
        Recherche une structure dane
        :param uai: code établissement
        :return: L'établissement trouvé, ou None si non trouvé.
        """
        ldap_filter = _get_filtre_dane(uai)
        self.connection.search(self.config.structuresDN, ldap_filter,
                               search_scope=LEVEL, attributes=
                               ['ou', 'ENTStructureSIREN', 'ENTStructureTypeStruct', 'ENTStructureJointure',
                                'postalCode', 'ENTStructureUAI', 'ESCODomaines', '+'])
        dane = [StructureLdap(entry) for entry in self.connection.entries]
        return dane[0] if dane else None

    def search_structure(self, uai: str = None) -> List[StructureLdap]:
        """
        Recherche de structures.
        :param uai: code établissement
        :return: Liste des structures trouvées
        """
        ldap_filter = _get_filtre_etablissement(uai)
        self.connection.search(self.config.structuresDN, ldap_filter,
                               search_scope=LEVEL, attributes=
                               ['ou', 'ENTStructureSIREN', 'ENTStructureTypeStruct', 'ENTStructureJointure',
                                'postalCode', 'ENTStructureUAI', 'ESCODomaines', '+'])
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

    def search_eleve_uid(self, since_timestamp: datetime.datetime = None, uai: str = None) -> List[str]:
        """
        Recherche d'uid d'étudiants.
        :param since_timestamp: datetime.datetime
        :param uai: code établissement
        :return: Liste des uid d'étudiants correspondant
        """
        ldap_filter = _get_filtre_eleves(since_timestamp, uai)
        self.connection.search(self.config.personnesDN, ldap_filter,
                               search_scope=LEVEL, attributes=
                               ['uid'])
        return [entry.uid.lower() for entry in self.connection.entries]

    def search_eleves_in_classe(self, classe: str, uai):
        """
        Recherche les élèves dans une classe.
        :param classe:
        :param uai:
        :return:
        """
        ldap_filter = '(&(ENTEleveClasses=*$%s)(ESCOUAI=%s))' % (ldap_escape(classe), ldap_escape(uai))
        self.connection.search(self.config.personnesDN, ldap_filter,
                               search_scope=LEVEL, attributes=
                               ['uid', 'sn', 'givenName', 'mail', 'ENTEleveClasses', 'ENTEleveNivFormation',
                                'ESCODomaines', 'ESCOUAICourant', '+'])
        return [EleveLdap(entry) for entry in self.connection.entries]

    def search_eleves_in_niveau(self, niveau: str, uai):
        """
        Recherche les élèves dans une niveau.
        :param niveau: Le niveau de formation recherché
        :param uai: L'établissement dans lequel on effectue la recherche
        :return: La liste des élèves trouvés
        """
        ldap_filter = '(&(objectClass=ENTEleve)(ENTEleveNivFormation=%s)(ESCOUAI=%s))' % (ldap_escape(niveau), ldap_escape(uai))
        self.connection.search(self.config.personnesDN, ldap_filter,
                               search_scope=LEVEL, attributes=
                               ['uid', 'sn', 'givenName', 'mail', 'ENTEleveClasses', 'ENTEleveNivFormation',
                                'ESCODomaines', 'ESCOUAICourant', '+'])
        return [EleveLdap(entry) for entry in self.connection.entries]

    def search_enseignant(self, since_timestamp: datetime.datetime = None, uai=None, tous=False) \
            -> List[EnseignantLdap]:
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
                                'ESCOUAICourant', 'ENTPersonStructRattach', 'ENTPersonProfils', 'isMemberOf', '+',
                                'ENTAuxEnsClasses'])
        return [EnseignantLdap(entry) for entry in self.connection.entries]

    def search_enseignant_uid(self, since_timestamp: datetime.datetime = None, uai=None, tous=False) \
            -> List[str]:
        """
        Recherche d'uid d'enseignants.
        :param since_timestamp: datetime.datetime
        :param uai: code etablissement
        :param tous: Si True, retourne également le personnel non enseignant
        :return: Liste des uid d'enseignants
        """
        ldap_filter = get_filtre_enseignants(since_timestamp, uai, tous)
        self.connection.search(self.config.personnesDN,
                               ldap_filter, LEVEL, attributes=
                               ['uid'])
        return [entry.uid.lower() for entry in self.connection.entries]

    def search_personnel_direction(self, since_timestamp: datetime.datetime = None, uai=None) \
            -> List[PersonnelDirection]:
        """
        Recherche du personnel de direction.
        :param since_timestamp: datetime.datetime
        :param uai: code etablissement
        :return: Liste du personnel de direction
        """
        ldap_filter = get_filtre_personnel_direction(since_timestamp, uai)
        self.connection.search(self.config.personnesDN,
                               ldap_filter, LEVEL, attributes=
                               ['objectClass', 'uid', 'sn', 'givenName', 'mail', 'ESCOUAI', 'ESCODomaines',
                                'ESCOUAICourant', 'ENTPersonStructRattach', 'ENTPersonProfils', 'isMemberOf', '+'])
        return [PersonnelDirection(entry) for entry in self.connection.entries]

    def search_personnel_direction_uid(self, since_timestamp: datetime.datetime = None, uai=None) \
            -> List[str]:
        """
        Recherche des uid du personnel de direction.
        :param since_timestamp: datetime.datetime
        :param uai: code etablissement
        :return: Liste des uid du personnel de direction
        """
        ldap_filter = get_filtre_personnel_direction(since_timestamp, uai)
        self.connection.search(self.config.personnesDN,
                               ldap_filter, LEVEL, attributes=
                               ['uid'])
        return [entry.uid.lower() for entry in self.connection.entries]

    def search_enseignants_in_classe(self, classe: str, uai):
        """
        Recherche les enseignants dans une classe.
        :param classe: La classe recherchée
        :param uai: L'établissement dans lequel on effectue la recherche
        :return: La liste des enseignants trouvés
        """
        ldap_filter = '(&(objectClass=ENTAuxEnseignant)(ENTAuxEnsClasses=*$%s)(ESCOUAI=%s))' % (ldap_escape(classe), ldap_escape(uai))
        self.connection.search(self.config.personnesDN,
                               ldap_filter, LEVEL, attributes=
                               ['objectClass', 'uid', 'sn', 'givenName', 'mail', 'ESCOUAI', 'ESCODomaines',
                                'ESCOUAICourant', 'ENTPersonStructRattach', 'ENTPersonProfils', 'isMemberOf', '+',
                                'ENTAuxEnsClasses'])
        return [EnseignantLdap(entry) for entry in self.connection.entries]

    def search_enseignants_in_etab(self, uai: str):
        """
        Recherche les enseignants dans un établissement.
        :param uai: L'établissement recherché
        :return: La liste des enseignants trouvés
        """
        ldap_filter = '(&(objectClass=ENTAuxEnseignant)(ESCOUAI=%s))' % ldap_escape(uai)
        self.connection.search(self.config.personnesDN,
                               ldap_filter, LEVEL, attributes=
                               ['objectClass', 'uid', 'sn', 'givenName', 'mail', 'ESCOUAI', 'ESCODomaines',
                                'ESCOUAICourant', 'ENTPersonStructRattach', 'ENTPersonProfils', 'isMemberOf', '+',
                                'ENTAuxEnsClasses'])
        return [EnseignantLdap(entry) for entry in self.connection.entries]

    def search_enseignants_in_niveau(self, niveau: str, uai: str, classe_to_niv_formation):
        """
        Recherche les enseignants dans un niveau de formation
        :param niveau: Le niveau de formation recherché
        :param uai: L'identifiant de l'établissement dans lequel on effectue la recherche
        :param classe_to_niv_formation:
        :return: La liste des enseignants trouvés
        """
        all_enseignants = self.search_enseignants_in_etab(uai)
        enseignants_in_niveau = []
        for enseignant_ldap in all_enseignants:
            for classe in enseignant_ldap.classes:
                #Il est possible qu'on ne trouve pas la classe dans le dictionnaire
                #Dans ce cas l'enseignant sera traité dans cette cohorte sur le
                #prochain établissement
                if classe.classe in classe_to_niv_formation.keys():
                    if classe_to_niv_formation[classe.classe] == niveau:
                        if enseignant_ldap not in enseignants_in_niveau:
                            enseignants_in_niveau.append(enseignant_ldap)
        return enseignants_in_niveau

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
        filtre += "(ESCOUAI={uai})".format(uai=ldap_escape(uai))
    if since_timestamp:
        filtre += "(modifyTimeStamp>={since_timestamp})" \
            .format(since_timestamp=since_timestamp.strftime("%Y%m%d%H%M%SZ"))
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
        filtre += "(|(objectClass=ENTAuxEnseignant)" \
                  "(objectClass=ENTAuxNonEnsEtab)" \
                  "(objectClass=ENTAuxNonEnsCollLoc)" \
                  ")"
    else:
        filtre += "(objectClass=ENTAuxEnseignant)"

    filtre += "(!(uid=ADM00000))"

    if uai:
        filtre += "(ESCOUAI={uai})".format(uai=ldap_escape(uai))
    if since_timestamp:
        filtre += "(modifyTimeStamp>={since_timestamp})" \
            .format(since_timestamp=since_timestamp.strftime("%Y%m%d%H%M%SZ"))

    filtre = filtre + ")"

    return filtre

def get_filtre_personnel_direction(since_timestamp: datetime.datetime = None, uai=None) -> str:
    """
    Construit le filtre pour récupérer les utilisateurs pêrsonne de direction au sein du LDAP.

    :param since_timestamp:
    :param uai: code établissement
    :return: Le filtre
    """
    filtre = "(&(|(objectClass=ENTAuxEnseignant)" \
        "(objectClass=ENTAuxNonEnsEtab)" \
        "(objectClass=ENTAuxNonEnsCollLoc)" \
        ")(!(uid=ADM00000))" \
        "(ENTPersonProfils=National_DIR)"

    if uai:
        filtre += "(ESCOUAI={uai})".format(uai=ldap_escape(uai))
    if since_timestamp:
        filtre += "(modifyTimeStamp>={since_timestamp})" \
            .format(since_timestamp=since_timestamp.strftime("%Y%m%d%H%M%SZ"))

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
                attribute_filtre = "(%s=%s)" % (ldap_escape(k), ldap_escape(item))
                filtre = filtre + attribute_filtre
        filtre = filtre + ")"
    if since_timestamp:
        filtre = filtre + "(modifyTimeStamp>=%s)"
        filtre = filtre % since_timestamp.strftime("%Y%m%d%H%M%SZ")
    filtre = filtre + ")"
    return filtre


def _get_filtre_etablissement(uai=None):
    """Construit le filtre pour les établissements."""
    filtre = "(&(ObjectClass=ENTEtablissement)" \
             "(!(ENTStructureSiren=0000000000000A))"

    if uai:
        filtre += "(ENTStructureUAI={uai})".format(uai=ldap_escape(uai))

    filtre += ")"
    return filtre


def _get_filtre_dane(uai=None):
    """Construit le filtre pour la dane."""
    filtre = "(&(ObjectClass=ENTServAc)" \
             "(!(ENTStructureSiren=0000000000000A))"

    if uai:
        filtre += "(ENTStructureUAI={uai})".format(uai=ldap_escape(uai))

    filtre += ")"
    return filtre
