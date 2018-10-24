#!/usr/bin/python -d
# -*- coding: utf-8 -*-


###############################################################################
# IMPORTS
###############################################################################
# System imports
import datetime
import logging
import re
import sys

logging.basicConfig(format='%(levelname)s:%(message)s', stream=sys.stdout, level=logging.INFO)
#logging.basicConfig(format='%(levelname)s:%(message)s', stream=sys.stdout, level=logging.DEBUG)

# Personnal imports
from utilsDB   import * 
from utilsFile import *
from utilsLDAP import *

###############################################################################
# CONSTANTES
###############################################################################

#######################################
# THEME PAR DEFAUT POUR LES
# UTILISATEURS INTER-ETABS
#######################################
DEFAULT_MOODLE_THEME = "netocentre"

#######################################
# MAIL
#######################################
# Par defaut les mails sont uniquement
# affiches aux participants du cours
DEFAULT_MAIL_DISPLAY = 2

# Email utilise lorsque les personnes
# n'ont pas d'email dans le LDAP
DEFAULT_MAIL = 'non_renseigne@netocentre.fr'

#######################################
# CLES UTILISE POUR STOCKER LES
# TIMESTAMP
#######################################
# Cle pour pour stocker le timestamp dud dernier traitement inter-etablissements
CLE_TRT_INTER_ETAB = "INTER_ETAB"

# Cle pour stocker le timestamp dernier traitement mahara
CLE_TRT_MAHARA = "MAHARA"

#######################################
# NIVEAUX DE CONTEXTES
#######################################
# Id de l'instance concernant Moodle
ID_INSTANCE_MOODLE = 1

# Niveau de contexte pour un cours
NIVEAU_CTX_COURS = 50

#######################################
# ID ROLES
#######################################
# Id pour le role createur de cours
ID_ROLE_CREATEUR_COURS = 2

# Id pour le role enseignant
ID_ROLE_ENSEIGNANT = 3

# Id pour le role eleve
ID_ROLE_ELEVE = 5

# Id pour le role inspecteur
ID_ROLE_INSPECTEUR = 9

# Id pour le role directeur
ID_ROLE_DIRECTEUR = 18

# Id pour le role d'utilisateur avec droits limites
ID_ROLE_UTILISATEUR_LIMITE = 14

#######################################
# LDAP
#######################################
# Type de structure d'un CFA
TYPE_STRUCTURE_CFA = "CFA"

# Type de structure d'un college
TYPE_STRUCTURE_CLG = "COLLEGE"

###############################################################################
# FONCTIONS
###############################################################################

######################################################################
# Fonction permettant d'indiquer si un etablissement fait partie
# d'un regroupement etablissement_ou non.
######################################################################
def estGrpEtab(rne, etabRgp, nomEtabRgp, uaiRgp):
    for uai_etablissement in etabRgp:
        if rne in uai_etablissement[uaiRgp]:
            return uai_etablissement;
    return False

######################################################################
# Fonction permettant d'extraire le nom des classes a partir de 
# classes issues de l'annuaire LDAP
######################################################################
def extraireClassesLdap( classesLdap ):
    classes = [ ]
    for classeLdap in classesLdap:
        split = classeLdap.rsplit("$")
        if len( split ) > 1:
            classes.append( split[1] )
    return classes

######################################################################
# Fonction permettant de mettre a jour les droits d'un enseignant.
# Cette mise a jour consiste a :
#   - Supprimer les roles non autorises
#   - ajouter les roles
######################################################################
def mettre_a_jour_droits_enseignant( mark, entete, enseignant_infos, gereAdminLocal, id_enseignant, id_context_categorie, id_context_course_forum, uais_autorises ):
    # Recuperation des themes autorises pour l'enseignant
    themes_autorises = [ uai_autorise.lower( ) for uai_autorise in uais_autorises ]
    logging.debug("      |_ Etablissements autorises pour l'enseignant pour %s : %s" % ( enseignant_infos, str( themes_autorises ) ) )

    #########################
    # ZONES PRIVEES
    #########################
    # Recuperation des ids des roles et les themes non autorises
    ids_roles_non_autorises, ids_themes_non_autorises = get_ids_and_themes_not_allowed_roles( mark, entete, id_enseignant, themes_autorises )

    # Suppression des roles non autorises
    if ids_roles_non_autorises:
        delete_roles( mark, entete, ids_roles_non_autorises )
        logging.info("      |_ Suppression des rôles d'enseignant pour %s dans les établissements %s" % ( enseignant_infos, str( ids_themes_non_autorises ) ) )
        logging.info("         Les seuls établissements autorisés pour cet enseignant sont %s"  % str( themes_autorises ))

    #########################
    # FORUMS
    #########################
    # Recuperation des SIREN des etablissements dans lequel l'enseignant travaille
    sirens = get_descriptions_course_categories_by_themes( mark, entete, themes_autorises )
    
    # Shortname des forums associes
    shortnames_forums = [ ( "ZONE-PRIVEE-%s" % str( siren ) ) for siren in sirens ] 
    
    # Recuperation des roles sur les forums qui ne devraient plus exister
    ids_roles_non_autorises, forums_summaries = get_ids_and_summaries_not_allowed_roles( mark, entete, id_enseignant, shortnames_forums ) 

    # Suppression des roles non autorises
    if ids_roles_non_autorises:
        # Suppression des roles
        delete_roles( mark, entete, ids_roles_non_autorises )
        logging.info("      |_ Suppression des rôles d'enseignant pour %s sur les forum '%s' " % (enseignant_infos, str( forums_summaries )))
        logging.info("         Les seuls établissements autorisés pour cet enseignant sont '%s'"  % themes_autorises)


