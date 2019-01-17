#!/usr/bin/env python3
# coding: utf-8

import logging

import sys

from synchromoodle.miseAJourTrt import miseAJour
from synchromoodle.utilsOptions import purge_demandee

logging.basicConfig(format='%(levelname)s:%(message)s', stream=sys.stdout, level=logging.INFO)

#######################################
# Infos pour la connexion et l'acces  
# aux donnees sur la BD moodle
#######################################
nomBD = "<nomBD>"
user = "<user>"
password = "<password>"
host = "<host>"
port = "<port>"
entete = "mdl_"

#######################################
# Infos pour la connexion et l'acces 
# aux donnees sur le serveur LDAP
#######################################
ldapServer = "<ldapServer>"
ldapUsername = "<ldapUsername>"
ldapPassword = "<ldapPassword>"

baseDN = ",dc=esco-centre,dc=fr"
structuresDN = "ou=structures" + baseDN
personnesDN = "ou=people" + baseDN
adminDN = "ou=administrateurs" + baseDN

#######################################
# Administrateurs locaux de Moodle
#######################################

# Prefixe de l'attribut 'isMemberOf' indiquant que l'utilisateur est un administrateur
# local de Moodle
prefixAdminMoodleLocal = "ef2s:admin:Moodle:local:"

#######################################
# Administrateurs locaux de
# l'etablissement
#######################################

# Prefix de l'attribut 'isMemberOf' indiquant que l'utilisateur est un administrateur local
prefixAdminLocal = "ef2s:admin:local:"

fileTrtPrecedent = '<path_fileTrtPrecedent>'
fileSeparator = '-'

#######################################
# Etablissements synchronises
#######################################
# EtabRgp = [
#           { NomEtabRgp : "Regroupement 1", UaiRgp : ['0180755y','0410590u']}
#        ];

NomEtabRgp = "<NomEtabRgp>"
UaiRgp = "uai"

EtabRgp = []

listeEtab = ['0370074E']

listeEtabSansAdmin = []

# Etablissement dont le mail des professeurs n'est pas synchronise
listeEtabSansMail = []

###################
# Mise a jour
###################
if __name__ == "__main__":
    purge_cohortes = purge_demandee(sys.argv[1:])
    # Mise a jour pour chaque etablissement de listeEtab :
    #  - de l'etablissement lui-meme
    #  - des enseignants
    #  - des eleves
    #  - des administrateurs locaux
    miseAJour(host, user, password, nomBD, port, ldapServer, ldapUsername, ldapPassword, listeEtab, listeEtabSansAdmin,
              listeEtabSansMail, structuresDN, personnesDN, entete, prefixAdminMoodleLocal, prefixAdminLocal, EtabRgp,
              NomEtabRgp, UaiRgp, fileTrtPrecedent, fileSeparator, purge_cohortes)
