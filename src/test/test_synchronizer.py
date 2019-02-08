# coding: utf-8

import pytest

from synchromoodle.config import Config
from synchromoodle.dbutils import Database, COHORT_NAME_FOR_CLASS
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

    def test_maj_etab(self, ldap: Ldap, db: Database, config: Config):
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchroniser = Synchronizer(ldap, db, config)
        synchroniser.initialize()
        structure = ldap.get_structure("0290009C")
        assert structure is not None
        etab_context = synchroniser.handle_etablissement(structure.uai)
        assert etab_context.uai == "0290009C"
        assert etab_context.gere_admin_local is True
        assert etab_context.etablissement_regroupe is False
        assert etab_context.regexp_admin_moodle == "(esco|clg37):admin:Moodle:local:.*_0290009C$"
        assert etab_context.regexp_admin_local == "(esco|clg37):admin:local:.*_0290009C$"
        assert etab_context.etablissement_theme == "0290009c"
        assert etab_context.id_context_categorie is not None
        assert etab_context.id_zone_privee is not None
        assert etab_context.id_context_course_forum is not None

        etablissement_ou = ldap.get_structure("0290009C").nom
        db.mark.execute("SELECT * FROM {entete}course_categories "
                        "WHERE name = %(name)s "
                        "AND theme = %(theme)s".format(entete=db.entete),
                        params={
                            'name': etablissement_ou,
                            'theme': etab_context.uai
                        })
        result = db.mark.fetchone()
        assert result is not None

    def test_maj_eleve(self, ldap: Ldap, db: Database, config: Config):
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchroniser = Synchronizer(ldap, db, config)
        synchroniser.initialize()
        structure = ldap.get_structure("0290009C")
        eleves = ldap.search_eleve(None, "0290009C")
        eleve = eleves[1]
        etab_context = synchroniser.handle_etablissement(structure.uai)
        synchroniser.handle_eleve(etab_context, eleve)

        db.mark.execute("SELECT * FROM {entete}user WHERE username = %(username)s".format(entete=db.entete),
                        params={
                            'username': str(eleve.uid).lower()
                        })
        result = db.mark.fetchone()
        assert result is not None
        assert result[10] == 'Dorian'
        assert result[12] == 'dorian.meyer@netocentre.fr'
        assert result[27] == '0290009c'
        eleve_id = result[0]
        db.mark.execute("SELECT * FROM {entete}role_assignments WHERE userid = %(userid)s".format(entete=db.entete),
                        params={
                            'userid': eleve_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 0
        for classe in eleve.classes:
            cohort_name = COHORT_NAME_FOR_CLASS % classe
            db.mark.execute("SELECT * FROM {entete}cohort WHERE name = %(name)s".format(entete=db.entete),
                            params={
                                'name': cohort_name
                            })
            cohort = db.mark.fetchone()
            cohort_id = cohort[0]
            db.mark.execute("SELECT * FROM {entete}cohort_members WHERE cohortid = %(cohortid)s AND userid = %(userid)s"
                            .format(entete=db.entete),
                            params={
                                'cohortid': cohort_id,
                                'userid': eleve_id
                            })
            result_cohort_enrollment = db.mark.fetchone()
            assert result_cohort_enrollment is not None
            assert result_cohort_enrollment[2] == eleve_id

        # Test sur un eleve de college
        structure_college = ldap.get_structure("0291595B")
        eleves_college = ldap.search_eleve(None, "0291595B")
        eleve_college = eleves_college[0]
        college_context = synchroniser.handle_etablissement(structure_college.uai)
        synchroniser.handle_eleve(college_context, eleve_college)

        db.mark.execute("SELECT * FROM {entete}user WHERE username = %(username)s".format(entete=db.entete),
                        params={
                            'username': str(eleve_college.uid).lower()
                        })
        result_college = db.mark.fetchone()
        eleve_college_id = result_college[0]
        db.mark.execute("SELECT * FROM {entete}role_assignments WHERE userid = %(userid)s".format(entete=db.entete),
                        params={
                            'userid': eleve_college_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 1
        assert roles_results[0][1] == 14

    def test_maj_enseignant(self, ldap: Ldap, db: Database, config: Config):
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchroniser = Synchronizer(ldap, db, config)
        synchroniser.initialize()
        structure = ldap.get_structure("0291595B")
        enseignants = ldap.search_enseignant(None, "0291595B")
        enseignant = enseignants[0]
        etab_context = synchroniser.handle_etablissement(structure.uai)
        synchroniser.handle_enseignant(etab_context, enseignant)

        db.mark.execute("SELECT * FROM {entete}user WHERE username = %(username)s".format(entete=db.entete),
                        params={
                            'username': str(enseignant.uid).lower()
                        })
        result = db.mark.fetchone()
        assert result is not None
        assert result[10] == 'Chiara'
        assert result[11] == 'OLIVIER'
        assert result[12] == 'noreply@ac-rennes.fr'
        assert result[27] == '0291595b'
        enseignant_id = result[0]

        db.mark.execute("SELECT * FROM {entete}role_assignments WHERE userid = %(userid)s".format(entete=db.entete),
                        params={
                            'userid': enseignant_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 3
        assert roles_results[0][1] == 2
        assert roles_results[0][2] == 3
        assert roles_results[1][1] == 2
        assert roles_results[1][2] == 1184277
        assert roles_results[2][1] == 5
        assert roles_results[2][2] == 1184278

    def test_maj_user_interetab(self, ldap: Ldap, db: Database, config: Config):
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchroniser = Synchronizer(ldap, db, config)
        synchroniser.initialize()
        users = ldap.search_personne()
        user = users[0]
        synchroniser.handle_user_interetab(user)

        db.mark.execute("SELECT * FROM {entete}user WHERE username = %(username)s".format(entete=db.entete),
                        params={
                            'username': str(user.uid).lower()
                        })
        result = db.mark.fetchone()
        user_id = result[0]

        db.mark.execute("SELECT * FROM {entete}role_assignments WHERE userid = %(userid)s".format(entete=db.entete),
                        params={
                            'userid': user_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 1

    def test_maj_usercfa_interetab(self, ldap: Ldap, db: Database, config: Config):
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchroniser = Synchronizer(ldap, db, config)
        synchroniser.initialize()
        users = ldap.search_personne()
        user = users[0]
        user.is_member_of = [config.inter_etablissements.ldap_valeur_attribut_admin]
        synchroniser.handle_user_interetab(user)

        db.mark.execute("SELECT * FROM {entete}user WHERE username = %(username)s".format(entete=db.entete),
                        params={
                            'username': str(user.uid).lower()
                        })
        result = db.mark.fetchone()
        user_id = result[0]
        db.mark.execute("SELECT * FROM {entete}role_assignments WHERE userid = %(userid)s".format(entete=db.entete),
                        params={
                            'userid': user_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 2
        assert roles_results[1][1] == db.get_id_role_admin_local()

    def test_maj_inspecteur(self, ldap: Ldap, db: Database, config: Config):
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchroniser = Synchronizer(ldap, db, config)
        synchroniser.initialize()
        users = ldap.search_personne()
        user = users[0]
        synchroniser.handle_inspecteur(user)

        db.mark.execute("SELECT * FROM {entete}user WHERE username = %(username)s".format(entete=db.entete),
                        params={
                            'username': str(user.uid).lower()
                        })
        result = db.mark.fetchone()
        user_id = result[0]
        assert result is not None

        db.mark.execute("SELECT * FROM {entete}role_assignments WHERE userid = %(userid)s".format(entete=db.entete),
                        params={
                            'userid': user_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 1
        assert roles_results[0][1] == 2

        db.mark.execute("SELECT * FROM {entete}user_info_data WHERE userid = %(userid)s".format(entete=db.entete),
                        params={
                            'userid': user_id
                        })
        infos_result = db.mark.fetchone()
        assert infos_result[3] == "lycees.netocentre.fr"