######################################################################
# Fonction permettant d'effectuer la mise a jour de la BD
# Moodle via les infos issues du LDAP
#
# Parametres:
# -----------
#  - host     : hote hebergeant la BD moodle
#  - user     : utilisateur pour la connexion a la BD moodle
#  - password : mot de passe pour la connexion a la BD moodle
#  - nomBD    : nom de la BD moodle
#
#  - ldapServer   : hote hebergeant le serveur LDAP
#  - ldapUserName : utilisateur pour la connexion au LDAP
#  - ldapPassword : mot de passe pour la connexion au serveur LDAP
#
#  - listeEtab          : liste des etablissements a traiter 
#  - listeEtabSansAdmin : liste des etablissements n'ayant pas d'admin
#
#  - structureDN : nom absolu pour acceder aux structures dans le LDAP
#  - personneDN  : nom absolu pour acceder aux personnes dans le LDAP
#
#  - entete : entete des noms de table dans la BD moodle
#
#  - prefixAdminMoodle : contenu de l'attribut 'isMemberOf' dans le LDAP
#                  indiquant le statut d'administrateur de Moodle 
#           d'une personne
#
#  - prefixAdminLocal : contenu de l'attribut 'isMemberOf' dans le LDAP
#                  indiquant le statut d'administrateur local d'une personne
#
#  - EtabRgp    : regroupement d'etablissements
#  - nomEtabRgp : nom du regroupement d'etablissements
#  - uaiRgp     : etablissement_uai du regroupement d'etablissements 
#
#  - fileTrtPrecedent : fichier contenant les dates de traitement
#                       precedent pour les etablissements
#  - fileSeparator    : seperateur utilise dans le fichier de 
#                       traitement pour separarer l'etablissement de
#                       sa date de traitement precedent
#  - purgeCohortes    : booleen indiquant si la purge des cohortes
#                       doit etre effectuee, ou non
######################################################################
def miseAJour(host,user,password,nomBD,port,ldapServer,ldapUsername, ldapPassword,listeEtab,listeEtabSansAdmin,listeEtabSansMail,structures_dn,personnes_dn,entete,prefixAdminMoodle, prefixAdminLocal, EtabRgp, NomEtabRgp, UaiRgp, fileTrtPrecedent, fileSeparator, purgeCohortes):
    try:
        logging.info('============================================')
        logging.info('Synchronisation établissements : DEBUT')

        ###################################################
        # Connexion a la BD Moodle et recuperation 
        # d'informations
        ###################################################
        connection, mark = connect_db( host, user, password, nomBD, port, 'utf8' )

        # Liste pour stocker les admins locaux de Moodle durant le traitement
        list_moodle_admin = [ ]

        # Liste pour stocker les admins locaux durant le traitement
        list_admin = [ ]

        # Ids des categories inter etablissements
        id_context_categorie_inter_etabs    = get_id_context_inter_etabs( mark, entete ) 

        id_categorie_inter_cfa              = get_id_categorie_inter_etabs_cfa( mark, entete )
        id_context_categorie_inter_cfa      = get_id_context_categorie( mark, entete, id_categorie_inter_cfa )

        # Recuperation des ids des roles admin local et extended teacher
        id_role_admin_local         = get_id_role_admin_local( mark, entete )
        id_role_extended_teacher    = get_id_role_extended_teacher( mark, entete )

        # Recuperation du timestamp actuel
        maintenant_sql = get_timestamp_now( mark )

        # Recuperation de l'id du user info field pour la classe
        id_user_info_field_classe = get_id_user_info_field_classe( mark, entete )
        if id_user_info_field_classe is None:
            insert_moodle_user_info_field_classe( mark, entete )
            id_user_info_field_classe = get_id_user_info_field_classe( mark, entete )


        ###################################################
        # Connexion au LDAP
        ###################################################
        l = connect_ldap( ldapServer, ldapUsername, ldapPassword )

        ###################################################
        # On ne va traiter, dans la suite du programme, 
        # que les utilisateurs ayant subi
        # une modification depuis le dernier traitement 
        ###################################################
        # Recuperation des dates de traitement precedent par etablissement
        timeStampByEtab  = read_time_stamp_by_etab( fileTrtPrecedent, fileSeparator )  

        # Recuperation du time stamp actuel au format LDAP
        now = datetime.datetime.now( )
        timeStampNow = format_date( now )

        ###################################################
        # Traitement etablissement par etablissement afin 
        # d'éviter la remontée de trop d'occurences du LDAP
        ###################################################
        for uai_etablissement in listeEtab:

            logging.info("  |_ Traitement de l'établissement %s" % uai_etablissement )

            gereAdminLocal = uai_etablissement not in listeEtabSansAdmin
            etablissement_regroupe = estGrpEtab(uai_etablissement, EtabRgp, NomEtabRgp, UaiRgp);

            # Regex pour savoir si l'utilisateur est administrateur moodle
            regexpAdminMoodle = prefixAdminMoodle + ".*_%s$" % uai_etablissement

            # Regex pour savoir si l'utilisateur est administrateur local
            regexpAdminLocal = prefixAdminLocal + ".*_%s$" % uai_etablissement


            ####################################
            # Mise a jour de l'etablissement 
            ####################################
            # On met a jour l'etablissement meme si celui-ci
            # n'a pas ete modifie depuis la derniere synchro
            # car des infos doivent etre recuperees dans Moodle 
            # dans tous les cas
            filtre          = get_filtre_etablissement( uai_etablissement )
            ldap_result_id  = ldap_search_structure( l, structures_dn, filtre ) 

            # Recuperation du resultat de la recherche
            result_set = ldap_retrieve_all_entries( l, ldap_result_id )

            for ldap_entry in result_set :
                #  Recuperation des informations
                ldap_entry_infos             = ldap_entry[0][1]
                etablissement_nom            = ldap_entry_infos['ou'][0].replace("'","\\'").replace("-ac-ORL._TOURS", "").decode( "utf-8" )
                etablissement_type_structure = ldap_entry_infos['ENTStructureTypeStruct'][0]
                etablissement_code_postal    = ldap_entry_infos['postalCode'][0][:2]
                etablissement_siren          = ldap_entry_infos['ENTStructureSIREN'][0]
                etablissement_uai            = ldap_entry_infos['ENTStructureUAI'][0]
                etablissement_path           = "/1"
                
                # Si l'etablissement fait partie d'un groupement
                if etablissement_regroupe:
                    etablissement_ou    = etablissement_regroupe[NomEtabRgp]
                    etablissement_uai   = etablissement_regroupe[UaiRgp][0]
                else:
                    etablissement_ou    = etablissement_nom

                # Recuperation du bon theme
                etablissement_theme = etablissement_uai.lower( )

                # Creation de la structure si elle n'existe pas encore
                id_etab_categorie = get_id_course_category_by_theme( mark, entete, etablissement_theme )
                if id_etab_categorie is None:
                    insert_moodle_structure( mark, entete, etablissement_regroupe, etablissement_nom, etablissement_path, etablissement_ou, etablissement_siren, etablissement_theme )
                    id_etab_categorie = get_id_course_category_by_id_number( mark, entete, etablissement_siren )

                # Mise a jour de la description dans la cas d'un groupement d'etablissement
                if etablissement_regroupe:
                    description = get_description_course_category( mark, entete, id_etab_categorie )
                    if description.find(etablissement_siren) == -1:
                        description = "%s$%s@%s" % ( description, etablissement_siren, etablissement_nom )
                        update_course_category_description( mark, entete, id_etab_categorie , description )
                        update_course_category_name( mark, entete, id_etab_categorie , etablissement_ou )

                # Recuperation de l'id du contexte correspondant à l'etablissement
                id_context_categorie    = get_id_context_categorie( mark, entete, id_etab_categorie )
                id_zone_privee          = get_id_course_by_id_number( mark, entete, "ZONE-PRIVEE-" + etablissement_siren )

                # Recreation de la zone privee si celle-ci n'existe plus
                if id_zone_privee is None:
                    id_zone_privee = insert_zone_privee( mark, entete, id_etab_categorie, etablissement_siren, etablissement_ou, maintenant_sql )

                id_context_course_forum = get_id_context( mark, entete, NIVEAU_CTX_COURS, 3, id_zone_privee  )
                if id_context_course_forum is None:
                    id_context_course_forum = insert_zone_privee_context( mark, entete, id_zone_privee )

            ####################################
            # Mise a jour des eleves 
            ####################################
            logging.info('    |_ Mise à jour des eleves')

            # Date du dernier traitement effectue
            time_stamp = timeStampByEtab.get( uai_etablissement.upper( ) )
            if purgeCohortes:
                # Si la purge des cohortes a ete demandee
                # On recupere tous les eleves sans prendre en compte le timestamp
                time_stamp = None

            # Recuperation du filtre ldap et recherche des eleves
            filtre          = get_filtre_eleves( time_stamp, uai_etablissement )
            logging.debug('      |_ Filtre LDAP pour récupérer les élèves : %s' % filtre)

            ldap_result_id  = ldap_search_student( l, personnes_dn, filtre ) 

            # Recuperation du resultat de la recherche
            result_set = ldap_retrieve_all_entries( l, ldap_result_id )

            # Dictionnaires permettant de sauvegarder les eleves inscrits
            # dans les cohortes, pour une eventuelle purge
            eleves_by_cohortes = { }

            # Traitement des eleves
            for ldap_entry in result_set :
                #  Recuperation des informations
                ldap_entry_infos        = ldap_entry[0][1]
                eleve_uid               = ldap_entry_infos['uid'][0]
                eleve_sn                = ldap_entry_infos['sn'][0].replace("'","\\'")
                eleve_given_name        = ldap_entry_infos['givenName'][0].replace("'","\\'")
                eleve_niveau_formation  = ldap_entry_infos['ENTEleveNivFormation'][0]
                eleve_infos             = "%s %s %s" % ( eleve_uid, eleve_given_name.decode( "utf-8" ), eleve_sn.decode( "utf-8" ) )
    
                # Recuperation du mail
                eleve_mail = DEFAULT_MAIL
                mail_display = DEFAULT_MAIL_DISPLAY
                if ldap_entry_infos.__contains__('mail'):
                    eleve_mail = ldap_entry_infos['mail'][0]

                # Recuperation des classes
                eleve_classe = None
                if ldap_entry_infos.__contains__('ENTEleveClasses'):
                    eleve_classes = extraireClassesLdap( ldap_entry_infos['ENTEleveClasses'] )
                    logging.debug("     |_ Les eleve_classes associees a l'eleve %s sont %s" % ( eleve_infos, str( eleve_classes ) ) )
                    if eleve_classes :
                        eleve_classe = eleve_classes[ 0 ]
        
                # Insertion de l'eleve
                eleve_id = get_user_id( mark, entete, eleve_uid )
                if not eleve_id:
                    insert_moodle_user( mark, entete, eleve_uid, eleve_given_name, eleve_sn, eleve_mail, mail_display, etablissement_theme )
                    eleve_id = get_user_id( mark, entete, eleve_uid )
                else:
                    update_moodle_user( mark, entete, eleve_id, eleve_given_name, eleve_sn, eleve_mail, mail_display, etablissement_theme )

                # Ajout du role d'utilisateur avec droits limites
                # Pour les eleves de college
                if etablissement_type_structure == TYPE_STRUCTURE_CLG :
                    add_role_to_user( mark, entete, ID_ROLE_UTILISATEUR_LIMITE, ID_INSTANCE_MOODLE, eleve_id )
                    logging.info( "      |_ Ajout du role d'utilisateur avec des droits limites à l'utilisateur %s %s %s (id = %s)" % ( eleve_given_name, eleve_sn, eleve_uid, str( eleve_id ) ) )

                # Inscription dans les cohortes associees aux classes
                eleve_cohorts = [ ]
                if eleve_classes :
                    ids_classes_cohorts = create_classes_cohorts( mark, entete, id_context_categorie, eleve_classes, maintenant_sql )
                    enroll_user_in_cohorts( mark, entete, id_context_categorie, ids_classes_cohorts, eleve_id, eleve_infos, maintenant_sql )
                    eleve_cohorts.extend( ids_classes_cohorts )

                # Inscription dans la cohorte associee au niveau de formation
                if eleve_niveau_formation :
                    id_formation_cohort = create_formation_cohort( mark, entete, id_context_categorie, eleve_niveau_formation, maintenant_sql )
                    enroll_user_in_cohort( mark, entete, id_formation_cohort, eleve_id, eleve_infos, maintenant_sql )
                    eleve_cohorts.append( id_formation_cohort )

                # Desinscription des anciennes cohortes
                disenroll_user_from_cohorts( mark, entete, eleve_cohorts, eleve_id )

                # Mise a jour des dictionnaires concernant les cohortes
                for cohort_id in eleve_cohorts:
                    # Si la cohorte est deja connue
                    if cohort_id in eleves_by_cohortes:
                        eleves_by_cohortes[ cohort_id ].append( eleve_id )
                    # Si la cohorte n'a pas encore ete rencontree
                    else:
                        eleves_by_cohortes[ cohort_id ] = [ eleve_id ]

                # Mise a jour de la classe
                id_user_info_data = get_id_user_info_data( mark, entete, eleve_id, id_user_info_field_classe )
                if id_user_info_data is not None:
                    update_user_info_data( mark, entete, eleve_id, id_user_info_field_classe, eleve_classe )
                    logging.debug("Mise à jour user_info_data")
                else:
                    insert_moodle_user_info_data( mark, entete, eleve_id, id_user_info_field_classe, eleve_classe )
                    logging.debug("Insertion user_info_data")
            
            # Purge des cohortes des eleves
            if purgeCohortes:
                logging.info('    |_ Purge des cohortes des élèves')
                purge_cohorts( mark, entete, eleves_by_cohortes )


            ####################################
            # Mise a jour des enseignants
            ####################################
            logging.info('    |_ Mise à jour du personnel enseignant')
            filtre = get_filtre_enseignants( timeStampByEtab.get( uai_etablissement.upper( ) ), uai_etablissement )
            logging.debug('      |_ Filtre LDAP pour récupérer les enseignants : %s' % filtre)

            ldap_result_id  = ldap_search_teacher( l, personnes_dn, filtre ) 

            # Recuperation du resultat de la recherche
            result_set = ldap_retrieve_all_entries( l, ldap_result_id )

            # Traitement des enseignants
            for ldap_entry in result_set :
                #  Recuperation des informations
                ldap_entry_infos                    = ldap_entry[0][1]
                enseignant_uid                      = ldap_entry_infos['uid'][0]
                enseignant_sn                       = ldap_entry_infos['sn'][0].replace("'","\\'")
                enseignant_given_name               = ldap_entry_infos['givenName'][0].replace("'","\\'")
                enseignant_structure_rattachement   = ldap_entry_infos['ENTPersonStructRattach'][0]
                enseignant_infos                    = "%s %s %s" % ( enseignant_uid, enseignant_given_name, enseignant_sn )

                # Recuperation des is_member_of
                enseignant_is_member_of = []
                if ldap_entry_infos.__contains__('isMemberOf'):
                    enseignant_is_member_of = ldap_entry_infos['isMemberOf']

                # Recuperation du theme courant
                if ldap_entry_infos.has_key('ESCOUAICourant') and not etablissement_regroupe:
                    etablissement_theme = ldap_entry_infos['ESCOUAICourant'][0].lower( )

                # Recuperation des profils
                enseignant_profils = [ ]
                if ldap_entry_infos.has_key('ENTPersonProfils'):
                    enseignant_profils = ldap_entry_infos['ENTPersonProfils']

                # Recuperation du mail
                mail = DEFAULT_MAIL
                if ldap_entry_infos.__contains__('mail'):
                    mail = ldap_entry_infos['mail'][0]

                # Affichage du mail reserve aux membres de cours
                mail_display = DEFAULT_MAIL_DISPLAY
                if etablissement_uai in listeEtabSansMail:
                    # Desactivation de l'affichage du mail
                    mail_display = 0

                
                # Insertion de l'enseignant
                id_user = get_user_id( mark, entete, enseignant_uid )
                if not id_user:
                    insert_moodle_user( mark, entete, enseignant_uid, enseignant_given_name, enseignant_sn, mail, mail_display, etablissement_theme )
                    id_user = get_user_id( mark, entete, enseignant_uid )
                else:
                    update_moodle_user( mark, entete, id_user, enseignant_given_name, enseignant_sn, mail, mail_display, etablissement_theme )

                # Mise ajour des droits sur les anciens etablissement
                if ldap_entry_infos.has_key('ESCOUAI') and not etablissement_regroupe:
                    # Recuperation des uais des etablissements dans lesquels l'enseignant est autorise
                    uais = ldap_entry_infos['ESCOUAI']
                    mettre_a_jour_droits_enseignant( mark, entete, enseignant_infos, gereAdminLocal, id_context_categorie, id_context_course_forum, id_user, uais )

                # Ajout du role de createur de cours au niveau de la categorie inter-etablissement Moodle
                add_role_to_user( mark, entete, ID_ROLE_CREATEUR_COURS, id_context_categorie_inter_etabs, id_user )
                logging.info( "        |_ Ajout du role de createur de cours dans la categorie inter-etablissements" )

                # Si l'enseignant fait partie d'un CFA
                # Ajout du role createur de cours au niveau de la categorie inter-cfa
                if etablissement_type_structure == TYPE_STRUCTURE_CFA :
                    add_role_to_user( mark, entete, ID_ROLE_CREATEUR_COURS, id_context_categorie_inter_cfa, id_user )
                    logging.info( "        |_ Ajout du role de createur de cours dans la categorie inter-cfa" )

                # ajout du role de createur de cours dans l'etablissement
                add_role_to_user( mark, entete, ID_ROLE_CREATEUR_COURS, id_context_categorie, id_user )

                # Ajouts des autres roles
                if 'National_3' in enseignant_profils   or 'National_5' in enseignant_profils or 'National_6' in enseignant_profils:
                    add_role_to_user( mark, entete, ID_ROLE_ELEVE, id_context_course_forum, id_user )
                    if not gereAdminLocal:
                        add_role_to_user( mark, entete, id_role_extended_teacher, id_context_categorie, id_user )
                elif 'National_4' in enseignant_profils:
                    add_role_to_user( mark, entete, ID_ROLE_DIRECTEUR, id_context_categorie, id_user )

                # Ajout des droits d'administration locale pour l'etablissement
                if gereAdminLocal:
                    desinscrit = False
                    inscrit = False
                    for member in enseignant_is_member_of:
                        # L'enseignant est il administrateur Moodle ?
                        adminMoodle = re.match( regexpAdminMoodle, member, flags=re.IGNORECASE )
                        if adminMoodle:
                            insert_moodle_local_admin( mark, entete, id_context_categorie, id_user )
                            logging.info("      |_ Insertion d'un admin Moodle local %s %s %s" % ( enseignant_uid, enseignant_given_name, enseignant_sn))
                            list_moodle_admin.append(id_user)
            
            ####################################
            # Mise a jour du time stamp pour
            # pour l'etablissement 
            ####################################
            timeStampByEtab[ uai_etablissement.upper( ) ] = timeStampNow

        ###################################################
        # Suppression du role d'administration locale aux 
        # utilisateurs ne faisant plus partie du groupe 
        # d'admin locale de moodle
        ###################################################
        if gereAdminLocal:
            # Suppression des droits d'admin local de Moodle
            list_moodle_admin.append( 0 )
            delete_moodle_local_admins( mark, entete, id_context_categorie, list_moodle_admin )

        connection.commit()

        ###################################################
        # Mise a jour du fichier contenant les informations
        # sur les traitements des etablissements
        ###################################################
        write_time_stamp_by_etab( timeStampByEtab, fileTrtPrecedent, fileSeparator )

        logging.info('Synchronisation établissements : FIN')
        logging.info('============================================')

    except StandardError, err:
        logging.exception("An exception has been thrown");
        logging.exception("Something went bad during the connection:\n", err)
        sys.exit(2)


    connection.close()


