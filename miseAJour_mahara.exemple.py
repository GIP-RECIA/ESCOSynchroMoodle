#!/usr/bin/python -d
# -*- coding: utf-8 -*-

import sys
from miseAJourTrt import *
from utilsOptions import purge_demandee


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
personnesDN     = "ou=people"+baseDN
adminDN         = "ou=administrateurs"+baseDN


######################################
# Traitements precedents
######################################
fileTrtPrecedentMahara  = "<path_fileTrtPrecedentMahara>" 
fileSeparatorMahara     = "-" 

######################################
# Utilisateurs synchronises
######################################

# Utilisateurs a recuperer dans le LDAP
maharaAttribut  = "isMemberOf" 
maharaUser      = [ "clg37:Etablissements:*:groupes_locaux:Mahara:Moodle-Mahara" , "esco:Etablissements:*:groupes_locaux:Mahara:Moodle-Mahara" ]

###################
# Mise a jour
###################
if __name__ == "__main__":
    purge = purge_demandee( sys.argv[ 1: ] )
    # Mise a jour des utilisateurs Mahara
    miseAJourMahara( host, user, password, nomBD, port, ldapServer, ldapUsername, ldapPassword, personnesDN, entete, maharaAttribut, maharaUser, fileTrtPrecedentMahara, fileSeparatorMahara, purge )
