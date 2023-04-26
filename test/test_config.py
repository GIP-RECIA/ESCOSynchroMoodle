# coding: utf-8
from synchromoodle.config import ConfigLoader
from os import path


class TestConfig:
    def test_config_update_no_id(self):
        config_loader = ConfigLoader()
        config = config_loader.load([
            path.join(path.dirname(__file__), 'data/config_test_no_id_1.yml'),
            path.join(path.dirname(__file__), 'data/config_test_no_id_2.yml'),
            path.join(path.dirname(__file__), 'data/config_test_invalid.yml')], True)

        assert config.constantes is not None
        assert config.database is not None
        assert config.ldap is not None
        assert config.actions is not None
        assert len(config.actions) == 2
        config_action_1 = config.actions[0]
        assert config_action_1.etablissements is not None
        assert config_action_1.inter_etablissements is not None
        assert config_action_1.inspecteurs is not None
        assert config_action_1.timestamp_store is not None

        assert config_action_1.timestamp_store.file == "config_test1_precedent.txt"

        config_action_2 = config.actions[1]
        assert config_action_2.timestamp_store.file == "config_test2_precedent.txt"

        assert config.constantes.foo == "constante test foo 2"
        assert config.constantes.bar == "constante test bar 1"
        assert config_action_1.etablissements.prefix_admin_moodle_local == "config_test1:admin:Moodle:local:"
        assert config_action_1.etablissements.prefix_admin_local == "config_test1:admin:local:"
        assert len(config_action_1.etablissements.liste_etab) == 3
        assert config_action_1.etablissements.etab_rgp[1].nom == "ETAB RGP DE TEST 2"
        assert len(config_action_1.etablissements.etab_rgp[2].uais) == 10

    def test_config_update_same_id(self):
        config_loader = ConfigLoader()
        config = config_loader.load([
            path.join(path.dirname(__file__), 'data/config_test_same_id_1.yml'),
            path.join(path.dirname(__file__), 'data/config_test_same_id_2.yml'),
            path.join(path.dirname(__file__), 'data/config_test_invalid.yml')], True)

        assert config.constantes is not None
        assert config.database is not None
        assert config.ldap is not None
        assert config.actions is not None
        assert len(config.actions) == 1
        config_action = config.actions[0]
        assert config_action.etablissements is not None
        assert config_action.inter_etablissements is not None
        assert config_action.inspecteurs is not None
        assert config_action.timestamp_store is not None

        assert config_action.timestamp_store.file == "config_test2_precedent.txt"
        assert config.constantes.foo == "constante test foo 2"
        assert config.constantes.bar == "constante test bar 1"
        assert config_action.etablissements.prefix_admin_moodle_local == "config_test1:admin:Moodle:local:"
        assert config_action.etablissements.prefix_admin_local == "config_test1:admin:local:"
        assert len(config_action.etablissements.liste_etab) == 3
        assert config_action.etablissements.etab_rgp[1].nom == "ETAB RGP DE TEST 2"
        assert len(config_action.etablissements.etab_rgp[2].uais) == 10