######################################################################
# Fonction permettant d'effectuer la mise a jour de la BD
# Moodle via les infos issues du LDAP
#
# Cette mise a jour concerne les utilisateurs et administrateurs
# inter-etablissements
#
# Parametres:
# -----------
#  - host     : hote hebergeant la BD moodle
#  - user     : utilisateur pour la connexion a la BD moodle
#  - password : mot de passe pour la connexion a la BD moodle
#  - nomBD    : nom de la BD moodle
#
#  - ldapServer   : hote hebergeant le serveur LDAP
#  - ldapUserName : utilisateur pour la connexion au LDAP
#  - ldapPassword : mot de passe pour la connexion au serveur LDAP
#
#  - structureDN : nom absolu pour acceder aux structures dans le LDAP
#  - personneDN  : nom absolu pour acceder aux personnes dans le LDAP
#
#  - entete : entete des noms de table dans la BD moodle
#
#  - ldap_attribut_user : attribut LDAP utilise pour savoir si un utilisateur
#                         est un utilisateur de l'inter-etablissements
#
#  - ldap_valeur_attribut_user : valeur de l'attribut LDAP permettant de savoir
#                                si un utilisateur est un utilisateur de
#                                l'inter-etablissements
#
#  - ldap_valeur_attribut_admin : valeur de l'attribut LDAP permettant de savoir
#                                 si un utilisateur est un administrateur de
#                                 l'inter-etablissements
#
#  - inter_etabs_cohorts : tableau associatif contenant comme cles
#                          les attributs 'isMemberOf' (permettant de
#                          recuperer les utilisateurs LDAP) et comme
#                          valeurs les noms des cohortes dans
#                          lesquelles injectees les utilisateurs trouves
#  - purgeCohortes    : booleen indiquant si la purge des cohortes
#                       doit etre effectuee, ou non
######################################################################
def miseAJourInterEtabsAll( host, user, password, nomBD, port, ldapServer, ldapUsername, ldapPassword, structures_dn, personnes_dn, entete, ldap_attribut_user, ldap_valeur_attribut_user, ldap_valeur_attribut_admin, inter_etabs_cohorts, fileTrtPrecedent, fileSeparator, purgeCohortes):
    # Connection BD
    connection, mark = connect_db( host, user, password, nomBD, port, 'utf8' )

    # ID du contexte pour la categorie inter etablissements regroupant tous les etablissements
    # CFA, Lycees, Colleges,...
    id_categorie_inter_etabs = get_id_categorie_inter_etabs( mark, entete )
    id_context_categorie_inter_etabs = get_id_context_categorie( mark, entete, id_categorie_inter_etabs )

    # Mise a jour
    logging.info('============================================')
    logging.info('Synchronisation inter-établissements (tous etablissements) : DEBUT')

    miseAJourInterEtabs( connection, mark, ldapServer, ldapUsername, ldapPassword, structures_dn, personnes_dn, entete, id_context_categorie_inter_etabs, ldap_attribut_user, ldap_valeur_attribut_user, ldap_valeur_attribut_admin, inter_etabs_cohorts, fileTrtPrecedent, fileSeparator, purgeCohortes)

    logging.info('Synchronisation inter-établissements (tous etablissements) : FIN')
    logging.info('============================================')

    # Fermeture connection
    connection.close( )

