# coding: utf-8
import datetime
import json
import os
import time

import pytest
import pytest_docker

from synchromoodle.config import Config, ActionConfig
from synchromoodle.dbutils import Database
from synchromoodle.ldaputils import Ldap

pytest_plugins = ["docker"]


@pytest.fixture(scope='session')
def docker_compose_file(pytestconfig):
    """Retourne le chemin vers le fichier de configuration pour les containers docker."""
    return os.path.join(str(pytestconfig.rootdir), 'docker-compose.pytest.yml')


@pytest.fixture(scope='session')
def docker_compose_subprocess_kwargs():
    return {}


@pytest.fixture(scope="session")
def action_config() -> ActionConfig:
    """
    Créée une configuration d'action avec les valeurs de base.

    :returns: La configuration créée
    """
    action_config = ActionConfig()
    return action_config


@pytest.fixture(scope="session")
def config(action_config: ActionConfig) -> Config:
    """
    Charge la configuration de base pour la session de tests.

    :param action_config: Une configuration d'action
    :returns: La configuration globale
    """
    config = Config()
    config.actions.append(action_config)
    return config

@pytest.fixture(scope="session", name="docker_config")
def docker_config(config: Config, docker_ip: str, docker_services: pytest_docker.plugin.Services) -> Config:
    """
    Configure l'application pour se connecter au container de test.
    S'assure également que les containers sont disponibles.

    :param config: La configuration de base pour la session de tests
    :param docker_ip: L'ip utilisé pour les containers docker
    :param docker_services: Les services docker
    :returns: La configuration pour la session de tests mise à jour
    """
    docker_config = Config()
    docker_config.update(**json.loads(json.dumps(config, default=lambda o: getattr(o, '__dict__', str(o)))))

    docker_config.database.host = docker_ip

    now = datetime.datetime.now()
    timeout = 60

    while True:
        docker_config.ldap.uri = f"ldap://{docker_ip}:{docker_services.port_for('ldap-test', 389)}"
        # Ensure ldap is available
        ldap = Ldap(docker_config.ldap)

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
    while True:
        docker_config.database.port = docker_services.port_for('moodle-db-test', 3306)
        db = Database(docker_config.database, docker_config.constantes)

        try:
            db.connect()
        except Exception as e:
            time.sleep(1)
            docker_config.database.host = docker_ip
            docker_config.database.port = docker_services.port_for('moodle-db-test', 3306)
            if (datetime.datetime.now() - now).seconds > timeout:
                raise e
            continue
        db.disconnect()
        break

    return docker_config
