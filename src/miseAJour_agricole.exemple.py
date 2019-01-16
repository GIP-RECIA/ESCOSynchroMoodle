#!/usr/bin/env python2
# coding: utf-8

import sys
from miseAJourTrt import miseAJour
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
structuresDN    = "ou=structures"+baseDN
personnesDN     = "ou=people"+baseDN
adminDN         = "ou=administrateurs"+baseDN

#######################################
# Administrateurs locaux de Moodle
#######################################

# Prefixe de l"attribut "isMemberOf" indiquant que l"utilisateur est un administrateur
# local de Moodle
prefixAdminMoodleLocal = "agri:admin:Moodle:local:" 


#######################################
# Administrateurs locaux de
# l"etablissement
#######################################

# Prefix de l"attribut "isMemberOf" indiquant que l"utilisateur est un administrateur local
prefixAdminLocal = "agri:admin:local:" 

NomEtabRgp       = "nomEtabRgp"
UaiRgp           = "uai"

fileTrtPrecedent = "<path_fileTrtPrecedent>" 
fileSeparator    = "-" 

#EtabRgp = [
#           { NomEtabRgp : "Regroupement 1", UaiRgp : ["0180755y","0410590u"]}
#        ];

EtabRgp = [ ]

listeEtab = [ "0410018X", "0180585N", "0280706R", "0370878D", "0450094H", "0451535Z", "0450027K", "0410629L", "0370781Y", "0360017Y", "0370794M", "0410626H" ]
listeEtabSansAdmin = [ ]

# Etablissement dont le mail des professeurs n"est pas synchronise
listeEtabSansMail = [ ]

###################
# Mise a jour
###################
if __name__ == "__main__":
    purge = purge_demandee( sys.argv[ 1: ] )
    # Mise a jour pour chaque etablissement de listeEtab :
    #  - de l'etablissement lui-meme
    #  - des enseignants
    #  - des eleves
    #  - des administrateurs locaux
    miseAJour(host, user, password, nomBD, port, ldapServer, ldapUsername, ldapPassword, listeEtab, listeEtabSansAdmin, listeEtabSansMail, structuresDN, personnesDN, entete, prefixAdminMoodleLocal, prefixAdminLocal, EtabRgp, NomEtabRgp, UaiRgp, fileTrtPrecedent, fileSeparator, purge )
