#!/usr/bin/env python3
# coding: utf-8
"""
Entrypoint
"""

from logging import getLogger, basicConfig
from logging.config import dictConfig

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
    if config.logging is not False:
        if isinstance(config.logging, dict):
            if config.logging.pop('basic', None):
                basicConfig(**config.logging)
            else:
                if 'version' not in config.logging:
                    config.logging['version'] = 1
                dictConfig(config.logging)
        elif isinstance(config.logging, str):
            basicConfig(level=config.logging)
        else:
            basicConfig(level='INFO')

    log = getLogger()
    log.info("Démarrage")

    for action in config.actions:
        try:
            action_func = getattr(actions, action.type)
        except AttributeError:
            log.error("Action invalide: %s", action)
            continue
        log.info("Démarrage de l'action %s", action)
        try:
            action_func(config, action, arguments)
        except Exception:  # pylint: disable=broad-except
            log.exception("Une erreur inattendue s'est produite")
        log.info("Fin de l'action %s", action)

    log.info("Terminé")


if __name__ == "__main__":
    main()
