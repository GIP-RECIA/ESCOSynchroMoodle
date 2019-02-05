# coding: utf-8

import pytest

from synchromoodle.config import Config
from synchromoodle.dbutils import Database
from synchromoodle.ldaputils import Ldap
from synchromoodle.synchronizer import Synchronizer
from test.utils import db_utils, ldap_utils


@pytest.fixture(scope='function', name='db')
def db(docker_config: Config):
    db = Database(docker_config.database, docker_config.constantes)
    db_utils.init(db)
    return db


@pytest.fixture(scope='function', name='ldap')
def ldap(docker_config: Config):
    ldap = Ldap(docker_config.ldap)
    ldap_utils.reset(ldap)
    return ldap


class TestEtablissement:
    @pytest.fixture(autouse=True)
    def manage_ldap(self, ldap: Ldap):
        ldap.connect()
        try:
            yield
        finally:
            ldap.disconnect()

    @pytest.fixture(autouse=True)
    def manage_db(self, db: Database):
        db.connect()
        try:
            yield
        finally:
            db.disconnect()

    def test_should_load_context(self, ldap: Ldap, db: Database, docker_config: Config):
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchroniser = Synchronizer(ldap, db, docker_config)
        synchroniser.initialize()

        assert synchroniser.context
        assert synchroniser.context.timestamp_now_sql is not None
        assert synchroniser.context.id_context_categorie_inter_etabs == 3
        assert synchroniser.context.id_context_categorie_inter_cfa == 343065
        assert synchroniser.context.id_field_classe == 1
        assert synchroniser.context.id_field_domaine == 3
        assert synchroniser.context.id_role_extended_teacher == 13
        assert synchroniser.context.id_role_advanced_teacher == 20
        assert synchroniser.context.map_etab_domaine == {'0291595B': ['lycees.netocentre.fr'],
                                                         '0290009C': ['lycees.netocentre.fr']}
