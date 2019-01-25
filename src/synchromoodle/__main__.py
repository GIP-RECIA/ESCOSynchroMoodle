#!/usr/bin/env python3
# coding: utf-8

import logging
import sys
from optparse import OptionParser

from synchromoodle import actions
from synchromoodle.config import ConfigLoader

logging.basicConfig(format="%(levelname)s:%(message)s", stream=sys.stdout, level=logging.INFO)


def main():
    parser = OptionParser()
    parser.add_option("-c", "--config", action="append", dest="config", default=[],
                      help="Chemin vers un fichier de configuration.")
    parser.add_option("--purge-cohortes", action="store_true", dest="purge_cohortes", default=False,
                      help="Active la purge des cohortes.")

    options, _ = parser.parse_args()

    config_loader = ConfigLoader()
    config = config_loader.load(['config.yml', 'config.yaml'], True)

    config = config_loader.update(config, options.config)

    for action in config.actions:
        try:
            action_func = getattr(actions, action)
        except AttributeError:
            logging.error("Action invalide: %s" % action)
            continue
        action_func(config, options)


if __name__ == "__main__":
    main()
