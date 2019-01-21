import datetime
import logging


class TimestampStore:
    """
    Stocker les timestamp de dernière modification pour les établissements.

    Permet de ne traiter que les utilisateurs ayant subi une modification depuis le dernier traitement
    """

    def __init__(self, file_location: str, separator='-'):
        self.file_location = file_location
        self.separator = separator
        self.now = datetime.datetime.now()
        self.timestamps = {}
        self.read()

    @property
    def current_timestamp(self):
        return self.format_date(self.now)

    def get_timestamp(self, uai: str):
        return self.timestamps.get(uai.upper())

    def format_date(self, date: datetime.datetime):
        """
        Formate une date au format LDAP.

        :param date: Date à formatter
        :return: Date formatée
        """
        return date.strftime('%Y%m%d%H%M%S') + 'Z'

    def read(self):
        """
        Recupère la dernière date de traitement pour chaque établissement.
        :param file_location: 
        :param separator: 
        :return: 
        """
        self.timestamps.clear()

        try:
            with open(self.file_location, 'r') as time_stamp_file:
                for line in time_stamp_file:
                    etab_and_time = line.split(self.separator)
                    etab = etab_and_time[0]
                    time_stamp = etab_and_time[1]
                    self.timestamps[etab] = time_stamp[:-1]
        except IOError:
            logging.warning("Impossible d'ouvrir le fichier : %s" % self.file_location)
            return {}

    def write(self):
        """
        Ecrit le fichier contenant les informations sur les établissements et leur dernière date de traitement.

        Exemple de contenu de fichier:
        045678A-20110101121345Z
        036783R-20121101121354Z
        018654B-20110405134523Z
        :param time_stamp_by_etab: 
        :param file_location: 
        :param separator: 
        :return: 
        """

        with open(self.file_location, 'w') as time_stamp_file:
            time_stamp_file.writelines(
                map(lambda item: item[0].upper() + self.separator + item[1], self.timestamps.items()))

    def mark(self, uai):
        self.timestamps[uai.upper()] = self.current_timestamp
