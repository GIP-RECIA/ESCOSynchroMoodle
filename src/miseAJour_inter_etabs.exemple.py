#!/usr/bin/env python2
# coding: utf-8

import sys
from synchromoodle.miseAJourTrt import miseAJourInterEtabsAll, miseAJourInterEtabsCFA
from synchromoodle.utilsOptions import purge_demandee


#######################################
# Infos pour la connexion et l"acces  
# aux donnees sur la BD moodle
#######################################
nomBD       = "<nomBD>" 
user        = "<user>" 
password    = "<password>" 
host        = "<host>" 
port        = "<port>" 
entete      = "mdl_" 

#######################################
# Infos pour la connexion et l"acces 
# aux donnees sur le serveur LDAP
#######################################
ldapServer      = "<ldapServer>" 
ldapUsername    = "<ldapUsername>" 
ldapPassword    = "<ldapPassword>" 

baseDN          = ",dc=esco-centre,dc=fr" 
structuresDN    = "ou=structures"+baseDN
personnesDN     = "ou=people"+baseDN
adminDN         = "ou=administrateurs"+baseDN


######################################
# Traitements precedents
######################################

# Inter etablissements
fileTrtPrecedentInterEtabs  = "<path_fileTrtPrecedentInterEtabs>" 
fileSeparatorInterEtabs     = "-" 

# Inter CFA
fileTrtPrecedentInterEtabsCFA   = "<path_fileTrtPrecedentInterEtabsCFA>" 
fileSeparatorInterEtabsCFA      = "-" 

######################################
# Utilisateurs synchronises
######################################
# Tableau permettant d"injecter les utilisateurs dans des cohortes de l"inter-etablissements
prefix_cohort_name_cfa = "CFA :"
prefix_cohort_name_clg = "CLG37 :"
prefix_cohort_name_la  = "LA :"
prefix_cohort_name_lyc = "LYC :"
prefix_cohort_name_lyc_clg = "LYC & CLG37 :"

############
# CFA
############
inter_etabs_cohorts_cfa = {
    "cfa:Inter_etablissements:Tous_Admin_local"             : "%s Tous les formateurs" % prefix_cohort_name_cfa,
    "cfa:Inter_etablissements:Tous_Direction"               : "%s Tout le personnel de direction" % prefix_cohort_name_cfa,
    "cfa:Inter_etablissements:Tous_Mediateur"               : "%s Tous les mediateurs" % prefix_cohort_name_cfa,
    "cfa:Inter_etablissements:Tous_Documentation"           : "%s Tous les documentalistes" % prefix_cohort_name_cfa,
    "cfa:Inter_etablissements:Tous_Profs"                   : "%s Tous les formateurs" % prefix_cohort_name_cfa,
    "cfa:Inter_etablissements:Tous_Responsable_Pedagogique" : "%s Tous les responsables pedagogiques" % prefix_cohort_name_cfa,
    "cfa:Inter_etablissements:Tous_Referent_DIMA"           : "%s Tous les referents DIMA" % prefix_cohort_name_cfa,
    "cfa:Inter_etablissements:Tous_Referent_SCB"            : "%s Tous les referents savoirs et competences de base" % prefix_cohort_name_cfa,
    "cfa:admin:local:*"                                     : "%s Tous les administrateurs ENT" % prefix_cohort_name_cfa
}

############
# LYCEES
############
inter_etabs_cohorts_lycees = {
    "esco:Etablissements:*:Profs"                   	: "%s Tous les profs" % prefix_cohort_name_lyc,
    "esco:admin:local:*"                                : "%s Tous les administrateurs ENT" % prefix_cohort_name_lyc,
    "esco:*:DIRECTION"                                  : "%s Tous les chefs d\'établissement" % prefix_cohort_name_lyc,
    "esco:*:EDUCATION"                                  : "%s Tous les CPE" % prefix_cohort_name_lyc
    #"acad:Services_Academique:*:INSPECTION"             : "%s Tous les inspecteurs" % prefix_cohort_name_lyc
}

############
# AGRIS
############
inter_etabs_cohorts_lycees_agri = {
    "agri:Etablissements:*:Profs"                   	: "%s Tous les profs" % prefix_cohort_name_la,
    "agri:admin:local:*"                                : "%s Tous les administrateurs ENT" % prefix_cohort_name_la
}

############
# COLLEGES
############
inter_etabs_cohorts_colleges = {
    "clg37:Etablissements:*:Profs"                   	: "%s Tous les profs" % prefix_cohort_name_clg,
    "clg37:admin:local:*"                               : "%s Tous les administrateurs ENT" % prefix_cohort_name_clg,
    "clg37:*:DIRECTION"                                 : "%s Tous les chefs d\'établissement" % prefix_cohort_name_clg,
    "clg37:*:EDUCATION"                                 : "%s Tous les CPE" % prefix_cohort_name_clg
}

############
# TOUS
############
inter_etabs_cohorts_all = dict( inter_etabs_cohorts_cfa.items( ) + inter_etabs_cohorts_lycees.items( ) + inter_etabs_cohorts_lycees_agri.items( ) + inter_etabs_cohorts_colleges.items( ) )

# Attribut utilise pour determiner les utilisateurs inter-etablissements
interEtabsAttribut = "isMemberOf" 

# Utilisateurs speciaux de la section inter-etablissement
interEtabsUser  = [ "cfa:Applications:Espace_Moodle:Inter_etablissements" ]

# Administrateurs de la section inter-etablissement
interEtabsAdmin = "cfa:admin:Moodle:local:Inter_etablissements" 


###################
# Mise a jour
###################
if __name__ == "__main__":
    purge = purge_demandee( sys.argv[ 1: ] )
    # Mise a jour pour la categorie inter-etablissements avec tous les etablissements :
    #  - des utilisateurs
    #  - des administrateurs locaux
    miseAJourInterEtabsAll( host, user, password, nomBD, port, ldapServer, ldapUsername, ldapPassword, structuresDN, personnesDN, entete, interEtabsAttribut, interEtabsUser, interEtabsAdmin, inter_etabs_cohorts_all, fileTrtPrecedentInterEtabs, fileSeparatorInterEtabs, purge )

    # Mise a jour pour la categorie inter-etablissements avec uniquement les CFA :
    #  - des utilisateurs
    #  - des administrateurs locaux
    miseAJourInterEtabsCFA( host, user, password, nomBD, port, ldapServer, ldapUsername, ldapPassword, structuresDN, personnesDN, entete, interEtabsAttribut, interEtabsUser, interEtabsAdmin, inter_etabs_cohorts_cfa, fileTrtPrecedentInterEtabsCFA, fileSeparatorInterEtabsCFA, purge )
