# coding: utf-8

import os
from pkgutil import get_data

import pytest
from ruamel import yaml

from synchromoodle.config import Config


@pytest.fixture(scope="session", name="config")
def config():
    config = Config()
    raw_data = get_data(__package__, os.path.join('config', os.environ.get('SYNCHROMOODLE_TEST_CONFIG', 'docker-vagrant.yml')))
    data = yaml.safe_load(raw_data)
    config.update(data)
    return config

