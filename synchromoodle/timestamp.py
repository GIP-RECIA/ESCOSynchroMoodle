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

def fromisoformat(iso: str) -> datetime.datetime:
    """
    Parse Datetime ISO Format
    :param iso:
    :return:
    """
    return datetime.datetime(*map(int, re.split(r'[^\d]', iso)))


class TimestampStore:
    """
    Stocker les timestamp de dernière modification pour les établissements.
    Permet de ne traiter que les utilisateurs ayant subi une modification depuis le dernier traitement.
    """

    def __init__(self, config: TimestampStoreConfig, now: datetime.datetime = None):
        self.config = config
        self.now = now if now else datetime.datetime.now()
        self.timestamps = {}  # type: Dict[str, datetime.datetime]
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
                        self.timestamps[etab] = fromisoformat(time_stamp)
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