######################################################################
# Fonction permettant d'effectuer la mise a jour de la BD
# Moodle via les infos issues du LDAP
#
# Cette mise a jour concerne les utilisateurs et administrateurs
# inter-etablissements
#
# Parametres:
# -----------
#  - host     : hote hebergeant la BD moodle
#  - user     : utilisateur pour la connexion a la BD moodle
#  - password : mot de passe pour la connexion a la BD moodle
#  - nomBD    : nom de la BD moodle
#
#  - ldapServer   : hote hebergeant le serveur LDAP
#  - ldapUserName : utilisateur pour la connexion au LDAP
#  - ldapPassword : mot de passe pour la connexion au serveur LDAP
#
#  - structureDN : nom absolu pour acceder aux structures dans le LDAP
#  - personneDN  : nom absolu pour acceder aux personnes dans le LDAP
#
#  - entete : entete des noms de table dans la BD moodle
#
#  - ldap_attribut_user : attribut LDAP utilise pour savoir si un utilisateur
#                         est un utilisateur de l'inter-etablissements
#
#  - ldap_valeur_attribut_user : valeur de l'attribut LDAP permettant de savoir
#                                si un utilisateur est un utilisateur de
#                                l'inter-etablissements
#
#  - ldap_valeur_attribut_admin : valeur de l'attribut LDAP permettant de savoir
#                                 si un utilisateur est un administrateur de
#                                 l'inter-etablissements
#
#  - inter_etabs_cohorts : tableau associatif contenant comme cles
#                          les attributs 'isMemberOf' (permettant de
#                          recuperer les utilisateurs LDAP) et comme
#                          valeurs les noms des cohortes dans
#                          lesquelles injectees les utilisateurs trouves
#  - purgeCohortes    : booleen indiquant si la purge des cohortes
#                       doit etre effectuee, ou non
######################################################################
def miseAJourInterEtabsCFA( host, user, password, nomBD, port, ldapServer, ldapUsername, ldapPassword, structures_dn, personnes_dn, entete, ldap_attribut_user, ldap_valeur_attribut_user, ldap_valeur_attribut_admin, inter_etabs_cohorts, fileTrtPrecedent, fileSeparator, purgeCohortes):
    # Connection BD
    connection, mark = connect_db( host, user, password, nomBD, port, 'utf8' )

    # ID du contexte pour la categorie inter etablissements regroupant tous les etablissements
    # CFA, Lycees, Colleges,...
    id_categorie_inter_etabs = get_id_categorie_inter_etabs_cfa( mark, entete )
    id_context_categorie_inter_etabs = get_id_context_categorie( mark, entete, id_categorie_inter_etabs )

    # Mise a jour
    logging.info('============================================')
    logging.info('Synchronisation inter-cfa : DEBUT')

    miseAJourInterEtabs( connection, mark, ldapServer, ldapUsername, ldapPassword, structures_dn, personnes_dn, entete, id_context_categorie_inter_etabs, ldap_attribut_user, ldap_valeur_attribut_user, ldap_valeur_attribut_admin, inter_etabs_cohorts, fileTrtPrecedent, fileSeparator, purgeCohortes)

    logging.info('Synchronisation inter-cfa : FIN')
    logging.info('============================================')

    # Fermeture connection
    connection.close( )


