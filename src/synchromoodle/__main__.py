#!/usr/bin/env python3
# coding: utf-8

import logging
import sys

from synchromoodle.config import ConfigLoader
from synchromoodle.miseAJourTrt import miseAJour, miseAJourInterEtabs, miseAJourInspecteurs

logging.basicConfig(format="%(levelname)s:%(message)s", stream=sys.stdout, level=logging.INFO)

from optparse import OptionParser


def main():
    parser = OptionParser()
    parser.add_option("-c", "--config", action="append", dest="config", default=[],
                      help="Chemin vers un fichier de configuration.")
    parser.add_option("-p", "--purge", action="store_true", dest="purge", default=False,
                      help="Active la purge.")

    options, _ = parser.parse_args()

    config_loader = ConfigLoader()
    config = config_loader.load(['config.yml', 'config.yaml'], True)

    config = config_loader.update(config, options.config)

    for action in config.actions:
        if action == 'default':
            miseAJour(config, options.purge)
        if action == 'interetab':
            miseAJourInterEtabs(config, options.purge)
        if action == 'inspecteurs':
            miseAJourInspecteurs(config)


if __name__ == "__main__":
    main()
