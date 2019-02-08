#!/usr/bin/env python3
# coding: utf-8
"""
Entrypoint
"""

import logging
import sys

from synchromoodle import actions
from synchromoodle.arguments import parse_args
from synchromoodle.config import ConfigLoader


def main():
    """
    Main function
    """
    arguments = parse_args()

    config_loader = ConfigLoader()
    config = config_loader.load(['config.yml', 'config.yaml'], True)

    config = config_loader.update(config, arguments.config)

    # TODO: Rendre le logger configurable, et ajouter un handler par logger (établissement, élève, enseignant)
    logging.basicConfig(format="%(levelname)s:%(message)s", stream=sys.stdout, level=logging.DEBUG)

    for action in config.actions:
        try:
            action_func = getattr(actions, action)
        except AttributeError:
            logging.error("Action invalide: %s", action)
            continue
        logging.info('Démarrage de l\'action "%s"' % action)
        try:
            action_func(config, arguments)
        except Exception as e:
            logging.exception("Une erreur inattendue s'est produite")
        logging.info('Fin de l\'action "%s"' % action)


if __name__ == "__main__":
    main()