######################################################################
# Fonction permettant d'effectuer la mise a jour de la BD
# Moodle via les infos issues du LDAP
#
# Cette mise a jour concerne les utilisateurs et administrateurs
# inter-etablissements
#
# Parametres:
# -----------
#  - connection   : connexion au serveur de BD
#  - mark         : pour les requestes en BD
#
#  - ldapServer   : hote hebergeant le serveur LDAP
#  - ldapUserName : utilisateur pour la connexion au LDAP
#  - ldapPassword : mot de passe pour la connexion au serveur LDAP
#
#  - structureDN : nom absolu pour acceder aux structures dans le LDAP
#  - personneDN  : nom absolu pour acceder aux personnes dans le LDAP
#
#  - entete : entete des noms de table dans la BD moodle
#  - id_context_categorie_inter_etabs : id du contexte de la categorie 
#                                       inter etablissements a traiter 
#
#  - ldap_attribut_user : attribut LDAP utilise pour savoir si un utilisateur
#                         est un utilisateur de l'inter-etablissements
#
#  - ldap_valeur_attribut_user : valeur de l'attribut LDAP permettant de savoir
#                                si un utilisateur est un utilisateur de
#                                l'inter-etablissements
#
#  - ldap_valeur_attribut_admin : valeur de l'attribut LDAP permettant de savoir
#                                 si un utilisateur est un administrateur de
#                                 l'inter-etablissements
#
#  - inter_etabs_cohorts : tableau associatif contenant comme cles
#                          les attributs 'isMemberOf' (permettant de
#                          recuperer les utilisateurs LDAP) et comme
#                          valeurs les noms des cohortes dans
#                          lesquelles injectees les utilisateurs trouves
#  - purgeCohortes    : booleen indiquant si la purge des cohortes
#                       doit etre effectuee, ou non
######################################################################
def miseAJourInterEtabs( connection, mark, ldapServer, ldapUsername, ldapPassword, structures_dn, personnes_dn, entete, id_context_categorie_inter_etabs, ldap_attribut_user, ldap_valeur_attribut_user, ldap_valeur_attribut_admin, inter_etabs_cohorts, fileTrtPrecedent, fileSeparator, purgeCohortes):
    try:
        logging.info("  |_ Traitement de l'inter-établissements")

        ###################################################
        # Connexion a la BD Moodle et recuperation 
        # d'informations
        ###################################################
        id_role_admin_local = get_id_role_admin_local( mark, entete )

        # Recuperation du timestamp actuel
        maintenant_sql = get_timestamp_now( mark )

        ###################################################
        # Connexion au LDAP
        ###################################################
        l = connect_ldap( ldapServer, ldapUsername, ldapPassword )
        
        ###################################################
        # Recuperation de la date de dernier traitement
        ###################################################
        time_stamp_by_etab  = read_time_stamp_by_etab( fileTrtPrecedent, fileSeparator )  
        time_stamp          = time_stamp_by_etab.get( CLE_TRT_INTER_ETAB )
        
        # Recuperation du time stamp actuel au format LDAP
        now             = datetime.datetime.now( )
        time_stamp_now  = format_date( now )

        ###################################################
        # Mise a jour des utilisateurs inter-etabs
        ###################################################
        logging.info('    |_ Mise à jour des utilisateurs inter-etablissements')

        list_moodle_admin = [ ]

        filtre          = get_filtre_personnes( time_stamp, ldap_attribut_user, ldap_valeur_attribut_user )
        logging.debug('      |_ Filtre LDAP pour récupérer les utilisateurs inter-établissements : %s' % filtre)
        ldap_result_id  = ldap_search_people( l, personnes_dn, filtre ) 

        # Recuperation du resultat de la recherche
        result_set = ldap_retrieve_all_entries( l, ldap_result_id )

        # Traitement des eleves
        for ldap_entry in result_set :
                #  Recuperation des informations
                ldap_entry_infos    = ldap_entry[0][1]
                people_uid          = ldap_entry_infos['uid'][0]
                people_sn           = ldap_entry_infos['sn'][0].replace("'","\\'")
                people_given_name   = ldap_entry_infos['givenName'][0].replace("'","\\'")

                people_is_member_of = [ ]
                if ldap_entry_infos.__contains__( ldap_attribut_user ):
                    people_is_member_of = ldap_entry_infos[ ldap_attribut_user ]

                people_mail = DEFAULT_MAIL
                if ldap_entry_infos.__contains__('mail'):
                    people_mail = ldap_entry_infos['mail'][0]

                # Creation de l'utilisateur
                id_user = get_user_id( mark, entete, people_uid )
                if not id_user:
                    insert_moodle_user( mark, entete, people_uid, people_given_name, people_sn, people_mail, DEFAULT_MAIL_DISPLAY, DEFAULT_MOODLE_THEME )
                    id_user = get_user_id( mark, entete, people_uid )
                else:
                    update_moodle_user( mark, entete, id_user, people_given_name, people_sn, people_mail, DEFAULT_MAIL_DISPLAY, DEFAULT_MOODLE_THEME )

                # Ajout du role de createur de cours 
                add_role_to_user( mark, entete, ID_ROLE_CREATEUR_COURS, id_context_categorie_inter_etabs, id_user )

                # Attribution du role admin local si necessaire
                for member in people_is_member_of:
                    admin = re.match( ldap_valeur_attribut_admin, member, flags=re.IGNORECASE )
                    if admin:
                        insert_moodle_local_admin( mark, entete, id_context_categorie_inter_etabs, id_user )
                        logging.info("      |_ Insertion d'un admin local %s %s %s" % ( people_uid, people_given_name, people_sn ) )
                        list_moodle_admin.append( id_user )
                        break

        delete_moodle_local_admins( mark, entete, id_context_categorie_inter_etabs, list_moodle_admin )

        ###################################################
        # Mise a jour des cohortes inter-etabs
        ###################################################
        logging.info('    |_ Mise à jour des cohortes de la categorie inter-etablissements')

        # Si la purge des cohortes a ete demandee
        if purgeCohortes:
            # On ignore le time stamp afin de traiter tous les utilisateurs
            time_stamp = None

        # Dictionnaires permettant de sauvegarder les eleves inscrits
        # dans les cohortes, pour une eventuelle purge
        utilisateurs_by_cohortes = { }

        # Mise a jour de chaque cohorte declaree
        for is_member_of, cohort_name in inter_etabs_cohorts.iteritems( ):
            # Creation de la cohort si necessaire
            create_cohort( mark, entete, id_context_categorie_inter_etabs, cohort_name, cohort_name, cohort_name, maintenant_sql )
            id_cohort = get_id_cohort( mark, entete, id_context_categorie_inter_etabs, cohort_name )

            # Liste permettant de sauvegarder les utilisateurs de la cohorte
            utilisateurs_by_cohortes[ id_cohort ] = [ ]

            # Recuperation des utilisateurs
            is_member_of_list   = [ is_member_of ]
            filtre              = get_filtre_personnes( time_stamp, "isMemberOf", is_member_of_list )
            logging.debug('      |_ Filtre LDAP pour récupérer les membres de cohortes inter-etablissements : %s' % filtre)

            ldap_result_id  = ldap_search_people( l, personnes_dn, filtre ) 
            result_set      = ldap_retrieve_all_entries( l, ldap_result_id )

            # Ajout des utilisateurs dans la cohorte
            for ldap_entry in result_set:
                ldap_entry_infos        = ldap_entry[0][1]
                people_uid              = ldap_entry_infos['uid'][0]
                people_sn               = ldap_entry_infos['sn'][0].replace("'","\\'")
                people_given_name       = ldap_entry_infos['givenName'][0].replace("'","\\'")
                people_infos            = "%s %s %s" % ( people_uid, people_given_name.decode( "utf-8" ), people_sn.decode( "utf-8" ) )

                people_id = get_user_id( mark, entete, people_uid )
                if people_id:
                    enroll_user_in_cohort( mark, entete, id_cohort, people_id, people_infos, maintenant_sql )
                    # Mise a jour des utilisateurs de la cohorte
                    utilisateurs_by_cohortes[ id_cohort ].append( people_id )
                else:
                    message = "      |_ Impossible d'inserer l'utilisateur %s dans la cohorte %s, car il n'est pas connu dans Moodle" 
                    message = message % ( people_infos, cohort_name )
                    logging.warn( message )

        # Purge des cohortes des eleves
        if purgeCohortes:
            logging.info('    |_ Purge des cohortes de la catégorie inter-établissements')
            purge_cohorts( mark, entete, utilisateurs_by_cohortes )
        
        connection.commit( )

        # Mise a jour de la date de dernier traitement
        time_stamp_by_etab[ CLE_TRT_INTER_ETAB  ] = time_stamp_now
        write_time_stamp_by_etab( time_stamp_by_etab, fileTrtPrecedent, fileSeparator )

    except StandardError, err:
        logging.exception("An exception has been thrown");
        logging.exception("Something went bad during the connection:\n", err)
        sys.exit(2)


