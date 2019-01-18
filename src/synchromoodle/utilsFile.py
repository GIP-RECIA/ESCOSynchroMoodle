# coding: utf-8

import logging


###########################################################
# Fonction permettant de recuperer les etablissements et 
# la derniere date de traitement associee a ces derniers
###########################################################
def read_time_stamp_by_etab(file_location, separator):
    # Tableau stockant l'association etab - time_stamp
    time_stamp_by_etab = {}

    # Recuperation des etab associes a leur time stamp
    try:
        time_stamp_file = open(file_location, 'r')
        for line in time_stamp_file:
            etab_and_time = line.split(separator)
            etab = etab_and_time[0]
            time_stamp = etab_and_time[1]
            time_stamp_by_etab[etab] = time_stamp[:-1]
        time_stamp_file.close()
        return time_stamp_by_etab
    except IOError:
        logging.warning("Impossible d'ouvrir le fichier : %s" % (file_location))
        return {}


###########################################################
# Fonction permettant d'ecrire le fichier contenant les 
# infos sur les etablissements et leur derniere date
# de traitement
#
# Exemple de contenu de fichier:
#   045678A-20110101121345Z        
#   036783R-20121101121354Z        
#   018654B-20110405134523Z        
###########################################################
def write_time_stamp_by_etab(time_stamp_by_etab, file_location, separator):
    # Ecriture des etablissements associes au time stamp
    time_stamp_file = open(file_location, 'w')
    for key, value in time_stamp_by_etab.items():
        time_stamp_file.write(key + separator + value + '\n')
    time_stamp_file.close()
