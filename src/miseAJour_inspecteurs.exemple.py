#!/usr/bin/env python3
# coding: utf-8

from synchromoodle.miseAJourTrt import miseAJourInspecteurs

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
# LDAP - Inspecteurs
#######################################
# Attribut utilise pour determiner si un utilisateur est inspecteur
attributInspecteur = "ESCOPersonProfils"

# Valeur de l'attribut indiquant que l'utilisateur est un inspecteur
valeurAttributInspecteur = ["INS"]

#######################################
# Mise a jour des inspecteurs
#######################################
miseAJourInspecteurs(host, user, password, nomBD, port, ldapServer, ldapUsername, ldapPassword, personnesDN,
                     structuresDN, entete, attributInspecteur, valeurAttributInspecteur)
