#!/usr/bin/env python2
# coding: utf-8

# System imports
import datetime
import ldap
import logging
import MySQLdb
import re
import sys
import pdb

logging.basicConfig(format='%(levelname)s:%(message)s', stream=sys.stdout, level=logging.DEBUG)


# Domaine par défaut
DEFAULT_DOMAIN = "lycees.netocentre.fr"

# Attributs retournés pour une structure
ATTRIBUTES_STRUCTURE = [ 'ou','ENTStructureSIREN','ENTStructureTypeStruct','ENTStructureUAI',"ESCODomaines" ]

# Attributs retournés pour un eleve
ATTRIBUTES_STUDENT = [ 'uid','ESCODomaines','ESCOUAICourant' ]

# Infos pour la connexion et l'acces aux donnees sur la BD moodle
#nomBD       = "test"
#user        = "root"
#password    = "admin"
#host        = "localhost"
nomBD       = "moodle"
user        = "moodle"
password    = "M2pAMAvCRRL"
host        = "chouette.giprecia.net"
port        = "3307"
entete      = "mdl_"

# Infos pour la connexion et l"acces aux donnees sur le serveur LDAP
ldapServer      = "pigeon.giprecia.net"
ldapUsername    = "cn=moodle,ou=administrateurs,dc=esco-centre,dc=fr"
ldapPassword    = "vxcG5H9ro5"

baseDN          = ",dc=esco-centre,dc=fr"
structuresDN    = "ou=structures"  + baseDN
personnesDN     = "ou=people" + baseDN
adminDN         = "ou=administrateurs" + baseDN

# Listes des établissements à rattraper
listeEtabs_academique = ['0450822X', '0410031L', '0371122U', '0450066C', '0451483T', '0410593X', '0410030K', '0370001A', '0360003H', '0370040T', '0370036N', '0451304Y', '0450051L', '0180008L', '0360011S', '0280657M', '0280036M', '0450062Y', '0280021W', '0360024F', '0410959V', '0371417P', '0280864M', '0450042B', '0370009J', '0360002G', '0370039S', '0180006J', '0410017W', '0450790P', '0451442Y', '0281047L', '0450064A', '0280925D', '0180007K', '0180042Y', '0371418R', '0360008N', '0180024D', '0180026F', '0280044W', '0360009P', '0281077U', '0410832G', '0180823X', '0180777X', '0360658V', '0180036S', '0180010N', '0180005H', '0180009M', '0280009H', '0280015P', '0280957N', '0280022X', '0360026H', '0360019A', '0360005K', '0371211R', '0370037P', '0370038R', '0370053G', '0370054H', '0371100V', '0410002E', '0410899E', '0410718H', '0410036S', '0451484U', '0451526P', '0450750W', '0450050K', '0450782F', '0451067R', '0280659P', '0360050J', '0451104F', '0180025E', '0180035R', '0280007F', '0280019U', '0280700J', '0281021H', '0360043B', '0370016S', '0370032J', '0370035M', '0370771M', '0370888P', '0371099U', '0371123V', '0371258S', '0410001D', '0450029M', '0450040Z', '0450043C', '0450049J', '0450786K', '0451037H', '0451462V', '0410860M', '0371159J', '0371204H', '0371316E', '0370011L', '0370991B', '0370041U', '0377777U', '0370006F', '0370015R', '0370768J', '0370791J', '0370792K', '0370799T', '0370886M', '0370887N', '0370994E', '0371101W', '0371158H', '0371191U', '0371248F', '0371391L', '0371397T', '0371403Z', '0371124W', '0370995F', '0370007G', '0370010K', '0371098T', '0370013N', '0371378X', '0370993D', '0370022Y', '0370034L', '0370766G', '0370044X', '0370045Y', '0370769K', '0370886M', '0370884K', '0371189S', '0370024A', '0370023Z', '0370026C', '0370051E', '0370071B', '0370764E', '0370765F', '0370767H', '0370793L', '0370885L', '0370033K', '0371126Y', '0371192V', '0371209N', '0371210P']
#listeEtabs_academique = ['0450822X']
listeEtabs_agricole = ['0410018X', '0180585N', '0280706R', '0370878D', '0450094H', '0451535Z', '0450027K', '0410629L', '0370781Y', '0360017Y', '0370794M', '0410626H']
#listeEtabs_agricole = ['0410018X']
listeEtabs_cfa = ['0180755y', '0180847y', '0180939y', '0180865t', '0180877f', '0180886r', '0180924g', '0280738a', '0280904f', '0281041e', '0281155d', '0281164n', '0333333y', '0360548a', '0360766m', '0360777z', '0360709a', '0370811f', '0370825w', '0370983t', '0370984u', '0371270e', '0371436k', '0371514v', '0371515w', '0371587z', '0371588a', '0371686g', '0371710h', '0371711j', '0371723x', '0410590u', '0410592w', '0410892y', '0410955r', '0411045n', '0411059d', '0411064j', '0411065k', '0450805f', '0450807h', '0450808j', '0450809k', '0450810l', '0450810q', '0451418X', '0451463w', '0451565g', '0451583b', '0451602x', '0451691u', '0451693w', '0451694x', '0451715v']
#listeEtabs_cfa = ['0180755y']

