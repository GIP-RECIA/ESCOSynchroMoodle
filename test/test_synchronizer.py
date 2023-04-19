# coding: utf-8

import pytest
from unittest.mock import call
import platform
import json
from synchromoodle.config import Config, ActionConfig, ConfigLoader
from synchromoodle.dbutils import Database
from synchromoodle.ldaputils import Ldap
from synchromoodle.synchronizer import Synchronizer
from synchromoodle.webserviceutils import WebService
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

def fake_get_courses_user_enrolled_test_eleves(userid):
    return_values = {492286:[37000],492287:[],492288:[],492289:[],492290:[37000],492291:[],\
    492292:[],492293:[],492294:[],492295:[],492296:[37000],492297:[37000],492298:[]}
    return return_values[userid]

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

        synchronizer = Synchronizer(ldap, db, docker_config)
        synchronizer.initialize()

        assert synchronizer.context
        assert synchronizer.context.timestamp_now_sql is not None
        assert synchronizer.context.id_context_categorie_inter_etabs == 3
        assert synchronizer.context.id_context_categorie_inter_cfa == 343065
        assert synchronizer.context.id_field_classe == 1
        assert synchronizer.context.id_field_domaine == 3
        assert synchronizer.context.id_role_extended_teacher == 13
        assert synchronizer.context.id_role_advanced_teacher == 20
        assert synchronizer.context.map_etab_domaine == {'0291595B': ['lycees.netocentre.fr'],
                                                         '0290009C': ['lycees.netocentre.fr']}

    def test_maj_etab(self, ldap: Ldap, db: Database, config: Config):
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()
        structure = ldap.get_structure("0290009C")
        assert structure is not None
        etab_context = synchronizer.handle_etablissement(structure.uai)
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

        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()
        structure = ldap.get_structure("0290009C")
        eleves = ldap.search_eleve(None, "0290009C")
        eleve = eleves[1]
        etab_context = synchronizer.handle_etablissement(structure.uai)
        synchronizer.handle_eleve(etab_context, eleve)

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
            cohort_name = "Élèves de la Classe %s" % classe.classe
            db.mark.execute("SELECT * FROM {entete}cohort WHERE name = %(name)s".format(entete=db.entete),
                            params={
                                'name': cohort_name
                            })
            cohort = db.mark.fetchone()
            assert cohort != None
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

    def test_maj_enseignant(self, ldap: Ldap, db: Database, config: Config):
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()
        structure = ldap.get_structure("0290009C")
        enseignants = ldap.search_enseignant(None, "0290009C")
        enseignant = enseignants[1]
        etab_context = synchronizer.handle_etablissement(structure.uai)
        synchronizer.handle_enseignant(etab_context, enseignant)

        db.mark.execute("SELECT * FROM {entete}user WHERE username = %(username)s".format(entete=db.entete),
                        params={
                            'username': str(enseignant.uid).lower()
                        })
        result = db.mark.fetchone()
        assert result is not None
        assert result[10] == 'Jules'
        assert result[11] == 'PICARD'
        assert result[12] == 'noreply@ac-rennes.fr'
        assert result[27] == '0290009c'
        enseignant_id = result[0]

        db.mark.execute("SELECT * FROM {entete}role_assignments WHERE userid = %(userid)s".format(entete=db.entete),
                        params={
                            'userid': enseignant_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 4
        assert roles_results[0][1] == 2
        assert roles_results[0][2] == 3
        assert roles_results[1][1] == 21
        assert roles_results[1][2] == 1
        assert roles_results[2][1] == 2
        assert roles_results[2][2] == 1184277
        assert roles_results[3][1] == 5
        assert roles_results[3][2] == 1184278

    def test_maj_user_interetab(self, ldap: Ldap, db: Database, config: Config):
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()
        users = ldap.search_personne()
        user = users[0]
        synchronizer.handle_user_interetab(user)

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

    def test_maj_usercfa_interetab(self, ldap: Ldap, db: Database, config: Config, action_config: ActionConfig):
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()
        users = ldap.search_personne()
        user = users[0]
        user.is_member_of = [action_config.inter_etablissements.ldap_valeur_attribut_admin]
        synchronizer.handle_user_interetab(user)

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

        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()
        users = ldap.search_personne()
        user = users[0]
        synchronizer.handle_inspecteur(user)

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

    def test_eleve_passage_lycee(self, ldap: Ldap, db: Database, config: Config):
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()
        college = ldap.get_structure("0291595B")
        lycee = ldap.get_structure("0290009C")
        eleves = ldap.search_eleve(None, "0291595B")
        eleve = eleves[0]
        college_context = synchronizer.handle_etablissement(college.uai)
        lycee_context = synchronizer.handle_etablissement(lycee.uai)
        synchronizer.handle_eleve(college_context, eleve)

        db.mark.execute("SELECT * FROM {entete}user WHERE username = %(username)s".format(entete=db.entete),
                        params={
                            'username': str(eleve.uid).lower()
                        })
        result = db.mark.fetchone()
        eleve_id = result[0]
        db.mark.execute("SELECT * FROM {entete}role_assignments WHERE userid = %(userid)s".format(entete=db.entete),
                        params={
                            'userid': eleve_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 1
        assert roles_results[0][1] == 14

        eleve.uai_courant = "0290009C"
        synchronizer.handle_eleve(lycee_context, eleve)
        db.mark.execute("SELECT * FROM {entete}role_assignments WHERE userid = %(userid)s".format(entete=db.entete),
                        params={
                            'userid': eleve_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 0

    def test_purge_cohortes(self, ldap: Ldap, db: Database, config: Config):
        """
        Teste la purge des cohortes :
            - Récupération des cohortes de moodle
            - Suppression d'un utilisateur d'une cohorte dans le ldap repercutée dans moodle
                - Eleves par classe
                - Eleves par niveau de formation
                - Enseignants par classe
                - Enseignants par établissement
            - Suppression des cohortes vides
        """

        #Chargement d'une configuration spécifique avec les infos relatives au nettoyage
        config_loader = ConfigLoader()
        config = config_loader.update(config, ["config/test-nettoyage.yml"])

        #Chargement du ldap et de la bd
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        #Initialisation du synchronizer
        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()

        #Synchronisation d'un établissement
        etab_context = synchronizer.handle_etablissement("0290009C")

        #Synchronisation des élèves de cet établissement
        eleves = ldap.search_eleve(None, "0290009C")
        for eleve in eleves:
            synchronizer.handle_eleve(etab_context, eleve)

        #Synchronisation des enseignants de cet établissement
        enseignants = ldap.search_enseignant(None, "0290009C")
        for enseignant in enseignants:
            synchronizer.handle_enseignant(etab_context, enseignant)

        #Récupération des cohortes dans le ldap et des cohortes crées dans moodle
        eleves_by_cohorts_db, eleves_by_cohorts_ldap = synchronizer.\
            get_users_by_cohorts_comparators_eleves_classes(etab_context, r'(Élèves de la Classe )(.*)$',
                                             'Élèves de la Classe %')

        eleves_lvformation_by_cohorts_db, eleves_lvformation_by_cohorts_ldap = synchronizer.\
            get_users_by_cohorts_comparators_eleves_niveau(etab_context, r'(Élèves du Niveau de formation )(.*)$',
                                             'Élèves du Niveau de formation %')

        profs_classe_by_cohorts_db, profs_classe_by_cohorts_ldap = synchronizer.\
            get_users_by_cohorts_comparators_profs_classes(etab_context, r'(Profs de la Classe )(.*)$',
                                             'Profs de la Classe %')

        profs_etab_by_cohorts_db, profs_etab_by_cohorts_ldap = synchronizer.\
            get_users_by_cohorts_comparators_profs_etab(etab_context, r"(Profs de l'établissement )(.*)$",
                                             "Profs de l'établissement %")

        #Sans aucune suppression ou ajout, les cohortes dans le ldap et dans moodle doivent être les mêmes
        assert eleves_by_cohorts_db == eleves_by_cohorts_ldap
        assert eleves_lvformation_by_cohorts_db == eleves_lvformation_by_cohorts_ldap
        assert profs_classe_by_cohorts_db == profs_classe_by_cohorts_ldap
        assert profs_etab_by_cohorts_db == profs_etab_by_cohorts_ldap

        #Suppression manuelle de certaines cohortes d'utilisateurs spécifiques dans le ldap
        #Eleves par classe
        eleves_by_cohorts_ldap.pop('1ERE S2', None)
        eleves_by_cohorts_ldap.pop('TES3', None)
        eleves_by_cohorts_ldap['TS2'].remove('f1700ivg')
        eleves_by_cohorts_ldap['TS2'].remove('f1700ivl')
        eleves_by_cohorts_ldap['TS2'].remove('f1700ivv')

        #Eleves par niveau
        eleves_lvformation_by_cohorts_ldap["TERMINALE GENERALE & TECHNO YC BT"].remove("f1700ivg")
        eleves_lvformation_by_cohorts_ldap["TERMINALE GENERALE & TECHNO YC BT"].remove("f1700ivh")

        #Enseignants par classe
        profs_classe_by_cohorts_ldap["TES1"].remove("f1700jym")

        #Enseignants par établissement
        profs_etab_by_cohorts_ldap["(0290009C)"].remove("f1700jym")

        #Purge des cohortes
        synchronizer.purge_cohorts(eleves_by_cohorts_db, eleves_by_cohorts_ldap,
                                   "Élèves de la Classe %s")
        synchronizer.purge_cohorts(eleves_lvformation_by_cohorts_db, eleves_lvformation_by_cohorts_ldap,
                                   'Élèves du Niveau de formation %s')
        synchronizer.purge_cohorts(profs_classe_by_cohorts_db, profs_classe_by_cohorts_ldap,
                                   'Profs de la Classe %s')
        synchronizer.purge_cohorts(profs_etab_by_cohorts_db, profs_etab_by_cohorts_ldap,
                                   "Profs de l'établissement %s")

        #Suppression des cohortes vides
        db.delete_empty_cohorts()

        #Vérification de la suppression des cohortes 1ERE S2 et TS2
        s = "SELECT COUNT(cohort_members.id) FROM {entete}cohort_members AS cohort_members" \
            " INNER JOIN {entete}cohort AS cohort" \
            " ON cohort_members.cohortid = cohort.id" \
            " WHERE cohort.name = %(cohortname)s".format(entete=db.entete)

        db.mark.execute(s, params={'cohortname': "Élèves de la Classe 1ERE S2"})
        result = db.mark.fetchone()
        assert result[0] == 0
        db.mark.execute(s, params={'cohortname': "Élèves de la Classe TES3"})
        result = db.mark.fetchone()
        assert result[0] == 0

        #On s'assure que les utilisateurs qu'on à supprimé des cohortes dans le ldap ont bien aussi été supprimés des cohortes dans moodle
        #Eleves par classe : récupération des membres de la cohorte d'élèves TS2
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Élèves de la Classe TS2"
                        })
        results = [result[0] for result in db.mark.fetchall()]
        assert 'f1700ivg' not in results
        assert 'f1700ivl' not in results
        assert 'f1700ivv' not in results
        assert len(results) == len(eleves_by_cohorts_db["TS2"])-3

        #Eleves par niveau : récupération des membres de la cohorte d'élèves TERMINALE GENERALE & TECHNO YC BT
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Élèves du Niveau de formation TERMINALE GENERALE & TECHNO YC BT"
                        })
        results = [result[0] for result in db.mark.fetchall()]
        assert 'f1700ivg' not in results
        assert 'f1700ivh' not in results
        assert len(results) == len(eleves_lvformation_by_cohorts_db["TERMINALE GENERALE & TECHNO YC BT"])-2

        #Enseignants par classe : récupération des membres de la cohorte de profs TES1
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Profs de la Classe TES1"
                        })
        results = [result[0] for result in db.mark.fetchall()]
        assert 'f1700jym' not in results
        assert len(results) == len(profs_classe_by_cohorts_db["TES1"])-1

        #Enseignants par établissement : récupération des membres de la cohorte de profs TES1
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Profs de l'établissement (0290009C)"
                        })
        results = [result[0] for result in db.mark.fetchall()]
        assert 'f1700jym' not in results
        assert len(results) == len(profs_etab_by_cohorts_db["(0290009C)"])-1

    def test_anonymize_or_delete_eleves(self, ldap: Ldap, db: Database, config: Config, mocker):
        """
        Teste la suppression/anonymisation des élèves devenus inutiles :
            - Ajout d'utilisateurs directement dans moodle qui ne sont pas présents dans le ldap
                - Variation de la date de dernière connexion
                - Inscriptions ou non à des cours
                - Références ou non à des cours
            - # TODO: Suppression d'utilisateurs dans le ldap qui sont présents dans moodle
        """

        #Chargement du ldap et de la bd
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        #Initialisation de l'objet webservice
        webservice = WebService(config.webservice)

        #Initialisation du synchronizer
        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()

        #Synchronisation d'un établissement
        etab_context = synchronizer.handle_etablissement("0290009C")

        #Synchronisation des élèves de cet établissement
        ldap_eleves = ldap.search_eleve(uai="0290009C")
        for eleve in ldap_eleves:
            synchronizer.handle_eleve(etab_context, eleve)

        #Ajout dans la BD des élèves, cours et références factices
        db_utils.insert_eleves(db, config, webservice)

        #Récupération des utilisateurs de la bd coté moodle
        db_valid_users = db.get_all_valid_users()

        #Mocks
        #Attention on mock les fonctions dans synchronizer.py et pas dans webserviceutils.py
        #Ici on a .WebService mais c'est pour indiquer l'objet WebService et non pas le fichier
        mock_get_users_enrolled = mocker.patch('synchromoodle.synchronizer.WebService.get_courses_user_enrolled',\
         side_effect=fake_get_courses_user_enrolled_test_eleves)
        mock_unenrol_user_from_course = mocker.patch('synchromoodle.synchronizer.WebService.unenrol_user_from_course')
        mock_delete_courses = mocker.patch('synchromoodle.synchronizer.WebService.delete_courses')
        mock_delete_users = mocker.patch('synchromoodle.synchronizer.WebService.delete_users')
        mock_anon_users = mocker.patch('synchromoodle.synchronizer.Database.anonymize_users')

        #Appel direct à la méthode s'occupant d'anonymiser et de supprimer les utilisateurs dans la synchro
        synchronizer.anonymize_or_delete_users(ldap_eleves, db_valid_users)

        #Vérification de la suppression des utilisateurs
        #Attention on bien 1 seul call à la méthode car on supprime tous les utilisateurs d'un coup
        mock_delete_users.assert_has_calls([call([492288,492290,492291,492293,492294])])

        #Vérification de l'anonymisation des utilisateurs
        mock_anon_users.assert_has_calls([call([492286,492287,492289,492292,492295])])

        #On vérifie aussi que l'on a pas fait d'appels aux méthodes qui ne doivent pas reçevoir d'appels
        mock_delete_courses.assert_not_called()
        mock_unenrol_user_from_course.assert_not_called()

    def test_course_backup(self, ldap: Ldap, db: Database, config: Config):

        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)
        db_utils.run_script('data/delete-context.sql', db, connect=False)

        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()
        etab_context = synchronizer.handle_etablissement("0290009C")

        ldap_eleves = ldap.search_eleve(uai="0290009C")
        ldap_enseignants = ldap.search_enseignant(uai="0290009C")
        enseignant = ldap_enseignants[0]
        enseignant2 = ldap_enseignants[1]
        for eleve in ldap_eleves:
            synchronizer.handle_eleve(etab_context, eleve)
        for enseignant in ldap_enseignants:
            synchronizer.handle_enseignant(etab_context, enseignant)

        db.mark.execute("SELECT id FROM {entete}user WHERE username = %(username)s".format(entete=db.entete), params={
            'username': str(enseignant.uid).lower()
        })
        enseignant_db = db.mark.fetchone()

        db.mark.execute("SELECT id FROM {entete}user WHERE username = %(username)s".format(entete=db.entete), params={
            'username': str(enseignant2.uid).lower()
        })
        enseignant2_db = db.mark.fetchone()

        now = synchronizer.context.timestamp_now_sql
        db.mark.execute("INSERT INTO {entete}course (fullname, timemodified) VALUES ('cours de test 1',"
                        " %(timemodified)s)".format(entete=db.entete), params={'timemodified': now})
        db.mark.execute("INSERT INTO {entete}course (fullname, timemodified) VALUES ('cours de test 2',"
                        " %(timemodified)s)".format(entete=db.entete), params={'timemodified': now - 31622400})
        db.mark.execute("INSERT INTO {entete}course (fullname, timemodified) VALUES ('cours de test 3',"
                        " %(timemodified)s)".format(entete=db.entete), params={'timemodified': now - 31622400})
        db.mark.execute("SELECT id, fullname, timemodified FROM {entete}course ORDER BY id DESC LIMIT 3"
                        .format(entete=db.entete))
        courses = db.mark.fetchall()

        for course in courses:
            db.mark.execute("INSERT INTO {entete}context (contextlevel, instanceid) VALUES (50, %(instanceid)s)"
                            .format(entete=db.entete), params={'instanceid': course[0]})
            db.mark.execute("SELECT id FROM {entete}context ORDER BY id DESC LIMIT 1".format(entete=db.entete))
            contextid = db.mark.fetchone()
            db.add_role_to_user(config.constantes.id_role_proprietaire_cours, contextid[0], enseignant_db[0])

        db.mark.execute("INSERT INTO {entete}context (contextlevel, instanceid) VALUES (60, %(instanceid)s)"
                        .format(entete=db.entete), params={'instanceid': courses[1][0]})

        db.mark.execute("SELECT id FROM {entete}context ORDER BY id DESC LIMIT 1".format(entete=db.entete))
        contextid = db.mark.fetchone()

        db.add_role_to_user(config.constantes.id_role_proprietaire_cours, contextid[0], enseignant2_db[0])

        synchronizer.check_and_process_user_courses(enseignant_db[0])

        db.mark.execute("SELECT id FROM {entete}course WHERE fullname LIKE 'cours de test%'".format(entete=db.entete))
        new_courses = db.mark.fetchall()
        new_courses_ids = [new_course[0] for new_course in new_courses]
        assert len(new_courses_ids) == 2
        assert courses[0][0] not in new_courses_ids
