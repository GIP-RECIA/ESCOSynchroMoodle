#!/usr/bin/env python3
# coding: utf-8
"""
Entrypoint
"""

import logging
import sys
from argparse import ArgumentParser

from synchromoodle import actions
from synchromoodle.config import ConfigLoader

logging.basicConfig(format="%(levelname)s:%(message)s", stream=sys.stdout, level=logging.INFO)


def main():
    """
    Main function
    """
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", action="append", dest="config", default=[],
                        help="Chemin vers un fichier de configuration.")
    parser.add_argument("--purge-cohortes", action="store_true", dest="purge_cohortes", default=False,
                        help="Active la purge des cohortes.")

    arguments = parser.parse_args()

    config_loader = ConfigLoader()
    config = config_loader.load(['config.yml', 'config.yaml'], True)

    config = config_loader.update(config, arguments.config)

    for action in config.actions:
        try:
            action_func = getattr(actions, action)
        except AttributeError:
            logging.error("Action invalide: %s", action)
            continue
        action_func(config, arguments)


if __name__ == "__main__":
    main()
