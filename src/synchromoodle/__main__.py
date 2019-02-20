#!/usr/bin/env python3
# coding: utf-8
"""
Entrypoint
"""

from logging import getLogger
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
    log = getLogger()

    for action in config.actions:
        try:
            action_func = getattr(actions, action.type)
        except AttributeError:
            log.error("Action invalide: %s", action)
            continue
        log.info('Démarrage de l\'action "%s"' % action)
        try:
            action_func(config, action, arguments)
        except Exception as e:
            log.exception("Une erreur inattendue s'est produite")
        log.info('Fin de l\'action "%s"' % action)


if __name__ == "__main__":
    main()
