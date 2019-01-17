#!/usr/bin/env python3
# coding: utf-8

import logging
import sys

from synchromoodle.config import ConfigLoader
from synchromoodle.miseAJourTrt import miseAJour

logging.basicConfig(format="%(levelname)s:%(message)s", stream=sys.stdout, level=logging.INFO)

from optparse import OptionParser

if __name__ == "__main__":
    config = ConfigLoader().load()

    parser = OptionParser()
    parser.add_option("-p", "--purge-cohortes", action="store_true", dest="purge_cohortes", default=False,
                      help="Purge les cohortes")

    options, _ = parser.parse_args()

    miseAJour(config, options.purge_cohortes)