def rattrapage_domaines():
    
    logging.info('============================================')
    logging.info('========== Rattrapage des domaines =========')
    # Connexion a la BD Moodle
    logging.info("|_Connexion à la BD Moodle.")
    connection, mark = connect_db( host, user, password, nomBD, port, 'utf8')

    # Récupération/Création de l'id du champ "Domaine" de la BD Moodle
    logging.info("|_Récupération/Création de l'id du champ \"Domaine\" de la BD Moodle.")
    id_field_domaine = create_field_domaine(mark)
    
    # Connexion au LDAP
    logging.info("|_Connexion au LDAP.")
    ldap = connect_ldap( ldapServer, ldapUsername, ldapPassword )

    # Récupération de la liste UAI-Domaine des établissements
    logging.info("|_Récupération de la liste UAI-Domaine des établissements.")
    map_etab_domaine = get_domaine_etab(ldap)

    logging.info("|_Rattrapage des domaines par type de structure.")

    # Ajout du champ domaine par type de structure
    logging.info("  |_Ajout du champ Domaine pour les établissements de l'académie.")
    count, absents, comptes = integration_domaines_etabs(mark, ldap, id_field_domaine, map_etab_domaine, listeEtabs_academique)
    count_global = count
    count_abs = absents
    comptes_ldap = comptes
    logging.info("  |_%s/%s utilisateur(s) mis à jour pour les établissements de l'académie, %s non trouvé(s)." % (count,comptes_ldap,absents))

    logging.info("  |_Ajout du champ Domaine pour les lycées agricoles.")
    count, absents, comptes = integration_domaines_etabs(mark, ldap, id_field_domaine, map_etab_domaine, listeEtabs_agricole)
    count_global = count_global + count
    count_abs = count_abs + absents
    comptes_ldap = comptes_ldap + comptes
    logging.info("  |_%s/%s utilisateur(s) mis à jour pour les lycées agricoles, %s non trouvé(s)." % (count,comptes,absents))

    logging.info("  |_Ajout du champ Domaine pour les cfa.")
    count, absents, comptes = integration_domaines_etabs(mark, ldap, id_field_domaine, map_etab_domaine, listeEtabs_cfa)
    count_global = count_global + count
    count_abs = count_abs + absents
    comptes_ldap = comptes_ldap + comptes
    logging.info("  |_%s/%s utilisateur(s) mis à jour pour les cfa, %s non trouvé(s)." % (count,comptes,absents))

    connection.commit()
    logging.info("|_%s/%s utilisateur(s) mis à jour pour l'ensemble des établissements, %s/%s non mis à jour." % (count_global, comptes_ldap, count_abs, comptes_ldap))
    logging.info('============ Rattrapage terminé ============')
    logging.info('============================================')

######################### Fonctions BDD #########################

def integration_domaines_etabs(mark, ldap, id_field_domaine, map_etab_domaine, listeEtabs):
    count_by_type = 0
    count_by_type_abs = 0
    count_ldap = 0
    # Récupération des utilisateurs dans le ldap pour tous les établissements dans la liste
    for etab in listeEtabs:
        logging.info("    |_Récupération des utilisateurs dans le ldap pour l'établissement %s." % etab)
        etab_users = get_etab_users(ldap, etab)
        count_ldap = count_ldap + len(etab_users)
        # Ajout ou Mise à jour du domaine pour tous les comptes récupérés
        count = 0
        count_abs = 0
        sans_escouaicourant = 0
        for uid_user_ldap in etab_users:
            user_domain = DEFAULT_DOMAIN
            user_infos = etab_users[uid_user_ldap]
            if not bool(user_infos["ESCOUAICourant"]):
                sans_escouaicourant = sans_escouaicourant + 1
            if len(user_infos["ESCODomaines"]) == 1:
                user_domain = user_infos["ESCODomaines"][0]
            else:
                if bool(user_infos["ESCOUAICourant"]) and user_infos["ESCOUAICourant"] in map_etab_domaine:
                    user_domain = map_etab_domaine[user_infos["ESCOUAICourant"]][0]
            code_retour =  set_user_domain(mark, uid_user_ldap, id_field_domaine, user_domain)
            if code_retour == 0:
                count_abs = count_abs + 1
            count = count + code_retour
        logging.info("    |_%s utilisateur(s) mis à jour." % count)
        logging.info("    |_%s utilisateur(s) non trouvés." % count_abs)
        count_by_type = count_by_type + count
        count_by_type_abs = count_by_type_abs + count_abs
    return count_by_type, count_by_type_abs, count_ldap

