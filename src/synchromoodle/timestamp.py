"""
Gestion des timestamps
"""

import datetime
import logging

from synchromoodle.config import TimestampStoreConfig


def format_date(date: datetime.datetime):
    """
    Formate une date au format LDAP.

    :param date: Date à formatter
    :return: Date formatée
    """
    return date.strftime('%Y%m%d%H%M%S') + 'Z'


class TimestampStore:
    """
    Stocker les timestamp de dernière modification pour les établissements.

    Permet de ne traiter que les utilisateurs ayant subi une modification depuis le dernier traitement.

    Exemple de contenu de fichier:
    045678A-20110101121345Z
    036783R-20121101121354Z
    018654B-20110405134523Z
    """

    def __init__(self, config: TimestampStoreConfig):
        self.config = config
        self.now = datetime.datetime.now()
        self.timestamps = {}
        self.read()

    @property
    def current_timestamp(self):
        """
        Timestamp courant.
        :return: Le timestamp courant
        """
        return format_date(self.now)

    def get_timestamp(self, uai: str):
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
            with open(self.config.file, 'r') as time_stamp_file:
                for line in time_stamp_file:
                    etab_and_time = line.split(self.config.separator)
                    etab = etab_and_time[0]
                    time_stamp = etab_and_time[1]
                    self.timestamps[etab] = time_stamp[:-1]
        except IOError:
            logging.warning("Impossible d'ouvrir le fichier : %s" % self.config.file)
            return {}

    def write(self):
        """
        Ecrit le fichier contenant la date de derniers traitement des établissements.
        """

        with open(self.config.file, 'w') as time_stamp_file:
            time_stamp_file.writelines(
                map(lambda item: item[0].upper() + self.config.separator + item[1], self.timestamps.items()))

    def mark(self, uai: str):
        """
        Ajoute le timestamp courant pour l'établissement donné.
        :param uai: code établissement
        """
        self.timestamps[uai.upper()] = self.current_timestamp
