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
        # pylint is not that smart with union type conditional inference
        # pylint: disable=no-member,not-a-mapping,unsupported-membership-test,unsupported-assignment-operation
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

    try:
        config.validate()
    except ValueError as e:
        log.error(e)
        exit(1)

    log.info("Démarrage")

    errors = 0

    for action in config.actions:
        try:
            action_func = getattr(actions, action.type)
        except AttributeError:
            errors += 1
            log.error("Action invalide: %s", action)
            continue
        log.info("Démarrage de l'action %s", action)
        try:
            action_func(config, action, arguments)
        except Exception:  # pylint: disable=broad-except
            errors += 1
            log.exception("Une erreur inattendue s'est produite")
        log.info("Fin de l'action %s", action)

    log.info("Terminé")
    if errors:
        exit(errors)


if __name__ == "__main__":
    main()