### Fonction pour saisir le Domaine d'un utilisateur Moodle
def set_user_domain(mark, uid_user, id_field_domaine, user_domain):
    user_id = get_user_id(mark, uid_user)
    if user_id != 0:
        #logging.debug("    |_Ajout du domaine %s pour l'utilisateur %s." % (user_domain, uid_user))
        sql = "SELECT id FROM %suser_info_data WHERE userid = %s AND fieldid = %s AND data = '%s'"
        sql = sql % (entete, user_id, id_field_domaine, user_domain)
        mark.execute(sql)
        if mark.rowcount > 0:
            result = mark.fetchone()
            sql = "REPLACE INTO %suser_info_data (id, userid, fieldid, data) VALUES (%s, %s,%s,'%s')"
            sql = sql % (entete, result[0], user_id, id_field_domaine, user_domain)
            mark.execute(sql)
        else:
            sql = "INSERT INTO %suser_info_data (userid, fieldid, data) VALUES (%s,%s,'%s')"
            sql = sql % (entete, user_id, id_field_domaine, user_domain)
            mark.execute(sql)
        return 1
    else:
        logging.debug("    |_L'utilisateur %s n'a pas été trouvé dans la base Moodle." %  uid_user)
        return 0
    
### Fonction permettant de récupérer l'id d'un utilisateur d'après son username
def get_user_id(mark, uid_user):
    # On récupère l'id de l'utilisateur s'il existe (username = uid_user)
    sql = "SELECT id FROM %suser WHERE username = '%s'"
    sql = sql % (entete, uid_user)
    mark.execute(sql)

    result = mark.fetchone()
    if mark.rowcount > 0:
        userid = result[ 0 ]
    else:
        userid = 0
    return userid

### Fonction permettant d'etablir une connexion à une BD MySQL
def connect_db( host, user, password, database, port, db_charset ):
    # Etablissement de la connexion
    conn = MySQLdb.connect( host = host, user = user, passwd = password, db = database, charset = db_charset, port = int( port ) )
    conn.set_character_set( db_charset )
    # Choix des options
    mark = conn.cursor( )
    mark.execute( 'SET NAMES ' + db_charset + ';' )
    mark.execute( 'SET CHARACTER SET ' + db_charset + ';' )
    mark.execute( 'SET character_set_connection=' + db_charset + ';' )
    return ( conn, mark )

### Fonction pour récupérer la liste des utilisateurs qui n'ont pas de valeur Domaine de Moodle
### Non utilisée car les utilisateurs sans domaine utilisent lycéess.netocentre.fr par défaut
def get_users_moodle(mark, domaine_id):
    users_moodle = {}

    sql = "SELECT username, id FROM %suser us WHERE id NOT IN (SELECT userid FROM %suser_info_data WHERE fieldid = %%s)"
    sql = sql % (entete, entete) % (domaine_id)    
    mark.execute(sql)
    results = mark.fetchall()

    for result in results:
        users_moodle[result[0]] = result[1]
    
    return users_moodle

### Fonction pour récupére l'id du champ Domaine et le créer s'il n'existe pas
def create_field_domaine(mark):
    id_field_domaine = [ ]

    # Si le champ Domaine existe, on en récupère l'id
    sql = "SELECT id FROM %suser_info_field WHERE shortname = 'Domaine' AND name ='Domaine'"
    sql = sql % (entete)
    mark.execute(sql)
    row = mark.fetchall()

    # Si le champ n'existe pas, on le crée et on récupère l'id
    if not bool(row):
        sql = "INSERT INTO %suser_info_field (shortname, name, datatype, " \
        "description, descriptionformat, categoryid, required, locked, visible, forceunique, " \
        "signup, defaultdata, defaultdataformat, param1, param2, param3, param4, param5)" \
        "VALUES ('Domaine', 'Domaine', 'text', \"<p>Domaine d'utilisation de Moodle pour " \
        "l'utilisateur</p>\", 1, 1, 0, 0, 1, 0, 1, '%s', 0, 25, 25, 0, '', '')"
        sql = sql % (entete, DEFAULT_DOMAIN)
        mark.execute(sql)
        id_field_domaine = mark.lastrowid
    else:
        id_field_domaine = row[0][0]

    return id_field_domaine

