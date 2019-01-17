# coding: utf-8

###############################################################################
# IMPORTS
###############################################################################
import ldap

###############################################################################
# CONSTANTES
###############################################################################
# Attributs retournes pour une structure
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


###########################################################
# Fonction permettant d'etablir une connexion a un LDAP 
###########################################################
def connect_ldap(ldap_server, ldap_username, ldap_password):
    l = ldap.initialize(ldap_server)
    l.protocol_version = ldap.VERSION3
    l.simple_bind_s(ldap_username, ldap_password)
    return l


###########################################################
# Fonction permettant de formater une date au format LDAP
# Format: AAAAMMJJHHMMSS + la lettre Z
###########################################################
def format_date(date_to_format):
    return (date_to_format.strftime('%Y%m%d%H%M%S') + 'Z')


###########################################################
# Fonction permettant d'obtenir le filtre pour recuperer 
# les eleves au sein du LDAP
###########################################################
def get_filtre_eleves(modify_time_stamp, uai_etab):
    filtre = "(&(objectClass=ENTEleve)(ESCOUAI=%s)"
    filtre = filtre % (uai_etab)
    if modify_time_stamp:
        filtre = filtre + "(modifyTimeStamp>=%s)"
        filtre = filtre % (modify_time_stamp)
    filtre = filtre + ")"
    return filtre


###########################################################
# Fonction permettant d'obtenir le filtre pour recuperer 
# les enseignants au sein du LDAP
###########################################################
def get_filtre_enseignants(modify_time_stamp, uai_etab):
    filtre = "(&(|" \
             + "(objectClass=ENTDirecteur)" \
             + "(objectClass=ENTAuxEnseignant)" \
             + "(objectClass=ENTAuxNonEnsEtab)" \
             + "(objectClass=ENTAuxNonEnsCollLoc)" \
             + ")" \
             + "(!(uid=ADM00000))" \
             + "(ESCOUAI=%s)"
    filtre = filtre % (uai_etab)
    if modify_time_stamp:
        filtre = filtre + "(modifyTimeStamp>=%s)"
        filtre = filtre % (modify_time_stamp)
    filtre = filtre + ")"
    return filtre


def get_filtre_enseignants_etablissement(modify_time_stamp, uai_etab):
    filtre = "(&(objectClass=ENTAuxEnseignant)(!(uid=ADM00000))(ESCOUAI=%s)"
    filtre = filtre % (uai_etab)
    if modify_time_stamp:
        filtre = filtre + "(modifyTimeStamp>=%s)"
        filtre = filtre % (modify_time_stamp)
    filtre = filtre + ")"
    return filtre


###########################################################
# Fonction permettant d'obtenir le filtre pour recuperer 
# les personnes au sein du LDAP
###########################################################
def get_filtre_personnes(modify_time_stamp, attribute, attribute_values):
    filtre = "(&(|" \
             + "(objectClass=ENTPerson)" \
             + ")" \
             + "(!(uid=ADM00000))"
    filtre = filtre + "(|"
    for attribute_value in attribute_values:
        attribute_filtre = "(%s=%s)" % (attribute, attribute_value)
        filtre = filtre + attribute_filtre
    filtre = filtre + ")"
    if modify_time_stamp:
        filtre = filtre + "(modifyTimeStamp>=%s)"
        filtre = filtre % (modify_time_stamp)
    filtre = filtre + ")"
    return filtre


###########################################################
# Fonction permettant d'obtenir le filtre pour recuperer 
# un etablissement au sein du LDAP.
###########################################################
def get_filtre_etablissement(uai_etab):
    filtre = "(&(ObjectClass=ENTEtablissement)" \
             + "(!(ENTStructureSiren=0000000000000A))" \
             + "(ENTStructureUAI=%s))"
    filtre = filtre % (uai_etab)
    return filtre


###########################################################
# Fonction permettant de recuperer le resultat d'une
# recherche au sein d'un tableau.
###########################################################
def ldap_retrieve_all_entries(ldap_connection, result_id):
    result_entries = []
    result_data = [0]
    while result_data:
        result_type, result_data = ldap_connection.result(result_id, 0)
        if result_data and result_type == ldap.RES_SEARCH_ENTRY:
            result_entries.append(result_data)
    return result_entries


###########################################################
# Fonction permettant de faire une recherche LDAP.
###########################################################
def ldap_search(ldap_connection, dn, scope, filter, attributes):
    return ldap_connection.search(dn, scope, filter, attributes)


###########################################################
# Fonction permettant de faire une recherche LDAP sur 
# les structures.
###########################################################
def ldap_search_structure(ldap_connection, dn, filter):
    return ldap_search(ldap_connection, dn, ldap.SCOPE_ONELEVEL, filter, ATTRIBUTES_STRUCTURE)


###########################################################
# Fonction permettant de faire une recherche LDAP sur 
# les personnes.
###########################################################
def ldap_search_people(ldap_connection, dn, filter):
    return ldap_search(ldap_connection, dn, ldap.SCOPE_ONELEVEL, filter, ATTRIBUTES_PEOPLE)


###########################################################
# Fonction permettant de faire une recherche LDAP sur 
# les eleves.
###########################################################
def ldap_search_student(ldap_connection, dn, filter):
    return ldap_search(ldap_connection, dn, ldap.SCOPE_ONELEVEL, filter, ATTRIBUTES_STUDENT)


###########################################################
# Fonction permettant de faire une recherche LDAP sur 
# les enseignants.
###########################################################
def ldap_search_teacher(ldap_connection, dn, filter):
    return ldap_search(ldap_connection, dn, ldap.SCOPE_ONELEVEL, filter, ATTRIBUTES_TEACHER)


###########################################################
# Fonction pour récupérer la liste des
# "ESCOUAICourant : Domaine" des établissements
###########################################################
def get_domaines_etabs(ldap, structuresDN):
    filtre = "(&(ObjectClass=ENTEtablissement)(!(ENTStructureSiren=0000000000000A)))"
    ldap_result_id = ldap_search_structure(ldap, structuresDN, filtre)

    # Recuperation du resultat de la recherche
    result_set = ldap_retrieve_all_entries(ldap, ldap_result_id)

    etabs_ldap = {}
    # Pour chaque établissement, on récupère l'UAI et le Domaine
    for ldap_entry in result_set:
        ldap_entry_infos = ldap_entry[0][1]
        etab_domaines = ldap_entry_infos["ESCODomaines"]
        etab_uai = ldap_entry_infos['ENTStructureUAI'][0]
        # On ajoute les données dans la liste
        etabs_ldap[etab_uai] = etab_domaines
    return etabs_ldap
