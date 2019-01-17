#!/usr/bin/env python3
# coding: utf-8

import logging

import sys

from synchromoodle.miseAJourTrt import miseAJour
from synchromoodle.utilsOptions import purge_demandee

logging.basicConfig(format="%(levelname)s:%(message)s", stream=sys.stdout, level=logging.INFO)

#######################################
# Infos pour la connexion et l"acces  
# aux donnees sur la BD moodle
#######################################
nomBD = "moodle"
user = "moodle"
password = "moodle"
host = "192.168.1.100"
port = "9806"
entete = "mdl_"

#######################################
# Infos pour la connexion et l"acces 
# aux donnees sur le serveur LDAP
#######################################
ldapServer = "ldap://192.168.1.100:9889"
ldapUsername = "cn=admin,ou=administrateurs,dc=esco-centre,dc=fr"
ldapPassword = "admin"

baseDN = "dc=esco-centre,dc=fr"
structuresDN = "ou=structures," + baseDN
personnesDN = "ou=people," + baseDN
adminDN = "ou=administrateurs," + baseDN

#######################################
# Administrateurs locaux de Moodle
#######################################

# Prefixe de l"attribut "isMemberOf" indiquant que l"utilisateur est un administrateur
# local de Moodle
prefixAdminMoodleLocal = "(esco|clg37):admin:Moodle:local:"

#######################################
# Administrateurs locaux de
# l"etablissement
#######################################

# Prefix de l"attribut "isMemberOf" indiquant que l"utilisateur est un administrateur local
prefixAdminLocal = "(esco|clg37):admin:local:"

fileTrtPrecedent = "trtPrecedent_academique.txt"
fileSeparator = "-"

#######################################
# Etablissements synchronises
#######################################
# EtabRgp = [
#           { NomEtabRgp : "Regroupement 1", UaiRgp : ["0180755y","0410590u"]}
#        ];

NomEtabRgp = "nomEtabRgp"
UaiRgp = "uai"

EtabRgp = []

listeEtab = ["0450822X", "0410031L", "0371122U", "0450066C", "0451483T", "0410593X", "0410030K", "0370001A", "0360003H",
             "0370040T", "0370036N", "0451304Y", "0450051L", "0180008L", "0360011S", "0280657M", "0280036M", "0450062Y",
             "0280021W", "0360024F", "0410959V", "0371417P", "0280864M", "0450042B", "0370009J", "0360002G", "0370039S",
             "0180006J", "0410017W", "0450790P", "0451442Y", "0281047L", "0450064A", "0280925D", "0180007K", "0180042Y",
             "0371418R", "0360008N", "0180024D", "0180026F", "0280044W", "0360009P", "0281077U", "0410832G", "0180823X",
             "0180777X", "0360658V", "0180036S", "0180010N", "0180005H", "0180009M", "0280009H", "0280015P", "0280957N",
             "0280022X", "0360026H", "0360019A", "0360005K", "0371211R", "0370037P", "0370038R", "0370053G", "0370054H",
             "0371100V", "0410002E", "0410899E", "0410718H", "0410036S", "0451484U", "0451526P", "0450750W", "0450050K",
             "0450782F", "0451067R", "0280659P", "0360050J", "0451104F", "0180025E", "0180035R", "0280007F", "0280019U",
             "0280700J", "0281021H", "0360043B", "0370016S", "0370032J", "0370035M", "0370771M", "0370888P", "0371099U",
             "0371123V", "0371258S", "0410001D", "0450029M", "0450040Z", "0450043C", "0450049J", "0450786K", "0451037H",
             "0451462V", "0410860M", "0371159J", "0371204H", "0371316E", "0370011L", "0370991B", "0370041U", "0377777U",
             "0370006F", "0370015R", "0370768J", "0370791J", "0370792K", "0370799T", "0370886M", "0370887N", "0370994E",
             "0371101W", "0371158H", "0371191U", "0371248F", "0371391L", "0371397T", "0371403Z", "0371124W", "0370995F",
             "0370007G", "0370010K", "0371098T", "0370013N", "0371378X", "0370993D", "0370022Y", "0370034L", "0370766G",
             "0370044X", "0370045Y", "0370769K", "0370886M", "0370884K", "0371189S", "0370024A"]

listeEtabSansAdmin = []

# Etablissement dont le mail des professeurs n'est pas synchronise
listeEtabSansMail = ["0371204H", "0371159J", "0370011L", "0370041U", "0370991B", "0371316E"]

###################
# Mise a jour
###################
if __name__ == "__main__":
    purge_cohortes = purge_demandee(sys.argv[1:])
    # Mise a jour pour chaque etablissement de listeEtab :
    #  - de l"etablissement lui-meme
    #  - des enseignants
    #  - des eleves
    #  - des administrateurs locaux
    miseAJour(host, user, password, nomBD, port, ldapServer, ldapUsername, ldapPassword, listeEtab, listeEtabSansAdmin,
              listeEtabSansMail, structuresDN, personnesDN, entete, prefixAdminMoodleLocal, prefixAdminLocal, EtabRgp,
              NomEtabRgp, UaiRgp, fileTrtPrecedent, fileSeparator, purge_cohortes)