######################################################################
# Fonction permettant d'effectuer la mise a jour de la BD
# Moodle via les infos issues du LDAP
#
# Cette mise a jour concerne les inspecteurs
#
# Parametres:
# -----------
#  - host     : hote hebergeant la BD moodle
#  - user     : utilisateur pour la connexion a la BD moodle
#  - password : mot de passe pour la connexion a la BD moodle
#  - nomBD    : nom de la BD moodle
#
#  - ldapServer   : hote hebergeant le serveur LDAP
#  - ldapUserName : utilisateur pour la connexion au LDAP
#  - ldapPassword : mot de passe pour la connexion au serveur LDAP
#
#  - personneDN  : nom absolu pour acceder aux personnes dans le LDAP
#
#  - entete : entete des noms de table dans la BD moodle
#
#  - ldap_attribut_user : attribut LDAP utilise pour savoir si un utilisateur
#                         est un inspecteur
#
#  - ldap_valeur_attribut_user : valeur de l'attribut LDAP permettant de savoir
#                                si un utilisateur est un inspecteur
#
######################################################################
def miseAJourInspecteurs( host, user, password, nomBD, port, ldapServer, ldapUsername, ldapPassword, personnes_dn, entete, ldap_attribut_user, ldap_valeur_attribut_user ):
    try:
        logging.info('============================================')
        logging.info('Synchronisation des inspecteurs : DEBUT')
        logging.info("  |_ Traitement des inspecteurs")

        ###################################################
        # Connexion a la BD Moodle et recuperation 
        # d'informations
        ###################################################
        connection, mark = connect_db( host, user, password, nomBD, port, 'utf8' )

        ###################################################
        # Connexion au LDAP
        ###################################################
        l = connect_ldap( ldapServer, ldapUsername, ldapPassword )
        
        ###################################################
        # Mise a jour des inspecteurs
        ###################################################
        logging.info('    |_ Mise à jour des inspecteurs')

        #TODO Time_stamp a gerer
        time_stamp = None

        filtre          = get_filtre_personnes( time_stamp, ldap_attribut_user, ldap_valeur_attribut_user )
        logging.debug('      |_ Filtre LDAP pour récupérer les inspecteurs : %s' % filtre)

        ldap_result_id  = ldap_search_people( l, personnes_dn, filtre ) 

        # Recuperation du resultat de la recherche
        result_set = ldap_retrieve_all_entries( l, ldap_result_id )

        # Traitement des inscpecteurs
        for ldap_entry in result_set :
                #  Recuperation des informations
                ldap_entry_infos    = ldap_entry[0][1]
                people_uid          = ldap_entry_infos['uid'][0]
                people_sn           = ldap_entry_infos['sn'][0].replace("'","\\'")
                people_given_name   = ldap_entry_infos['givenName'][0].replace("'","\\'")

                people_mail = DEFAULT_MAIL
                if ldap_entry_infos.__contains__('mail'):
                    people_mail = ldap_entry_infos['mail'][0]

                # Creation de l'utilisateur
                insert_moodle_user( mark, entete, people_uid, people_given_name, people_sn, people_mail, DEFAULT_MAIL_DISPLAY, DEFAULT_MOODLE_THEME )

        connection.commit( )

        logging.info('Synchronisation des inspecteurs : FIN')
        logging.info('============================================')

    except StandardError, err:
        logging.exception("An exception has been thrown");
        logging.exception("Something went bad during the connection:\n", err)
        sys.exit(2)

    connection.close( )


