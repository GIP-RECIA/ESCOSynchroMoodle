# coding: utf-8
"""
Module pour les tests par rapport au comportement de la synchronisation
"""

from test.utils import db_utils, ldap_utils, mock_utils
from unittest.mock import call
import pytest
import pytest_mock
from synchromoodle.config import Config, ActionConfig
from synchromoodle.dbutils import Database
from synchromoodle.ldaputils import Ldap
from synchromoodle.synchronizer import Synchronizer, UserType


@pytest.fixture(scope='function', name='db')
def fixture_db(docker_config: Config) -> Database:
    """
    Créé la base de données utilisée cette session de tests

    :returns: L'objet Database permettant d'intéragir avec le docker contenant le mariadb
    """
    db = Database(docker_config.database, docker_config.constantes)
    db_utils.init(db)
    return db


@pytest.fixture(scope='function', name='ldap')
def fixture_ldap(docker_config: Config) -> Ldap:
    """
    Créé le ldap utilisé cette session de tests

    :returns: L'objet Ldap permettant d'intéragir avec le docker contenant le ldap
    """
    ldap = Ldap(docker_config.ldap)
    ldap_utils.reset(ldap)
    return ldap

class TestEtablissement:
    """Classe de tests pour vérifier la synchro d'un établissement
    et de ses élèves et enseignants."""

    @pytest.fixture(autouse=True)
    def manage_ldap(self, ldap: Ldap):
        """
        Se connecte au ldap.

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        """
        ldap.connect()
        try:
            yield
        finally:
            ldap.disconnect()

    @pytest.fixture(autouse=True)
    def manage_db(self, db: Database):
        """
        Se connecte au mariadb.

        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        """
        db.connect()
        try:
            yield
        finally:
            db.disconnect()

    def test_should_load_context(self, ldap: Ldap, db: Database, docker_config: Config):
        """
        Vérifie que le contexte par défaut d'un établissement se charge bien.

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param docker_config: La configuration globale pendant la session de tests
        """
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
        """
        Permet de vérifier la synchronisation des établissements dans moodle.

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        """
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        #Synchronisation d'un établissement
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
        assert etab_context.id_zone_privee is not None #Vérification de la création du cours privé
        assert etab_context.id_context_course_forum is not None

        #On s'assure qu'une catégorie de cours associée à l'établissement à bien été créée
        etablissement_ou = ldap.get_structure("0290009C").nom
        db.mark.execute(f"SELECT * FROM {db.entete}course_categories "
                        "WHERE name = %(name)s "
                        "AND theme = %(theme)s",
                        params={
                            'name': etablissement_ou,
                            'theme': etab_context.uai
                        })
        result = db.mark.fetchone()
        assert result is not None

    def test_maj_dane(self, ldap: Ldap, db: Database, config: Config):
        """
        Permet de vérifier la synchronisation de la dane en vérifiant
        que les cohortes dane ont bien été créées.

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        """
        ldap_utils.run_ldif('data/structure_dane.ldif', ldap)
        ldap_utils.run_ldif('data/user_dane.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        #Synchronisation de la dane
        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()
        dane_context = synchronizer.handle_dane(config.constantes.uai_dane)
        assert dane_context.uai == "0450080T"
        assert dane_context.etablissement_theme == "0450080t"
        assert dane_context.id_context_categorie is not None
        assert synchronizer.ids_cohorts_dane_lycee_en
        assert synchronizer.ids_cohorts_dane_dep_clg

        #On s'assure de la création des utilisateurs de la dane
        assert db.get_user_id("F171008t")
        medic_id = db.get_user_id("F111009f")
        assert medic_id

        #On s'assure de la création de la cohorte médic de la dane
        db.mark.execute(f"SELECT * FROM {db.entete}cohort WHERE name = %(name)s",
                        params={
                            'name': config.dane.cohort_medic_dane_name
                        })
        cohort = db.mark.fetchone()
        assert cohort is not None
        cohort_id = cohort[0]
        #Inscription du bon utilisateur dans la cohorte
        db.mark.execute(f"SELECT * FROM {db.entete}cohort_members"
                        " WHERE cohortid = %(cohortid)s AND userid = %(userid)s",
                        params={
                            'cohortid': cohort_id,
                            'userid': medic_id
                        })
        result_cohort_enrollment = db.mark.fetchone()
        assert result_cohort_enrollment is not None
        assert result_cohort_enrollment[2] == medic_id

        #On s'assure de la création des autres cohortes dane
        #Pour les lycées
        for user_type in UserType:
            db.mark.execute("SELECT * FROM {entete}cohort as cohort"
                                      " INNER JOIN {entete}context as context"
                                      " ON cohort.contextid = context.id"
                                      " WHERE cohort.id = %(cohortid)s".format(entete=db.entete),
                            params={
                                'cohortid': synchronizer.ids_cohorts_dane_lycee_en[user_type],
                            })
            result = db.mark.fetchone()
            assert result is not None

        #Pour les collèges
        for departement in config.constantes.departements:
            for user_type in UserType:
                db.mark.execute("SELECT * FROM {entete}cohort as cohort"
                                          " INNER JOIN {entete}context as context"
                                          " ON cohort.contextid = context.id"
                                          " WHERE cohort.id = %(cohortid)s".format(entete=db.entete),
                                params={
                                    'cohortid': synchronizer.ids_cohorts_dane_dep_clg[user_type][departement],
                                })
                result = db.mark.fetchone()
                assert result is not None

    def test_maj_eleve(self, ldap: Ldap, db: Database, config: Config):
        """
        Permet de vérifier la synchronisation des élèves dans moodle.

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        """
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()
        structure = ldap.get_structure("0290009C")
        eleves = ldap.search_eleve(None, "0290009C")
        eleve = None
        for eleve_searched in eleves:
            if eleve_searched.uid == "F1700ivh":
                eleve = eleve_searched
        etab_context = synchronizer.handle_etablissement(structure.uai)
        synchronizer.handle_eleve(etab_context, eleve)

        #On vérifie si les infos de moodle correspondent bien avec celles du ldap
        db.mark.execute(f"SELECT * FROM {db.entete}user WHERE username = %(username)s",
                        params={
                            'username': str(eleve.uid).lower()
                        })
        result = db.mark.fetchone()
        assert result is not None
        assert result[10] == 'Dorian'
        assert result[12] == 'dorian.meyer@netocentre.fr'
        assert result[27] == '0290009c'

        #On modifie l'élève dans le ldap et on vérifie que la modification s'est bien reportée
        eleve.given_name = "Thomas"
        synchronizer.handle_eleve(etab_context, eleve)
        db.mark.execute(f"SELECT * FROM {db.entete}user WHERE username = %(username)s",
                        params={
                            'username': str(eleve.uid).lower()
                        })
        result = db.mark.fetchone()
        assert result is not None
        assert result[10] == 'Thomas'

        #Vérification des rôles
        eleve_id = result[0]
        db.mark.execute(f"SELECT * FROM {db.entete}role_assignments WHERE userid = %(userid)s",
                        params={
                            'userid': eleve_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 0

        #Vérification des inscriptions dans les cohortes
        #Cohorte de la classe de l'élève
        for classe in eleve.classes:
            cohort_name = config.constantes.cohortname_pattern_eleves_classe.replace("%", classe.classe)
            db.mark.execute(f"SELECT * FROM {db.entete}cohort WHERE name = %(name)s",
                            params={
                                'name': cohort_name
                            })
            cohort = db.mark.fetchone()
            assert cohort is not None #On vérifie que la cohorte existe
            cohort_id = cohort[0]
            db.mark.execute(f"SELECT * FROM {db.entete}cohort_members"
                            " WHERE cohortid = %(cohortid)s AND userid = %(userid)s",
                            params={
                                'cohortid': cohort_id,
                                'userid': eleve_id
                            })
            result_cohort_enrollment = db.mark.fetchone()
            assert result_cohort_enrollment is not None
            assert result_cohort_enrollment[2] == eleve_id #On vérifie que l'élève est bien inscrit dedans

        #Cohorte du niveau de formation de l'élève
        cohort_name = config.constantes.cohortname_pattern_eleves_niv_formation.replace("%", eleve.niveau_formation)
        db.mark.execute(f"SELECT * FROM {db.entete}cohort WHERE name = %(name)s",
                        params={
                            'name': cohort_name
                        })
        cohort = db.mark.fetchone()
        assert cohort is not None #On vérifie que la cohorte existe
        cohort_id = cohort[0]
        db.mark.execute(f"SELECT * FROM {db.entete}cohort_members"
                        " WHERE cohortid = %(cohortid)s AND userid = %(userid)s",
                        params={
                            'cohortid': cohort_id,
                            'userid': eleve_id
                        })
        result_cohort_enrollment = db.mark.fetchone()
        assert result_cohort_enrollment is not None
        assert result_cohort_enrollment[2] == eleve_id


    def test_maj_enseignant(self, ldap: Ldap, db: Database, config: Config):
        """
        Permet de vérifier la synchronisation des enseignants dans moodle.
        - Charge un enseignant depuis le LDAP et l'ajoute dans moodle
        - Modifie un enseignant dans le LDAP et vérifie que les informations
        sont bien reportées dans mooodle

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        """

        #Chargement de la bd et du ldap
        ldap_utils.run_ldif('data/all.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        #Initialisation du synchronizer
        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()

        #Récupération du lycée, des élèves et des enseignants depuis le ldap
        structure_lyc = ldap.get_structure("0290009C")
        enseignants = ldap.search_enseignant(None, "0290009C")
        eleves = ldap.search_eleve(None, "0290009C")

        #Récupération de l'enseignant sur lequel on va faire les tests
        enseignant = None
        for enseignant_searched in enseignants:
            if enseignant_searched.sn == "JEAN" and enseignant_searched.given_name == "Diane":
                enseignant = enseignant_searched
        assert enseignant is not None

        #Synchronisation de l'établissement et des élèves du lycée et de l'enseignant dans ce contexte
        etab_context = synchronizer.handle_etablissement(structure_lyc.uai)
        synchronizer.construct_classe_to_niv_formation(etab_context, ldap.search_eleve_classe_and_niveau(structure_lyc.uai))
        synchronizer.handle_enseignant(etab_context, enseignant)

        #Synchronisation aussi du contexte du collège
        structure_clg = ldap.get_structure("0291595B")
        etab_context_clg = synchronizer.handle_etablissement(structure_clg.uai)
        eleves_clg = ldap.search_eleve(None, "0291595B")
        synchronizer.construct_classe_to_niv_formation(etab_context_clg, ldap.search_eleve_classe_and_niveau(structure_clg.uai))

        #On va inscrire aussi l'enseignant dans les cohortes du niveau de formation correspondant au collège
        synchronizer.handle_enseignant(etab_context_clg, enseignant)

        #On vérifie que les informations correspondent bien
        db.mark.execute(f"SELECT * FROM {db.entete}user WHERE username = %(username)s",
                        params={
                            'username': str(enseignant.uid).lower()
                        })
        result = db.mark.fetchone()
        assert result is not None
        assert result[10] == 'Diane'
        assert result[11] == 'JEAN'
        assert result[12] == 'noreply@ac-rennes.fr'
        assert result[27] == '0290009c'

        #On simule un changement sur l'enseignant dans le ldap
        enseignant.sn = "JEANNE"
        synchronizer.handle_enseignant(etab_context, enseignant)
        #On vérifie qu'il s'est bien reporté dans moodle
        db.mark.execute(f"SELECT * FROM {db.entete}user WHERE username = %(username)s",
                        params={
                            'username': str(enseignant.uid).lower()
                        })
        result = db.mark.fetchone()
        enseignant_id = result[0]

        assert result is not None
        assert result[11] == 'JEANNE'

        #On vérifie qu'il a les bons rôles
        db.mark.execute(f"SELECT * FROM {db.entete}role_assignments WHERE userid = %(userid)s",
                        params={
                            'userid': enseignant_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 6

        #Role créateur de cours dans la catégorie interetablissements
        assert roles_results[0][1] == config.constantes.id_role_createur_cours
        assert roles_results[0][2] == 3

        #Role BigBlueButton
        assert roles_results[1][1] == config.constantes.id_role_bigbluebutton
        assert roles_results[1][2] == 1

        #Role créateur de cours dans la catégorie de son établissement
        assert roles_results[2][1] == config.constantes.id_role_createur_cours
        assert roles_results[2][2] == 1184277

        #Role élève dans le contexte forum (zone privée)
        assert roles_results[3][1] == config.constantes.id_role_eleve
        assert roles_results[3][2] == 1184278

        #Role créateur de cours dans la catégorie de son établissement
        assert roles_results[4][1] == config.constantes.id_role_createur_cours
        assert roles_results[4][2] == 1184281

        #Role élève dans le contexte forum (zone privée)
        assert roles_results[5][1] == config.constantes.id_role_eleve
        assert roles_results[5][2] == 1184282

        #On vérifie aussi ses inscriptions dans les cohortes
        #Cohorte de la classe des enseignants
        for classe in enseignant.classes:
            cohort_name = config.constantes.cohortname_pattern_enseignants_classe.replace("%", classe.classe)
            db.mark.execute(f"SELECT * FROM {db.entete}cohort WHERE name = %(name)s",
                            params={
                                'name': cohort_name
                            })
            cohort = db.mark.fetchone()
            assert cohort is not None #On vérifie que la cohorte existe
            cohort_id = cohort[0]
            db.mark.execute(f"SELECT * FROM {db.entete}cohort_members"
                            " WHERE cohortid = %(cohortid)s AND userid = %(userid)s",
                            params={
                                'cohortid': cohort_id,
                                'userid': enseignant_id
                            })
            result_cohort_enrollment = db.mark.fetchone()
            assert result_cohort_enrollment is not None
            assert result_cohort_enrollment[2] == enseignant_id

        #Cohorte de profs de l'établissement
        for enseignant_uai in enseignant.uais:
            cohort_name = config.constantes.cohortname_pattern_enseignants_etablissement\
             .replace("%", f"({enseignant_uai})")
            db.mark.execute(f"SELECT * FROM {db.entete}cohort WHERE name = %(name)s",
                            params={
                                'name': cohort_name
                            })
            cohort = db.mark.fetchone()
            assert cohort is not None #On vérifie que la cohorte existe
            cohort_id = cohort[0]
            db.mark.execute(f"SELECT * FROM {db.entete}cohort_members"
                            " WHERE cohortid = %(cohortid)s AND userid = %(userid)s",
                            params={
                                'cohortid': cohort_id,
                                'userid': enseignant_id
                            })
            result_cohort_enrollment = db.mark.fetchone()
            assert result_cohort_enrollment is not None
            assert result_cohort_enrollment[2] == enseignant_id

        #Cohorte des niveaux de formation
        #Partie lycée
        niveaux_formation = set()
        for classe in enseignant.classes:
            if classe.classe in etab_context.classe_to_niv_formation:
                niveaux_formation.add(etab_context.classe_to_niv_formation[classe.classe])

        for niv_formation in niveaux_formation:
            cohort_name = config.constantes.cohortname_pattern_enseignants_niv_formation.replace("%", niv_formation)
            db.mark.execute(f"SELECT * FROM {db.entete}cohort WHERE name = %(name)s",
                            params={
                                'name': cohort_name
                            })

            cohort = db.mark.fetchone()
            assert cohort is not None #On vérifie que la cohorte existe
            cohort_id = cohort[0]
            db.mark.execute(f"SELECT * FROM {db.entete}cohort_members"
                            " WHERE cohortid = %(cohortid)s AND userid = %(userid)s",
                            params={
                                'cohortid': cohort_id,
                                'userid': enseignant_id
                            })
            result_cohort_enrollment = db.mark.fetchone()
            assert result_cohort_enrollment is not None
            assert result_cohort_enrollment[2] == enseignant_id

        #Partie collège
        niveaux_formation = set()
        for classe in enseignant.classes:
            if classe.classe in etab_context_clg.classe_to_niv_formation:
                niveaux_formation.add(etab_context_clg.classe_to_niv_formation[classe.classe])

        for niv_formation in niveaux_formation:
            cohort_name = f'Profs du niveau de formation {niv_formation}'
            db.mark.execute(f"SELECT * FROM {db.entete}cohort WHERE name = %(name)s",
                            params={
                                'name': cohort_name
                            })

            cohort = db.mark.fetchone()
            assert cohort is not None #On vérifie que la cohorte existe
            cohort_id = cohort[0]
            db.mark.execute(f"SELECT * FROM {db.entete}cohort_members"
                            " WHERE cohortid = %(cohortid)s AND userid = %(userid)s",
                            params={
                                'cohortid': cohort_id,
                                'userid': enseignant_id
                            })
            result_cohort_enrollment = db.mark.fetchone()
            assert result_cohort_enrollment is not None
            assert result_cohort_enrollment[2] == enseignant_id


    def test_maj_user_interetab(self, ldap: Ldap, db: Database, config: Config):
        """
        Permet de vérifier la synchronisation des utilisateurs interetablissement.

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        """
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()
        users = ldap.search_personne()
        user = users[0]
        synchronizer.handle_user_interetab(user)

        db.mark.execute(f"SELECT * FROM {db.entete}user WHERE username = %(username)s",
                        params={
                            'username': str(user.uid).lower()
                        })
        result = db.mark.fetchone()
        user_id = result[0]

        db.mark.execute(f"SELECT * FROM {db.entete}role_assignments WHERE userid = %(userid)s",
                        params={
                            'userid': user_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 1

    def test_maj_usercfa_interetab(self, ldap: Ldap, db: Database, config: Config, action_config: ActionConfig):
        """
        Permet de vérifier la synchronisation des utilisateurs interetablissement.

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        :param action_config: La configuration de l'action cfa interetab
        """
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

        db.mark.execute(f"SELECT * FROM {db.entete}user WHERE username = %(username)s",
                        params={
                            'username': str(user.uid).lower()
                        })
        result = db.mark.fetchone()
        user_id = result[0]
        db.mark.execute(f"SELECT * FROM {db.entete}role_assignments WHERE userid = %(userid)s",
                        params={
                            'userid': user_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 2
        assert roles_results[1][1] == db.get_id_role_admin_local()


    def test_maj_inspecteur(self, ldap: Ldap, db: Database, config: Config):
        """
        Permet de vérifier la synchronisation des inspecteurs dans moodle.

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        """
        ldap_utils.run_ldif('data/default-structures.ldif', ldap)
        ldap_utils.run_ldif('data/default-personnes-short.ldif', ldap)
        ldap_utils.run_ldif('data/default-groups.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()
        users = ldap.search_personne()
        user = users[0]
        synchronizer.handle_inspecteur(user)

        db.mark.execute(f"SELECT * FROM {db.entete}user WHERE username = %(username)s",
                        params={
                            'username': str(user.uid).lower()
                        })
        result = db.mark.fetchone()
        user_id = result[0]
        assert result is not None

        db.mark.execute(f"SELECT * FROM {db.entete}role_assignments WHERE userid = %(userid)s",
                        params={
                            'userid': user_id
                        })
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 1
        #Les inspecteurs ont le rôle créateur de cours
        assert roles_results[0][1] == config.constantes.id_role_createur_cours

        db.mark.execute(f"SELECT * FROM {db.entete}user_info_data WHERE userid = %(userid)s",
                        params={
                            'userid': user_id
                        })
        infos_result = db.mark.fetchone()
        assert infos_result[3] == "lycees.netocentre.fr"


    def test_eleve_passage_lycee(self, ldap: Ldap, db: Database, config: Config):
        """
        Permet de vérifier qu'on enlève bien le rôle "Utilisateurs avec droits limités"
        quand un élève passe du collège au lycée.

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        """
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

        #Récupération de l'id de l'élève dans moodle
        db.mark.execute(f"SELECT * FROM {db.entete}user WHERE username = %(username)s",
                        params={
                            'username': str(eleve.uid).lower()
                        })
        result = db.mark.fetchone()
        eleve_id = result[0]
        db.mark.execute(f"SELECT * FROM {db.entete}role_assignments WHERE userid = %(userid)s",
                        params={
                            'userid': eleve_id
                        })
        #On vérifie qu'il a bien le rôle Utilisateurs avec droits limités
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 1
        assert roles_results[0][1] == config.constantes.id_role_utilisateur_limite

        #On le fait passer au lycée
        eleve.uai_courant = "0290009C"
        synchronizer.handle_eleve(lycee_context, eleve)
        db.mark.execute(f"SELECT * FROM {db.entete}role_assignments WHERE userid = %(userid)s",
                        params={
                            'userid': eleve_id
                        })

        #On vérifie qu'on lui a bien enlevé le rôle
        roles_results = db.mark.fetchall()
        assert len(roles_results) == 0


    def test_purge_cohortes(self, ldap: Ldap, db: Database, config: Config, mocker: pytest_mock.plugin.MockerFixture):
        """
        Teste la purge des cohortes :

        - Récupération des cohortes de moodle
        - Suppression d'un utilisateur d'une cohorte dans le ldap repercutée dans moodle
        - Eleves par classe
        - Eleves par niveau de formation
        - Enseignants par classe
        - Enseignants par établissement
        - Suppression des cohortes vides

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        :param mocker: L'objet permettant de mocker des fonctions
        """

        #Chargement du ldap et de la bd
        ldap_utils.run_ldif('data/all.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        #Mock pour la suppression de cohortes
        mock_delete_cohorts = mocker.patch('synchromoodle.synchronizer.WebService.delete_cohorts')

        #Initialisation du synchronizer
        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()

        #Synchronisation d'un établissement
        etab_context = synchronizer.handle_etablissement("0290009C")

        #Synchronisation des élèves de cet établissement
        eleves = ldap.search_eleve(None, "0290009C")
        for eleve in eleves:
            synchronizer.handle_eleve(etab_context, eleve)

        #Construction du dictionnaire d'association classe -> niveau formation
        synchronizer.construct_classe_to_niv_formation(etab_context, ldap.search_eleve_classe_and_niveau("0290009C"))

        #Synchronisation des enseignants de cet établissement
        enseignants = ldap.search_enseignant(None, "0290009C", tous=True)
        for enseignant in enseignants:
            synchronizer.handle_enseignant(etab_context, enseignant)

        #Cration d'une fausse cohorte qui n'est associée à rien dans le ldap
        db.create_cohort(etab_context.id_context_categorie,
                         config.constantes.cohortname_pattern_eleves_classe.replace("%","0EME S2"),
                         config.constantes.cohortname_pattern_eleves_classe.replace("%","0EME S2"),
                         config.constantes.cohortname_pattern_eleves_classe.replace("%","0EME S2"), 0)
        old_cohort_id = db.get_cohort_id_from_name(etab_context.id_context_categorie,
           config.constantes.cohortname_pattern_eleves_classe.replace("%","0EME S2"))

        #Inscription d'un utilisateur dans cette cohorte
        db.enroll_user_in_cohort(old_cohort_id, db.get_user_id("f1700ivg"), 0)

        #Récupération des cohortes dans le ldap et des cohortes crées dans moodle
        eleves_by_cohorts_db, eleves_by_cohorts_ldap = synchronizer.\
            get_users_by_cohorts_comparators_eleves_classes(etab_context,
                                                            config.constantes.cohortname_pattern_re_eleves_classe,
                                                            config.constantes.cohortname_pattern_eleves_classe)

        eleves_lvformation_by_cohorts_db, eleves_lvformation_by_cohorts_ldap = synchronizer.\
            get_users_by_cohorts_comparators_eleves_niveau(etab_context,
                                                           config.constantes.cohortname_pattern_re_eleves_niv_formation,
                                                           config.constantes.cohortname_pattern_eleves_niv_formation)

        profs_classe_by_cohorts_db, profs_classe_by_cohorts_ldap = synchronizer.\
            get_users_by_cohorts_comparators_profs_classes(etab_context,
                                                           config.constantes.cohortname_pattern_re_enseignants_classe,
                                                           config.constantes.cohortname_pattern_enseignants_classe)

        profs_etab_by_cohorts_db, profs_etab_by_cohorts_ldap = synchronizer.\
            get_users_by_cohorts_comparators_profs_etab(etab_context,
                                                        config.constantes.cohortname_pattern_re_enseignants_etablissement,
                                                        config.constantes.cohortname_pattern_enseignants_etablissement)

        profs_niveau_by_cohorts_db, profs_niveau_by_cohorts_ldap = synchronizer.\
            get_users_by_cohorts_comparators_profs_niveau(etab_context,
                                                          config.constantes.cohortname_pattern_re_enseignants_niv_formation,
                                                          config.constantes.cohortname_pattern_enseignants_niv_formation)

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

        #Enseignants par niveau
        profs_niveau_by_cohorts_ldap["TERMINALE GENERALE & TECHNO YC BT"].remove("f1700jym")

        #Purge des cohortes
        synchronizer.purge_cohorts(eleves_by_cohorts_db, eleves_by_cohorts_ldap,
                                   config.constantes.cohortname_pattern_eleves_classe.replace("%","%s"))
        synchronizer.purge_cohorts(eleves_lvformation_by_cohorts_db, eleves_lvformation_by_cohorts_ldap,
                                   config.constantes.cohortname_pattern_eleves_niv_formation.replace("%","%s"))
        synchronizer.purge_cohorts(profs_classe_by_cohorts_db, profs_classe_by_cohorts_ldap,
                                   config.constantes.cohortname_pattern_enseignants_classe.replace("%","%s"))
        synchronizer.purge_cohorts(profs_etab_by_cohorts_db, profs_etab_by_cohorts_ldap,
                                   config.constantes.cohortname_pattern_enseignants_etablissement.replace("%","%s"))
        synchronizer.purge_cohorts(profs_niveau_by_cohorts_db, profs_niveau_by_cohorts_ldap,
                                   config.constantes.cohortname_pattern_enseignants_niv_formation.replace("%","%s"))

        #Suppression des cohortes vides
        synchronizer.delete_empty_cohorts()

        #Vérification de la suppression des cohortes 1ERE S2 et TES3 et 0EME S2
        cohorts_to_delete_ids = []
        db.mark.execute(f"SELECT id FROM {db.entete}cohort WHERE name = %(cohortname)s",
                        params={
                            'cohortname': config.constantes.cohortname_pattern_eleves_classe.replace("%", "TES3")
                        })
        cohorts_to_delete_ids.append(db.mark.fetchone()[0])
        db.mark.execute(f"SELECT id FROM {db.entete}cohort WHERE name = %(cohortname)s",
                        params={
                            'cohortname': config.constantes.cohortname_pattern_eleves_classe.replace("%", "1ERE S2")
                        })
        cohorts_to_delete_ids.append(db.mark.fetchone()[0])
        cohorts_to_delete_ids.append(old_cohort_id)
        mock_delete_cohorts.assert_has_calls([call(cohorts_to_delete_ids)])

        #On s'assure que les utilisateurs qu'on à supprimé des cohortes dans le ldap
        #ont bien aussi été supprimés des cohortes dans moodle
        #Eleves par classe : récupération des membres de la cohorte d'élèves TS2
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': config.constantes.cohortname_pattern_eleves_classe.replace("%", "TS2")
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
                            'cohortname': config.constantes.cohortname_pattern_eleves_niv_formation\
                                          .replace("%", "TERMINALE GENERALE & TECHNO YC BT")
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
                            'cohortname': config.constantes.cohortname_pattern_enseignants_classe.replace("%", "TES1")
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
                            'cohortname': config.constantes.cohortname_pattern_enseignants_etablissement\
                                          .replace("%", "(0290009C)")
                        })
        results = [result[0] for result in db.mark.fetchall()]
        assert 'f1700jym' not in results
        assert len(results) == len(profs_etab_by_cohorts_db["(0290009C)"])-1

        #Enseignants par niveau : récupération des membres de la cohorte de profs TERMINALE GENERALE & TECHNO YC BT
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': config.constantes.cohortname_pattern_enseignants_niv_formation
                                          .replace("%", "TERMINALE GENERALE & TECHNO YC BT")
                        })
        results = [result[0] for result in db.mark.fetchall()]
        assert 'f1700jym' not in results
        assert len(results) == len(profs_niveau_by_cohorts_db["TERMINALE GENERALE & TECHNO YC BT"])-1


    def test_purge_cohortes_dane(self, ldap: Ldap, db: Database, config: Config,
                                 mocker: pytest_mock.plugin.MockerFixture):
        """
        Teste la purge des cohortes de la dane :

        - Récupération des cohortes de la dane de moodle
        - Suppression d'un utilisateur d'une cohorte dans le ldap repercutée dans moodle
        - Eleves par classe
        - Eleves par niveau de formation
        - Enseignants par classe
        - Enseignants par établissement

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        :param mocker: L'objet permettant de mocker des fonctions
        """

        #Chargement du ldap et de la bd
        ldap_utils.run_ldif('data/all.ldif', ldap)
        ldap_utils.run_ldif('data/college_dane_18.ldif', ldap)
        ldap_utils.run_ldif('data/lycee_dane.ldif', ldap)
        ldap_utils.run_ldif('data/eleves_college_dane_18.ldif', ldap)
        ldap_utils.run_ldif('data/eleves_lycee_dane.ldif', ldap)
        ldap_utils.run_ldif('data/direction_college_dane_18.ldif', ldap)
        ldap_utils.run_ldif('data/direction_lycee_dane.ldif', ldap)
        ldap_utils.run_ldif('data/profs_college_dane_18.ldif', ldap)
        ldap_utils.run_ldif('data/profs_lycee_dane.ldif', ldap)
        ldap_utils.run_ldif('data/structure_dane.ldif', ldap)
        db_utils.run_script('data/default-context.sql', db, connect=False)

        #Mock pour la suppression de cohortes
        mocker.patch('synchromoodle.synchronizer.WebService.delete_cohorts')

        #Initialisation du synchronizer
        synchronizer = Synchronizer(ldap, db, config)
        synchronizer.initialize()

        #Récupération du contexte de la dane et synchronisation de la dane
        synchronizer.handle_dane(config.constantes.uai_dane, readonly=False)

        #--- PARTIE COLLEGE ---#

        #UAI de l'établissement qu'on va tester
        uai = "0180002E"

        #Synchronisation de cet établissement et de ses élèves/enseignants
        etab_context = synchronizer.handle_etablissement(uai)
        etab_departement = etab_context.departement

        #Synchronisation des élèves de cet établissement
        eleves = ldap.search_eleve(None, uai)
        for eleve in eleves:
            synchronizer.handle_eleve(etab_context, eleve)

        #Construction du dictionnaire d'association classe -> niveau formation
        synchronizer.construct_classe_to_niv_formation(etab_context, ldap.search_eleve_classe_and_niveau(uai))

        #Synchronisation des enseignants de cet établissement
        enseignants = ldap.search_enseignant(None, uai, tous=True)
        for enseignant in enseignants:
            synchronizer.handle_enseignant(etab_context, enseignant)

        #Récupération des cohortes dans le ldap pour les collèges
        cohorts_elv_dep_clg_ldap = {}
        cohorts_ens_dep_clg_ldap = {}
        cohorts_dir_dep_clg_ldap = {}

        for departement in config.constantes.departements:
            cohorts_elv_dep_clg_ldap[departement] = []
            cohorts_ens_dep_clg_ldap[departement] = []
            cohorts_dir_dep_clg_ldap[departement] = []

        assert etab_context.college
        assert etab_departement in config.constantes.departements

        cohorts_elv_dep_clg_ldap[etab_departement].extend(ldap.search_eleve_uid(uai=uai))
        cohorts_ens_dep_clg_ldap[etab_departement].extend(ldap.search_enseignant_profil_uid(profil="National_ENS",\
         uai=uai, tous=False))
        cohorts_dir_dep_clg_ldap[etab_departement].extend(ldap.search_personnel_direction_uid(uai=uai))

        #On vérifie qu'on a bien récupéré les cohortes du ldap
        assert cohorts_elv_dep_clg_ldap
        assert cohorts_ens_dep_clg_ldap
        assert cohorts_dir_dep_clg_ldap

        #Suppression manuelle dans certaines cohortes d'utilisateurs spécifiques dans le ldap
        #On teste pour un département pour chaque type d'utilisateur
        #Type Eleve
        cohorts_elv_dep_clg_ldap[etab_departement].remove("f19105ii")
        #Type Enseignant
        cohorts_ens_dep_clg_ldap[etab_departement].remove("f1700drk")
        #Type personnel de direction
        cohorts_dir_dep_clg_ldap[etab_departement].remove("f171006i")

        #Récupération des cohortes dane collège dans le ldap
        cohort_dane_clg = {}
        for departement in config.constantes.departements:
            cohort_dane_clg[departement] = {UserType.ELEVE:cohorts_elv_dep_clg_ldap[departement],
                                            UserType.ENSEIGNANT:cohorts_ens_dep_clg_ldap[departement],
                                            UserType.PERSONNEL_DE_DIRECTION:cohorts_dir_dep_clg_ldap[departement]}

        #Récupération de ce qu'on a en bd avant la supression
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Élèves des collèges du 18"
                        })
        cohorts_elv_dep_clg_bd =[result[0] for result in db.mark.fetchall()]

        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Enseignants des collèges du 18"
                        })
        cohorts_ens_dep_clg_bd =[result[0] for result in db.mark.fetchall()]

        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Personnel de direction des collèges du 18"
                        })
        cohorts_dir_dep_clg_bd =[result[0] for result in db.mark.fetchall()]

        #Purge des cohortes Collèges
        for departement in config.constantes.departements:
            synchronizer.purge_cohort_dane_clg_dep(cohort_dane_clg[etab_departement], departement)

        #On s'assure que les utilisateurs qu'on à supprimé des cohortes dans le ldap
        #ont bien aussi été supprimés des cohortes dans moodle
        #Type élèves : récupération des membres de la cohorte des élèves des collèges du 18
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Élèves des collèges du 18"
                        })

        results = [result[0] for result in db.mark.fetchall()]
        assert 'f19105ii' not in results
        assert len(results) == len(cohorts_elv_dep_clg_bd)-1

        #Type enseignants : récupération des membres de la cohorte des enseignants des collèges du 18
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Enseignants des collèges du 18"
                        })

        results = [result[0] for result in db.mark.fetchall()]
        assert 'f1700drk' not in results
        assert len(results) == len(cohorts_ens_dep_clg_bd)-1

        #Type personnels de direction : membres de la cohorte des personnels de direction des collèges du 18
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Personnel de direction des collèges du 18"
                        })

        results = [result[0] for result in db.mark.fetchall()]
        assert 'f171006i' not in results
        assert len(results) == len(cohorts_dir_dep_clg_bd)-1

        #--- PARTIE LYCEE ---#

        #UAI de l'établissement qu'on va tester
        uai = "0180005H"

        #Synchronisation de cet établissement et de ses élèves/enseignants
        etab_context = synchronizer.handle_etablissement(uai)

        #Synchronisation des élèves de cet établissement
        eleves = ldap.search_eleve(None, uai)
        for eleve in eleves:
            synchronizer.handle_eleve(etab_context, eleve)

        #Construction du dictionnaire d'association classe -> niveau formation
        synchronizer.construct_classe_to_niv_formation(etab_context, ldap.search_eleve_classe_and_niveau(uai))

        #Synchronisation des enseignants de cet établissement
        enseignants = ldap.search_enseignant(None, uai, tous=True)
        for enseignant in enseignants:
            synchronizer.handle_enseignant(etab_context, enseignant)

        #Récupération des cohortes dane pour les lycées depuis le ldap
        cohort_elv_lycee_en_ldap = []
        cohort_ens_lycee_en_ldap = []
        cohort_dir_lycee_en_ldap = []

        #On vérifie que l'établissement de test est bien un lycée
        assert etab_context.lycee
        assert etab_context.etablissement_en

        cohort_elv_lycee_en_ldap.extend(ldap.search_eleve_uid(uai=uai))
        cohort_ens_lycee_en_ldap.extend(ldap.search_enseignant_profil_uid(profil="National_ENS",\
         uai=uai, tous=False))
        cohort_dir_lycee_en_ldap.extend(ldap.search_personnel_direction_uid(uai=uai))

        #On vérifie qu'on a bien récupéré les cohortes du ldap
        assert cohort_elv_lycee_en_ldap
        assert cohort_ens_lycee_en_ldap
        assert cohort_dir_lycee_en_ldap

        #Suppression manuelle dans certaines cohortes d'utilisateurs spécifiques dans le ldap
        #On teste pour chaque type d'utilisateur
        #Type Eleve
        cohort_elv_lycee_en_ldap.remove("f154039k")
        #Type Enseignant
        cohort_ens_lycee_en_ldap.remove("f17100gv")
        #Type personnel de direction
        cohort_dir_lycee_en_ldap.remove("f08005nl")

        #Récupération des cohortes dane lycée dans le ldap
        cohort_dane_lycee = {UserType.ELEVE:cohort_elv_lycee_en_ldap,
                            UserType.ENSEIGNANT:cohort_ens_lycee_en_ldap,
                            UserType.PERSONNEL_DE_DIRECTION:cohort_dir_lycee_en_ldap}

        #Récupération de ce qu'on a en bd avant la supression
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Élèves des lycées de l'éducation nationale"
                        })
        cohorts_elv_lyc_bd =[result[0] for result in db.mark.fetchall()]

        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Enseignants des lycées de l'éducation nationale"
                        })
        cohorts_ens_lyc_bd =[result[0] for result in db.mark.fetchall()]

        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Personnel de direction des lycées de l'éducation nationale"
                        })
        cohorts_dir_lyc_bd =[result[0] for result in db.mark.fetchall()]

        #Purge des cohortes lycées
        synchronizer.purge_cohort_dane_lycee_en(cohort_dane_lycee)

        #On s'assure que les utilisateurs qu'on à supprimé des cohortes dans le ldap
        #ont bien aussi été supprimés des cohortes dans moodle
        #Type élèves : récupération des membres de la cohorte des élèves des lycées
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Élèves des lycées de l'éducation nationale"
                        })

        results = [result[0] for result in db.mark.fetchall()]
        assert 'f154039k' not in results
        assert len(results) == len(cohorts_elv_lyc_bd)-1

        #Type enseignants : récupération des membres de la cohorte des enseignants des lycées
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Enseignants des lycées de l'éducation nationale"
                        })

        results = [result[0] for result in db.mark.fetchall()]
        assert 'f17100gv' not in results
        assert len(results) == len(cohorts_ens_lyc_bd)-1

        #Type personnels de direcrtion : récupération des membres de la cohorte des personnels de direction des lycées
        db.mark.execute("SELECT {entete}user.username FROM {entete}cohort_members AS cohort_members"
                        " INNER JOIN {entete}cohort AS cohort"
                        " ON cohort_members.cohortid = cohort.id"
                        " INNER JOIN {entete}user"
                        " ON cohort_members.userid = {entete}user.id"
                        " WHERE cohort.name = %(cohortname)s".format(entete=db.entete),
                        params={
                            'cohortname': "Personnel de direction des lycées de l'éducation nationale"
                        })

        results = [result[0] for result in db.mark.fetchall()]
        assert 'f08005nl' not in results
        assert len(results) == len(cohorts_dir_lyc_bd)-1


    def test_anonymize_or_delete_eleves(self, ldap: Ldap, db: Database, config: Config,
                                        mocker: pytest_mock.plugin.MockerFixture):
        """
        Teste la suppression/anonymisation des élèves devenus inutiles :
            - Ajout d'utilisateurs directement dans moodle qui ne sont pas présents dans le ldap
                - Variation de la date de dernière connexion
                - Inscriptions ou non à des cours
                - Références ou non à des cours
            - Suppression d'un utilisateur dans le ldap qui est présent dans moodle

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        :param mocker: L'objet permettant de mocker des fonctions
        """

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
        ldap_eleves = ldap.search_eleve(uai="0290009C")
        for eleve in ldap_eleves:
            synchronizer.handle_eleve(etab_context, eleve)

        #Ajout dans la BD des élèves, cours et références factices
        db_utils.insert_eleves(db, config)

        #Récupération des utilisateurs de la bd coté moodle
        db_valid_users = db.get_all_valid_users()

        #Mocks
        #Attention on mock les fonctions dans synchronizer.py et pas dans webserviceutils.py
        #Ici on a .WebService mais c'est pour indiquer l'objet WebService et non pas le fichier
        mocker.patch('synchromoodle.synchronizer.WebService.get_courses_user_enrolled',\
         side_effect=mock_utils.fake_get_courses_user_enrolled_test_eleves)
        mock_unenrol_user_from_course = mocker.patch('synchromoodle.synchronizer.WebService.unenrol_user_from_course')
        mock_delete_courses = mocker.patch('synchromoodle.synchronizer.WebService.delete_courses')
        mock_delete_users = mocker.patch('synchromoodle.synchronizer.WebService.delete_users')
        mock_anon_users = mocker.patch('synchromoodle.synchronizer.Database.anonymize_users')

        #Suppression d'un utilisateur dans le ldap
        ldap_eleves.pop()

        #Appel direct à la méthode s'occupant d'anonymiser et de supprimer les utilisateurs dans la synchro
        synchronizer.anonymize_or_delete_users(ldap_eleves, db_valid_users)

        #Vérification de la suppression des utilisateurs
        #Attention on bien 1 seul call à la méthode car on supprime tous les utilisateurs d'un coup
        mock_delete_users.assert_has_calls([call([492285,492288,492290,492291,492293,492294])])

        #Vérification de l'anonymisation des utilisateurs
        mock_anon_users.assert_has_calls([call([492286,492287,492289,492292,492295])])

        #On vérifie aussi que l'on a pas fait d'appels aux méthodes qui ne doivent pas reçevoir d'appels
        mock_delete_courses.assert_not_called()
        mock_unenrol_user_from_course.assert_not_called()


    def test_anonymize_or_delete_enseignants(self, ldap: Ldap, db: Database, config: Config,
                                             mocker: pytest_mock.plugin.MockerFixture):
        """
        Teste la suppression/anonymisation des enseignants devenus inutiles :
            - Ajout d'utilisateurs directement dans moodle qui ne sont pas présents dans le ldap
                - Variation de la date de dernière connexion
                - Inscriptions ou non à des cours (hors enseignant)
                - Références ou non à des cours
                - Possession de cours (rôles enseignant ou propriétaire de cours)
            - Suppression d'un utilisateur dans le ldap qui est présent dans moodle

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        :param mocker: L'objet permettant de mocker des fonctions
        """

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
        ldap_enseignants = ldap.search_enseignant(uai="0290009C")
        for enseignant in ldap_enseignants:
            synchronizer.handle_enseignant(etab_context, enseignant)

        #Ajout dans la BD des enseignants, cours et références factices
        db_utils.insert_enseignants(db, config)

        #Récupération des utilisateurs de la bd coté moodle
        db_valid_users = db.get_all_valid_users()

        #Mocks
        mocker.patch('synchromoodle.synchronizer.WebService.get_courses_user_enrolled',\
            side_effect=mock_utils.fake_get_courses_user_enrolled_test_enseignants)
        mocker.patch('synchromoodle.synchronizer.WebService.unenrol_user_from_course')
        mock_delete_courses = mocker.patch('synchromoodle.synchronizer.WebService.delete_courses')
        mock_delete_users = mocker.patch('synchromoodle.synchronizer.WebService.delete_users')
        mock_anon_users = mocker.patch('synchromoodle.synchronizer.Database.anonymize_users')
        mocker.patch('synchromoodle.synchronizer.Synchronizer.backup_course',\
            return_value=config.webservice.backup_success_re)

        #Suppression d'un enseignant dans le ldap
        ldap_enseignants.pop()

        #Appel direct à la méthode s'occupant d'anonymiser et de supprimer les utilisateurs dans la synchro
        synchronizer.anonymize_or_delete_users(ldap_enseignants, db_valid_users)

        #Vérification de la suppression des utilisateurs
        mock_delete_users.assert_has_calls([call([492215,492231,492232])])

        #Vérification de l'anonymisation des utilisateurs
        mock_anon_users.assert_has_calls([call([492220,492222,492223,492224,492226,492227,492228,492230])])

        #Vérification que des traitements ont été lancés sur les cours de certains enseignants
        mock_delete_courses.assert_has_calls([call([37005]),call([37007])])


    def test_course_backup(self, ldap: Ldap, db: Database, config: Config, mocker: pytest_mock.plugin.MockerFixture):
        """
        Teste le traitement des cours des enseignants devenus inutiles :
            - Ajout d'enseignants directement dans moodle qui ne sont pas présents dans le ldap
            - Création de cours pour ces enseignants
            - Inscription ou non aux cours avec des rôles différents (propriétaire ou simple enseignant)

        :param ldap: L'objet Ldap pour intéragir avec le ldap dans le docker
        :param db: L'objet Database pour intégragir avec le mariabd dans le docker
        :param config: La configuration globale pendant la session de tests
        :param mocker: L'objet permettant de mocker des fonctions
        """

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

        #Synchronisation des enseignants
        ldap_enseignants = ldap.search_enseignant(uai="0290009C")
        for enseignant in ldap_enseignants:
            synchronizer.handle_enseignant(etab_context, enseignant)

        #Ajout dans la BD des enseignants, cours et références factices
        db_utils.insert_courses(db, config)

        #Récupération des utilisateurs de la bd coté moodle
        db_valid_users = db.get_all_valid_users()

        #Mocks
        mocker.patch('synchromoodle.synchronizer.WebService.get_courses_user_enrolled',\
            side_effect=mock_utils.fake_get_courses_user_enrolled_test_cours)
        mock_unenrol_user_from_course = mocker.patch('synchromoodle.synchronizer.WebService.unenrol_user_from_course')
        mock_delete_courses = mocker.patch('synchromoodle.synchronizer.WebService.delete_courses')
        mock_delete_users = mocker.patch('synchromoodle.synchronizer.WebService.delete_users')
        mock_anon_users = mocker.patch('synchromoodle.synchronizer.Database.anonymize_users')
        mocker.patch('synchromoodle.synchronizer.Synchronizer.backup_course',\
            return_value=config.webservice.backup_success_re)

        #Appel direct à la méthode s'occupant d'anonymiser et de supprimer les utilisateurs dans la synchro
        synchronizer.anonymize_or_delete_users(ldap_enseignants, db_valid_users)

        #Cours qui doit être supprimé
        mock_delete_courses.assert_has_calls([call([37003])])

        #Cours dont doit être désinscrit l'utilisateur
        mock_unenrol_user_from_course.assert_has_calls([call(492216,37001),call(492216,37002),
                                                        call(492216,37004),call(492216,37005)])

        #On n'est pas censé anonymiser ou supprimer des utilisateurs dans les cas testés
        mock_anon_users.assert_not_called()
        mock_delete_users.assert_not_called()
