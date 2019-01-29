# coding: utf-8
import datetime
import os
import time

import pytest

from synchromoodle.config import Config
from synchromoodle.dbutils import Database
from synchromoodle.ldaputils import Ldap

pytest_plugins = ["docker"]


@pytest.fixture(scope='session')
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), '..', 'docker-compose.pytest.yml')


@pytest.fixture(scope='session')
def docker_compose_subprocess_kwargs():
    return {'cwd': '..'}


@pytest.fixture(scope="session", name="config")
def config():
    config = Config()
    return config


@pytest.fixture(scope="session", name="docker_config")
def docker_config(config, docker_ip, docker_services):
    """
    Configure l'application pour se connecter au container de test.

    S'assure également que les containers sont disponibles.

    :param config: 
    :param docker_ip: 
    :param docker_services: 
    :return: 
    """
    docker_config = Config()
    docker_config.update(config.__dict__)
    """"
    raw_data = get_data(__package__,
                        os.path.join('config', os.environ.get('SYNCHROMOODLE_TEST_CONFIG', 'docker-vagrant.yml')))
    data = yaml.safe_load(raw_data)
    config.update(data)
    """
    docker_config.database.host = docker_ip
    docker_config.database.port = docker_services.port_for('moodle-db-test', 3306)

    docker_config.ldap.uri = "ldap://%s:%s" % (docker_ip, docker_services.port_for('ldap-test', 389))

    now = datetime.datetime.now()
    timeout = 60

    # Ensure ldap is available
    ldap = Ldap(docker_config.ldap)
    while True:
        try:
            ldap.connect()
        except Exception as e:
            time.sleep(1)
            if (datetime.datetime.now() - now).seconds > timeout:
                raise e
            continue
        ldap.disconnect()
        break

    # Ensure database is available
    db = Database(docker_config.database, docker_config.constantes)
    while True:
        try:
            db.connect()
        except Exception as e:
            time.sleep(1)
            if (datetime.datetime.now() - now).seconds > timeout:
                raise e
            continue
        db.disconnect()
        break

    return config
