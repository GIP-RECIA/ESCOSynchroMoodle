# -*- coding: utf-8 -*-

###############################################################################
# IMPORTS
###############################################################################
import getopt
import logging
import sys
logging.basicConfig(format='%(levelname)s:%(message)s', stream=sys.stdout, level=logging.INFO)

###############################################################################
# FONCTIONS
###############################################################################

#######################################
# Fonction pour la synchronisation
#######################################
def purge_demandee( argv ):
    try:
        opts, args = getopt.getopt( argv, "", [ "purge" ] )
    except getopt.GetoptError:
        logging.warning("      |_ Certaines options de lancement ne sont pas reconnues" )
        logging.warning("      |_ Les seules options valides sont : '--purge'" )
        sys.exit( 2 )
    purge = False
    for opt, arg in opts:
        if opt == "--purge":
            purge = True
    # Purge des cohortes demandee ?
    if purge:
        logging.info("      |_ La purge des cohortes et utilisateurs Mahara va être effectuée" )
    else:
        logging.info("      |_ La purge ne va pas être effectuée" )
    return purge