######################################################################
# Fonction permettant d'effectuer la mise a jour de la BD
# Moodle via les infos issues du LDAP
#
# Cette mise a jour concerne les utilisateurs de Mahara
#
# Parametres:
# -----------
#  - host     : hote hebergeant la BD moodle
#  - user     : utilisateur pour la connexion a la BD moodle
#  - password : mot de passe pour la connexion a la BD moodle
#  - nomBD    : nom de la BD moodle
#
#  - ldapServer   : hote hebergeant le serveur LDAP
#  - ldapUserName : utilisateur pour la connexion au LDAP
#  - ldapPassword : mot de passe pour la connexion au serveur LDAP
#
#  - personnesDN  : nom absolu pour acceder aux personnes dans le LDAP
#
#  - entete : entete des noms de table dans la BD moodle
#
#  - ldap_attribut_user : attribut LDAP utilise pour savoir si un utilisateur
#                         est un utilisateur de Mahara
#
#  - ldap_valeur_attribut_user : valeur de l'attribut LDAP permettant de savoir
#                                si un utilisateur est un utilisateur de Mahara
#  - purge            : booleen indiquant si la purge des utilisateurs
#                       doit etre effectuee, ou non
######################################################################
def miseAJourMahara( host, user, password, nomBD, port, ldapServer, ldapUsername, ldapPassword, personnesDN, entete, maharaAttribut, maharaUser, fileTrtPrecedentMahara, fileSeparatorMahara, purge ):
    try:
        logging.info('============================================')
        logging.info('Synchronisation des utilisateurs Mahara : DEBUT')
        logging.info("  |_ Traitement des utilisateurs Mahara")

        ###################################################
        # Connexion a la BD Moodle et recuperation 
        # d'informations
        ###################################################
        connection, mark = connect_db( host, user, password, nomBD, port, 'utf8' )

        ###################################################
        # Connexion au LDAP
        ###################################################
        l = connect_ldap( ldapServer, ldapUsername, ldapPassword )
        
        ###################################################
        # Recuperation de la date de dernier traitement
        ###################################################
        time_stamp_by_etab  = read_time_stamp_by_etab( fileTrtPrecedentMahara, fileSeparatorMahara )  
        time_stamp          = time_stamp_by_etab.get( CLE_TRT_MAHARA )
        
        # Recuperation du time stamp actuel au format LDAP
        now             = datetime.datetime.now( )
        time_stamp_now  = format_date( now )

        ###################################################
        # Purge des utilisateurs de Mahara
        ###################################################
        # Si la purge a ete demandee
        if purge:
            # On ignore le time stamp afin de traiter tous les utilisateurs
            time_stamp = None
            # On enleve les roles aux utilisateurs de Mahara
            delete_all_mahara_roles( mark, entete )


        ###################################################
        # Mise a jour des utilisateurs
        ###################################################
        logging.info('    |_ Mise à jour des utilisateurs Mahara')

        filtre          = get_filtre_personnes( time_stamp, maharaAttribut, maharaUser )
        logging.debug('      |_ Filtre LDAP pour récupérer les utilisateurs Mahara : %s' % filtre)

        ldap_result_id  = ldap_search_people( l, personnesDN, filtre ) 

        # Recuperation du resultat de la recherche
        result_set = ldap_retrieve_all_entries( l, ldap_result_id )

        # Traitement des inscpecteurs
        for ldap_entry in result_set :
                #  Recuperation des informations
                ldap_entry_infos    = ldap_entry[0][1]
                people_uid          = ldap_entry_infos['uid'][0]
                people_sn           = ldap_entry_infos['sn'][0].replace("'","\\'")
                people_given_name   = ldap_entry_infos['givenName'][0].replace("'","\\'")
                people_infos        = "%s %s %s" % ( people_uid, people_given_name.decode( "utf-8" ), people_sn.decode( "utf-8" ) )

                # Recuperation de l'utilisateur en bd
                people_id = get_user_id( mark, entete, people_uid )
                
                # Si l'utilisateur n'est pas present dans Moodle
                if not people_id:
                    message = "      |_ Impossible de donner les droits sur Mahara a %s, car il n'est pas connu dans Moodle" 
                    message = message % people_infos
                    logging.warn( message )
                    continue

                # Si l'utilisateur est present dans Moodle
                message = "      |_ Ajout du droit utilisateur de Mahara a %s" 
                message = message % people_infos
                logging.info( message )
                add_role_mahara_to_user( mark, entete, people_id )

        connection.commit( )

        # Mise a jour de la date de dernier traitement
        time_stamp_by_etab[ CLE_TRT_MAHARA  ] = time_stamp_now
        write_time_stamp_by_etab( time_stamp_by_etab, fileTrtPrecedentMahara, fileSeparatorMahara )

        logging.info('Synchronisation des utilisateurs Mahara : FIN')
        logging.info('============================================')

    except StandardError, err:
        logging.exception("An exception has been thrown");
        logging.exception("Something went bad during the connection:\n", err)
        sys.exit(2)

    connection.close( )


