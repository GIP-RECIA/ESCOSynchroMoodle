# coding: utf-8
from synchromoodle.config import ConfigLoader
from os import path


class TestConfig:
    def test_config_update(self):
        config_loader = ConfigLoader()
        config = config_loader.load([
            path.join(path.dirname(__file__), 'data/config_test1.yml'),
            path.join(path.dirname(__file__), 'data/config_test2.yml'),
            path.join(path.dirname(__file__), 'data/config_test_invalid.yml')], True)

        assert config.constantes is not None
        assert config.database is not None
        assert config.ldap is not None
        assert config.etablissements is not None
        assert config.inter_etablissements is not None
        assert config.inspecteurs is not None
        assert config.timestamp_store is not None

        assert config.timestamp_store.file == "config_test2_precedent.txt"
        assert config.constantes.foo == "constante test foo 2"
        assert config.constantes.bar == "constante test bar 1"
        assert config.etablissements.prefixAdminMoodleLocal == "config_test1:admin:Moodle:local:"
        assert config.etablissements.prefixAdminLocal == "config_test1:admin:local:"
        assert len(config.etablissements.listeEtab) == 3
        assert config.etablissements.etabRgp[1].nom == "ETAB RGP DE TEST 2"
        assert len(config.etablissements.etabRgp[2].uais) == 10