######################### Fonctions LDAP #########################

### Fonction pour récupérer la liste des comptes ldap pour tous les établissements dans la liste
def get_users_ldap(ldap, listeEtabs):
    users_ldap = {}
    for etab in listeEtabs:
        etab_users = get_etab_users(ldap, etab)
        users_ldap.update(etab_users)
    return users_ldap

### Fonction pour récupérer la liste des comptes ldap pour un établissement
def get_etab_users(ldap, uai_etab):
    filtre = "(&(|(objectClass=ENTEleve)(objectClass=ENTDirecteur)" \
            "(objectClass=ENTAuxEnseignant)(objectClass=ENTAuxNonEnsEtab)" \
            "(objectClass=ENTAuxNonEnsCollLoc))(ESCOUAI=%s))" % ( uai_etab )
    ldap_result_id  = ldap_search_student( ldap, personnesDN, filtre )

    # Recuperation du resultat de la recherche
    result_set = ldap_retrieve_all_entries( ldap, ldap_result_id )

    users_ldap = {}
    # Pour chaque compte, on récupère l'UAI et le Domaine
    for ldap_entry in result_set :
        ldap_entry_infos = ldap_entry[0][1]
        user_uid         = ldap_entry_infos["uid"][0]
        user_domaines    = ldap_entry_infos["ESCODomaines"]
        user_uai_courant = ldap_entry_infos['ESCOUAICourant'][0]
	    # On ajoute les données dans la liste
        users_ldap[user_uid] = { "ESCODomaines" : user_domaines, "ESCOUAICourant" : user_uai_courant }
        
    return users_ldap

### Fonction pour récupérer la liste "ESCOUAICourant : Domaine" des établissements
def get_domaine_etab(ldap):
    filtre = "(&(ObjectClass=ENTEtablissement)(!(ENTStructureSiren=0000000000000A)))"
    ldap_result_id  = ldap_search_structure( ldap, structuresDN, filtre )

    # Recuperation du resultat de la recherche
    result_set = ldap_retrieve_all_entries( ldap, ldap_result_id )

    etabs_ldap = {}
    # Pour chaque établissement, on récupère l'UAI et le Domaine
    for ldap_entry in result_set :
        ldap_entry_infos = ldap_entry[0][1]
        etab_domaines    = ldap_entry_infos["ESCODomaines"]
        etab_uai         = ldap_entry_infos['ENTStructureUAI'][0]
	    # On ajoute les données dans la liste
        etabs_ldap[etab_uai] = etab_domaines
    return etabs_ldap

### Fonction permettant d'etablir une connexion a un LDAP
def connect_ldap( ldap_server, ldap_username, ldap_password  ):
    l = ldap.open( ldap_server )
    l.protocol_version = ldap.VERSION3
    l.simple_bind_s( ldap_username, ldap_password )
    return l

### Fonction permettant de faire une recherche LDAP.
def ldap_search( ldap_connection, dn, scope, filter, attributes ):
    return ldap_connection.search( dn, scope, filter, attributes )

###Fonction permettant de faire une recherche LDAP sur les structures.
def ldap_search_student( ldap_connection, dn, filter ):
    return ldap_search( ldap_connection, dn, ldap.SCOPE_ONELEVEL, filter, ATTRIBUTES_STUDENT )

###Fonction permettant de faire une recherche LDAP sur les structures.
def ldap_search_structure( ldap_connection, dn, filter ):
    return ldap_search( ldap_connection, dn, ldap.SCOPE_ONELEVEL, filter, ATTRIBUTES_STRUCTURE )

### Fonction permettant de recuperer le resultat d'une recherche au sein d'un tableau.
def ldap_retrieve_all_entries( ldap_connection, result_id ):
    result_entries = [ ]
    result_data = [ 0 ]
    while result_data :
        result_type, result_data = ldap_connection.result( result_id, 0 )
        if result_data and result_type == ldap.RES_SEARCH_ENTRY:
            result_entries.append( result_data )
    return result_entries

if __name__ == "__main__":
    rattrapage_domaines()