#######################################
# Partie permettant de tester
#######################################
if __name__ == "__main__":
  # Tests sur les dates
  now = datetime.datetime.now( )
  logging.info("Test | Date actuelle : %s" % now)
  logging.info("Test | Meme date au format LDAP (AAAAMMJJHHMMSS + la lettre Z) : %s" % format_date( now ) )
  logging.info('')
 
  # Tests sur la lecture des uai_etablissement et time stamp stockes dans un fichier
  timeStampByEtab = read_time_stamp_by_etab( './test/trtPrecedentLectureTest.txt', '-' )
  logging.info("Test | Tableau associatif issu du fichier test/trtPrecedentLectureTest.txt : %s" % timeStampByEtab  )
  for key, value in timeStampByEtab.iteritems( ):
      logging.info("     |_ Etablissement %s traite pour la derniere fois le %s" % ( key, value ))
  logging.info('')

  # Tests sur l'ecriture des uai_etablissement et time stamp
  timeStampByEtab = { '0180345B':'20121201131332Z', '0410254R':'20100310132456Z' }
  logging.info("Test | Ecriture du tableau associtaif dans test/trtPrecedentEritureTest.txt")
  logging.info("     |_ Contenu prevu : %s" % timeStampByEtab)
  write_time_stamp_by_etab( timeStampByEtab, './test/trtPrecedentEcritureTest.txt', '-' )
  timeStampByEtab = read_time_stamp_by_etab( './test/trtPrecedentEcritureTest.txt', '-' )
  logging.info("     |_ Contenu reel : %s" % timeStampByEtab)
  logging.info("")

  # Test sur les filtres
  filtreEtab = 'ESCOUAI=0180345B'
  logging.info('Test | Filtre pour les eleves du 0180345B (avec time stamp) : %s' % get_filtre_eleves( timeStampByEtab.get( '0180345B' ), filtreEtab ))
  logging.info('Test | Filtre pour les eleves du 0180345B (sans time stamp) : %s' % get_filtre_eleves( timeStampByEtab.get( '01803B' ), filtreEtab ))
  logging.info('')

  filtreEtab = 'ESCOUAI=0180345B'
  logging.info('Test | Filtre pour les enseignants du 0180345B (avec time stamp) :  %s' % get_filtre_enseignants( timeStampByEtab.get( '0180345B' ), filtreEtab ))
  logging.info('Test | Filtre pour les enseignants du 0180345B (sans time stamp) :  %s' % get_filtre_enseignants( timeStampByEtab.get( '01803B' ), filtreEtab ))
  logging.info('')
