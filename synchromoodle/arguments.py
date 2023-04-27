"""
Module permettant le parsing des arguments sur la ligne de commande
"""

from argparse import ArgumentParser

from synchromoodle.__version__ import __version__


def parse_args(args=None, namespace=None):
    """
    Parse les arguments donnés sur la ligne de commande.
    """
    parser = ArgumentParser(description="Scrit de synchronisation de moodle depuis l'annuaire LDAP.")
    parser.add_argument("-v", "--version", action="version", version='%(prog)s ' + __version__)
    parser.add_argument("-c", "--config", action="append", dest="config", default=[],
                        help="Chemin vers un fichier de configuration. Lorsque cette option est utilisée plusieurs "
                             "fois, les fichiers de configuration sont alors fusionnés.")

    arguments = parser.parse_args(args, namespace)
    return arguments


DEFAULT_ARGS = parse_args([])
