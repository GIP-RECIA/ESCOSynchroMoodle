"""
Gestion des timestamps
"""

import datetime
import os
import re
from logging import getLogger
from typing import Dict

from synchromoodle.config import TimestampStoreConfig

log = getLogger('timestamp')

def fromisoformat(iso: str, modify_timestamp_delay: int) -> datetime.datetime:
    """
    Parse Datetime ISO Format.
    Décale de modify_timestamp_delay heures dans le passé.
    :param iso: Le timestamp sous forme d'une chaine de caractères
    :param modify_timestamp_delay: Le décalage en heures
    :return: Le timestamp sous forme d'un timestamp Python
    """
    # Récupération des données en entrée
    timestamp_etab = datetime.datetime(*map(int, re.split(r'[^\d]', iso)))
    timestamp_decalage = datetime.timedelta(hours=modify_timestamp_delay)
    # Calcul du nouveau timestamp après décalage
    timestamp_etab -= timestamp_decalage
    return timestamp_etab


class TimestampStore:
    """
    Stocker les timestamp de dernière modification pour les établissements.
    Permet de ne traiter que les utilisateurs ayant subi une modification depuis le dernier traitement.
    Prends une marge de sécurité de modify_timestamp_delay heures si il y a des problèmes de syncho ldap.
    """

    def __init__(self, config: TimestampStoreConfig, modify_timestamp_delay: int = 0, now: datetime.datetime = None):
        self.config = config
        self.now = now if now else datetime.datetime.now()
        self.timestamps = {}  # type: Dict[str, datetime.datetime]
        self.modify_timestamp_delay = modify_timestamp_delay
        self.read()

    def get_timestamp(self, uai: str) -> datetime.datetime:
        """
        Obtient le timestamp d'un établissement
        :param uai: code établissement
        :return: timestamp
        """
        return self.timestamps.get(uai.upper())

    def read(self):
        """
        Charge le fichier contenant la date des derniers traitement
        """
        self.timestamps.clear()

        try:
            with open(self.config.file, 'r', encoding="utf-8") as time_stamp_file:
                for line in time_stamp_file.readlines():
                    line = line.strip(os.linesep)
                    if line:
                        etab_and_time = line.split(self.config.separator, 1)
                        etab = etab_and_time[0]
                        time_stamp = etab_and_time[1]
                        self.timestamps[etab] = fromisoformat(time_stamp, self.modify_timestamp_delay)
        except IOError:
            log.warning("Impossible d'ouvrir le fichier : %s", self.config.file)

    def write(self):
        """
        Ecrit le fichier contenant la date de derniers traitement des établissements.
        """

        with open(self.config.file, 'w', encoding="utf-8") as time_stamp_file:
            time_stamp_file.writelines(
                map(lambda item: item[0].upper() + self.config.separator + item[1].isoformat() + os.linesep,
                    self.timestamps.items()))

    def mark(self, uai: str):
        """
        Ajoute le timestamp courant pour l'établissement donné.
        :param uai: code établissement
        """
        self.timestamps[uai.upper()] = self.now
