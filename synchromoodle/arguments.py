"""
Arguments
"""

from synchromoodle.__version__ import __version__
from argparse import ArgumentParser


def parse_args(args=None, namespace=None):
    """
    Parse arguments
    :param args:
    :param namespace:
    :return:
    """
    parser = ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version='%(prog)s ' + __version__)
    parser.add_argument("-c", "--config", action="append", dest="config", default=[],
                        help="Chemin vers un fichier de configuration. Lorsque cette option est utilisée plusieurs "
                             "fois, les fichiers de configuration sont alors fusionnés.")

    arguments = parser.parse_args(args, namespace)
    return arguments


DEFAULT_ARGS = parse_args([])
