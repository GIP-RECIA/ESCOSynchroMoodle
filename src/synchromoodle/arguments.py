from argparse import ArgumentParser


def parse_args(args=None, namespace=None):
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", action="append", dest="config", default=[],
                        help="Chemin vers un fichier de configuration.")
    parser.add_argument("--purge-cohortes", action="store_true", dest="purge_cohortes", default=False,
                        help="Active la purge des cohortes.")

    arguments = parser.parse_args(args, namespace)
    return arguments


default_args = parse_args([])
