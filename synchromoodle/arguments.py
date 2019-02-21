from argparse import ArgumentParser


def parse_args(args=None, namespace=None):
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", action="append", dest="config", default=[],
                        help="Chemin vers un fichier de configuration. Lorsque cette option est utilisée plusieurs "
                             "fois, les fichiers de configuration sont alors fusionnés.")

    arguments = parser.parse_args(args, namespace)
    return arguments


default_args = parse_args([])
