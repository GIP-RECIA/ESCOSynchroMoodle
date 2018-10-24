#!/usr/bin/python -d
# -*- coding: utf-8 -*-

import sys
from miseAJourTrt import miseAJour
from miseAJourTrt import miseAJourInterEtabs
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
prefixAdminMoodleLocal = "cfa:admin:Moodle:local:" 


#######################################
# Administrateurs locaux de
# l"etablissement
#######################################

# Prefix de l"attribut "isMemberOf" indiquant que l"utilisateur est un administrateur local
prefixAdminLocal = "cfa:admin:local:" 

######################################
# Traitements precedents
######################################

# Etablissements
fileTrtPrecedent = "<path_fileTrtPrecedent>" 
fileSeparator    = "-" 

#######################################
# Etablissements synchronises
#######################################
#EtabRgp = [
#           { NomEtabRgp : "Regroupement 1", UaiRgp : ["0180755y","0410590u"]}
#        ];

NomEtabRgp  = "<NomEtabRgp>" ;
UaiRgp      = "uai" ;

EtabRgp = [
           { NomEtabRgp : "CFA DU CHER", UaiRgp : [ "0180755y", "0180939y", "0410892y" ]},
           { NomEtabRgp : "FORMASAT CFA Sport Animation Tourisme", UaiRgp : [ "0451583b", "0281155d","0411064j" ]},
           { NomEtabRgp : "CFA MFR Centre et Île-de-France", UaiRgp : ["0451715v", "0370983t", "0371686g", "0371710h", "0371711j", "0371723x", "0411059d", "0451691u", "0451693w", "0451694x"]}
        ];

listeEtab = ["0180755y", "0180939y", "0180865t", "0180877f", "0280738a", "0280904f", "0281155d", "0333333y", "0360548a", "0360777z", "0360709a", "0370811f", "0370983t", "0370984u", "0371686g", "0371710h", "0371711j", "0371723x", "0410590u", "0410592w", "0410892y", "0411059d", "0411064j", "0450807h", "0450808j", "0450809k", "0450810l", "0450810q", "0451583b", "0451691u", "0451693w", "0451694x", "0451715v"]

listeEtabSansAdmin = []

# Etablissement dont le mail des utilisateurs n"est pas synchronise
listeEtabSansMail = []

###################
# Mise a jour
###################
if __name__ == "__main__":
    purge = purge_demandee( sys.argv[ 1: ] )
    # Mise a jour pour chaque CFA de listeEtab :
    #  - de l"etablissement lui-meme
    #  - des enseignants
    #  - des eleves
    #  - des administrateurs locaux
    miseAJour(host, user, password, nomBD, port, ldapServer, ldapUsername, ldapPassword, listeEtab, listeEtabSansAdmin, listeEtabSansMail, structuresDN, personnesDN, entete, prefixAdminMoodleLocal, prefixAdminLocal, EtabRgp, NomEtabRgp, UaiRgp, fileTrtPrecedent, fileSeparator, purge )
