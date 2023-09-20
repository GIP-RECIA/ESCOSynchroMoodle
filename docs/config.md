# Configuration YAML

Le script fonctionne à l'aide d'un fichier de configuration au format YAML. Il est possible de spécifier plusieurs
fichiers de configuration, en utilisant plusieurs fois le flag -c, les configuration de chaque fichier sont alors
fusionnées.

La structure de la configuration est modélisée par les classes situées dans
[synchromoodle/config.py](./synchromoodle/config.py)

#### Propriétés

| Propriété            | Description                                                          | Type         |
|----------------------|----------------------------------------------------------------------|:------------:|
| constantes           | Constantes utilisées par le script                                   | Dictionnaire |
| database             | Informations de connexion à la bdd                                   | Dictionnaire |
| ldap                 | Informations de connexion au LDAP                                    | Dictionnaire |
| logging              | Configuration de logging (module standard logging, voir dictConfig)  | Dictionnaire |
| actions              | Liste des actions a exécuter avec la configuration associée          | Tableau      |
| delete               | Informations pour la suppression de données                          | Dictionnaire |
| webservice           | Informations de connexion au webservice moodle                       | Dictionnaire |
| dane                 | Informations relatives à la dane                                     | Dictionnaire |

#### actions

| Propriété            | Description                                                          | Type                 |
|----------------------|----------------------------------------------------------------------|:--------------------:|
| id                   | Identifiant de l'action (libre)                                      | Chaine de caractères |
| type                 | Type d'action à éxecuter (nom de la fonction dans `actions.py`)      | Chaine de caractères |
| timestamp_store      | Informations du fichier de stockage des dates de dernières exécution | Dictionnaire         |
| etablissements       | Informations générales sur les établissements                        | Dictionnaire         |
| inter_etablissements | Informations générales sur les inter-établissements                  | Dictionnaire         |
| inspecteurs          | Informations générales sur les inspecteurs                           | Dictionnaire         |
| specific_cohorts     | Informations sur les cohortes à créer spécifiquement                 | Dictionnaire         |

###### constantes

| Propriété                  | Description                                                              | Valeur par défaut             |         Type         |
|----------------------------|--------------------------------------------------------------------------|-------------------------------|:--------------------:|
| default_moodle_theme       | Thèmes par défault pour les utilisateurs inter-etabs                     | "netocentre"                  | Chaine de caractères |
| default_mail_display       | Par défaut, les mails sont uniquement affichés aux participants du cours | 2                             |     Nombre entier    |
| default_mail               | Email utilise lorsque les personnes n'ont pas d'email dans le LDAP       | "non_renseigne@netocentre.fr" | Chaine de caractères |
| default_domain             | Domaine par défaut                                                       | "lycees.netocentre.fr"        | Chaine de caractères |
| id_instance_moodle         | Id de l'instance concernant Moodle                                       | 1                             |     Nombre entier    |
| niveau_ctx_categorie       | Niveau de contexte pour une categorie                                    | 40                            |     Nombre entier    |
| niveau_ctx_cours           | Niveau de contexte pour un cours                                         | 50                            |     Nombre entier    |
| niveau_ctx_forum           | Niveau de contexte pour un forum                                         | 70                            |     Nombre entier    |
| niveau_ctx_bloc            | Niveau de contexte pour un bloc                                          | 80                            |     Nombre entier    |
| id_role_admin              | Id pour le role admin                                                    | 1                             |     Nombre entier    |
| id_role_createur_cours     | Id pour le role createur de cours                                        | 2                             |     Nombre entier    |
| id_role_proprietaire_cours | Id pour le role propriétaire de cours                                    | 11                            |     Nombre entier    |
| id_role_enseignant         | Id pour le role enseignant                                               | 3                             |     Nombre entier    |
| id_role_eleve              | Id pour le role eleve                                                    | 5                             |     Nombre entier    |
| id_role_directeur          | Id pour le role directeur                                                | 18                            |     Nombre entier    |
| id_role_utilisateur_limite | Id pour le role d'utilisateur avec droits limites                        | 14                            |     Nombre entier    |
| type_structure_cfa         | Type de structure d'un CFA                                               | "CFA"                         | Chaine de caractères |
| type_structure_clg         | Type de structure d'un college                                           | "COLLEGE"                     | Chaine de caractères |
| anonymous_phone            | Valeur assignée aux numeros de telephones des utilisateurs anonymisés    | "0606060606"                  | Chaine de caractères |
| anonymous_name             | Valeur assignée aux champs divers du profil des utilisateurs anonymisés  | "Anonyme"                     | Chaine de caractères |
| anonymous_mail             | Adresse email assignée aux utilisateurs anonymisés                       | "Anonyme"                     | Chaine de caractères |
| cohortname_pattern_eleves_classe | Pattern à appliquer pour le nom des cohortes de classes d'élèves | "Élèves de la Classe %" | Chaine de caractères |
| cohortidnumber_pattern_eleves_classe | Pattern à appliquer pour l'idnumber des cohortes de classes d'élèves | "Classe %" | Chaine de caractères |
| cohortdesc_pattern_eleves_classe | Pattern à appliquer pour la description des cohortes de classes d'élèves | "Élèves de la Classe %" | Chaine de caractères |
| cohortname_pattern_eleves_niv_formation | Pattern à appliquer pour le nom des cohortes de niveau de formation d'élèves | "Élèves du Niveau de formation %" | Chaine de caractères |
| cohortidnumber_pattern_eleves_niv_formation | Pattern à appliquer pour l'idnumber des cohortes de niveau de formation d'élèves | "Élèves du Niveau de formation %" | Chaine de caractères |
| cohortdesc_pattern_eleves_niv_formation | Pattern à appliquer pour la description des cohortes de niveau de formation d'élèves | "Élèves avec le Niveau de formation %" | Chaine de caractères |
| cohortname_pattern_enseignants_classe | Pattern à appliquer pour le nom des cohortes de classes d'enseignants | "Profs de la Classe %" | Chaine de caractères |
| cohortidnumber_pattern_enseignants_classe | Pattern à appliquer pour l'idnumber des cohortes de classes d'enseignants | "Profs de la Classe %" | Chaine de caractères |
| cohortdesc_pattern_enseignants_classe | Pattern à appliquer pour la description des cohortes de classes d'enseignants | "Enseignants de la Classe" | Chaine de caractères |
| cohortname_pattern_enseignants_niv_formation | Pattern à appliquer pour le nom des cohortes de niveau de formation d'enseignants | "Profs du niveau de formation %" | Chaine de caractères |
| cohortidnumber_pattern_enseignants_niv_formation | Pattern à appliquer pour l'idnumber des cohortes de niveau de formation d'enseignants | "Profs du niveau de formation %" | Chaine de caractères |
| cohortdesc_pattern_enseignants_niv_formation | Pattern à appliquer pour la description des cohortes de niveau de formation d'enseignants | "Enseignants avec le Niveau de formation % | Chaine de caractères |
| cohortname_pattern_enseignants_etablissement | Pattern à appliquer pour le nom des cohortes d'établissements d'enseignants | "Profs de l'établissement %" | Chaine de caractères |
| cohortidnumber_pattern_enseignants_etablissement | Pattern à appliquer pour l'idnumber des cohortes d'établissements d'enseignants | "Profs de l'établissement %" | Chaine de caractères |
| cohortdesc_pattern_enseignants_etablissement | Pattern à appliquer pour la description des cohortes d'établissements d'enseignants | "Enseignants de l'établissement %" | Chaine de caractères |
| cohortname_pattern_re_eleves_classe | Regex à reconnaître pour le nom des cohortes de classes d'élèves | r'(Élèves de la Classe )(.*)$' | Chaine de caractères |
| cohortname_pattern_re_eleves_niv_formation | Regex à reconnaître pour le nom des cohortes de niveau de formation d'élèves | r'(Élèves du Niveau de formation )(.*)$' | Chaine de caractères |
| cohortname_pattern_re_enseignants_classe | Regex à reconnaître pour le nom des cohortes de classes d'enseignants | r'(Profs de la Classe )(.*)$' | Chaine de caractères |
| cohortname_pattern_re_enseignants_niv_formation | Regex à reconnaître pour le nom des cohortes de niveau de formation d'enseignants | r"(Profs du niveau de formation )(.*)$" | Chaine de caractères |
| cohortname_pattern_re_enseignants_etablissement | Regex à reconnaître pour le nom des cohortes d'établissements d'enseignants | r"(Profs de l'établissement )(.*)$" | Chaine de caractères |
| moodledatadir | Path vers le dossier moodledata | "" | Chaine de caractères |
| backup_destination | Chemin vers la destination des fichiers de backup des cours | "" | Chaine de caractères |

###### database

| Propriété | Description                                        | Valeur par défaut |         Type         |
|-----------|----------------------------------------------------|-------------------|:--------------------:|
| database  | Nom de la base de données                          | "moodle"          | Chaine de caractères |
| user      | Nom de l'utilisateur moodle                        | "moodle"          | Chaine de caractères |
| password  | Mot de passe de l'utilisateur moodle               | "moodle"          | Chaine de caractères |
| host      | Adresse IP ou nom de domaine de la base de données | "192.168.1.100"   | Chaine de caractères |
| port      | Port TCP                                           | 9806              |     Nombre entier    |
| entete    | Entêtes des tables                                 | "mdl_"            | Chaine de caractères |
| charset   | Charset à utiliser pour la connexion               | "utf8"            | Chaine de caractères |

###### ldap

| Propriété      | Description                 | Valeur par défaut                                  |         Type         |
|----------------|-----------------------------|----------------------------------------------------|:--------------------:|
| uri            | URI du serveur LDAP         | "ldap://192.168.1.100:9889"                        | Chaine de caractères |
| username       | Utilisateur                 | "cn=admin,ou=administrateurs,dc=esco-centre,dc=fr" | Chaine de caractères |
| password       | Mot de passe                | "admin"                                            | Chaine de caractères |
| base_dn        | DN de base                  | "dc=esco-centre,dc=fr"                             | Chaine de caractères |
| structures_rdn | OU pour les structures      | "ou=structures"                                    | Chaine de caractères |
| personnes_rdn  | OU pour les personnes       | "ou=people"                                        | Chaine de caractères |
| groups_rdn     | OU pour les groupes         | "ou=groups"                                        | Chaine de caractères |
| admin_rdn      | OU pour les administrateurs | "ou=administrateurs"                               | Chaine de caractères |
| page_size      | Taille d'une page pour les grandes requêtes | 10000                              | Nombre entier        |

###### delete

| Propriété               | Description                                                                                                           | Valeur par défaut |           Type           |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------|-------------------|:------------------------:|
| ids_roles_teachers      | Ids des roles considérés comme enseignants pour la suppression                                                        | [2]               | Liste de Nombres entiers |
| delay_anonymize_student | Délai, en jours, avant de anonymiser un élève qui n'est plus présent dans l'annuaire LDAP                             | 60                |      Nombres entiers     |
| delay_delete_student    | Délai, en jours, avant de supprimer un élève qui n'est plus présent dans l'annuaire LDAP                              | 90                |      Nombres entiers     |
| delay_anonymize_teacher | Délai, en jours, avant d'anonymiser un enseignant qui n'est plus présent dans l'annuaire LDAP                         | 90                | Nombres entiers          |
| delay_delete_teacher    | Délai, en jours, avant de supprimer un enseignant qui n'est plus présent dans l'annuaire LDAP                         | 395               | Nombres entiers          |
| delay_backup_course     | Délai, en jours, avant de sauvegarder un cours inutilisé                                                              | 365               | Nombres entiers          |
| delay_unused_course     | Délai, en jours, avant de sauvegarder un cours non accédé                                                             | 360               | Nombres entiers          |
| delay_force_delete      | Délai, en jours, avant de supprimer un compte qui n'est plus présent dans l'annuaire LDAP peut importe ses références | 1095              | Nombres entiers          |
| purge_cohorts           | Paramétrage de la purge des cohortes                                                                                  | False             | Booléen                  |
| purge_zones_privees     | Paramétrage de la purge des zones privées                                                                             | False             | Booléen                  |

###### webservice

| Propriété         | Description                                                                                                               | Valeur par défaut                                                  |         Type         |
|-------------------|---------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------|:--------------------:|
| token             | Token d'accès au webservice Moodle                                                                                        | ""                                                                 | Chaine de caractères |
| moodle_host       | Host HTTP cible pour accéder au webservice Moodle SANS '/' FINAL                                                          | ""                                                                 | Chaine de caractères |                                               | Chaine de caractères |
| user_delete_pagesize        | Nombre d'utilisateurs maximum supprimés en un seul     appel au WebService                                                                      | 50 | Nombres entiers |

###### dane

| Propriété     | Description                 | Valeur par défaut                                  |         Type         |
|---------------|-----------------------------|----------------------------------------------------|:--------------------:|
| dane_attribut | Attribut de la dane pour indiquer une appartenance à un groupe | "isMemberOf"  | Chaine de caractères |
| dane_user | Valeur du filtre pour les utilisateurs de la dane dans le ldap  | "acad:Services_Academique:ACADEMIE D ORLEANS-TOURS_0450080T:Groupes locaux:DANE" | Chaine de caractères |
| dane_user_medic | Valeur du filtre pour les utilisateurs médicaux-sociaux de la dane | "acad:Services_Academique:ACADEMIE D ORLEANS-TOURS_0450080T:PERSONNELS MEDICO-SOCIAUX"  | Chaine de caractères |
| cohort_medic_dane_name | Nom de la cohorte dane des personnels médico-sociaux | "Personnels medico-sociaux" | Chaine de caractères |

###### timestamp_store

| Propriété | Description                                                                                                    | Valeur par défaut |         Type         |
|-----------|----------------------------------------------------------------------------------------------------------------|-------------------|:--------------------:|
| file      | Fichier contenant les dates de traitement précédent pour les établissements                                    | "timestamps.txt"  | Chaine de caractères |
| separator | Séparateur utilisé dans le fichier de traitement pour séparer l'etablissement des date de traitement précedent | "-"               | Chaine de caractères |

###### etablissements

| Propriété                     | Description                                                                                          | Valeur par défaut                  |                   Type                  |
|-------------------------------|------------------------------------------------------------------------------------------------------|------------------------------------|:---------------------------------------:|
| etab_rgp                       | Regroupement d'etablissements                                                                        | []                                 | Liste de regroupements d'etablissements |
| inter_etab_categorie_name     | Nom de la catégorie inter-etablissement                                                              | "Catégorie Inter-Établissements"   |           Chaine de caractères          |
| inter_etab_categorie_name_cfa | Nom de la catégorie inter-etablissement pour les CFA                                                 | "Catégorie Inter-CFA"              |           Chaine de caractères          |
| liste_etab                     | Liste des établissements                                                                             | []                                 |      Liste de chaines de caractères     |
| liste_etab_sans_admin            | Etablissements sans administrateurs                                                                  | []                                 |      Liste de chaines de caractères     |
| liste_etab_sans_mail             | Etablissements dont le mail des professeurs n'est pas synchronise                                    | []                                 |      Liste de chaines de caractères     |
| prefix_admin_moodle_local        | Préfixe de l'attribut "isMemberOf" indiquant que l'utilisateur est un administrateur local de Moodle | "(esco&#124;clg37):admin:Moodle:local:" |           Chaine de caractères          |
| prefix_admin_local              | Prefix de l'attribut "isMemberOf" indiquant que l'utilisateur est un administrateur local            | "(esco&#124;clg37):admin:local:"        |           Chaine de caractères          |

###### Regroupement d'etablissements

| Propriété | Description                               | Valeur par défaut |              Type              |
|-----------|-------------------------------------------|-------------------|:------------------------------:|
| nom       | Nom du regroupement d'etablissements      | ""                |      Chaine de caractères      |
| uais      | Liste des UAI constituant le regroupement | []                | Liste de chaines de caractères |

###### inter_etablissements

| Propriété                  | Description                                                                                             | Valeur par défaut                                       |              Type              |
|----------------------------|---------------------------------------------------------------------------------------------------------|---------------------------------------------------------|:------------------------------:|
| cohorts                    | Cohortes à synchroniser                                                                                 | {}                                                      |          Dictionnaire          |
| categorie_name             | Nom de la catégorie inter-etablissement                                                                 | "%%Cat%%gorie inter%%tablissements"                     |      Chaine de caractères      |
| ldap_attribut_user         | Attribut utilisé pour determiner les utilisateurs inter-établissement                                   | "isMemberOf"                                            |      Chaine de caractères      |
| ldap_valeur_attribut_user  | Valeurs possibles de l'attribut pour déterminer si l'utilisateur est un utilisateur inter-établissement | ["cfa:Applications:Espace_Moodle:Inter_etablissements"] | Liste de chaines de caractères |
| ldap_valeur_attribut_admin | Utilisateurs administrateurs de la section inter-etablissement                                          | "cfa:admin:Moodle:local:Inter_etablissements"           |      Chaine de caractères      |
| cle_timestamp              | Clé pour stocker le timestamp du dernier traitement inter-etablissements                                | "INTER_ETAB"                                            |      Chaine de caractères      |

###### inspecteurs

| Propriété                 | Description                                                              | Valeur par défaut   |              Type              |
|---------------------------|--------------------------------------------------------------------------|---------------------|:------------------------------:|
| ldap_attribut_user        | Attribut utilisé pour déterminer les inspecteurs                         | "ESCOPersonProfils" |      Chaine de caractères      |
| ldap_valeur_attribut_user | Valeur de l'attribut pour déterminer les inspecteurs                    | ["INS"]             | Liste de chaines de caractères |
| cle_timestamp             | Clé pour stocker le timestamp du dernier traitement inter-etablissements | "INSPECTEURS"       |      Chaine de caractères      |

###### specific_cohorts

| Propriété  | Description                                                              | Valeur par défaut | Type |
|------------|--------------------------------------------------------------------------|------------------ |------|
| cohorts | Dictionnaire ou la clé représente l'établissement dans lequel on veut créer les cohortes. La valeur est un dictionnaire où la clé est la valeur de l'attribut isMemberOf dans le ldap et la valeur le nom de la cohorte à créer dans moodle. | {} | Dictionnaire |

#### Exemple de configuration

- [config/test.yml](../config/test.yml)
- [config/nettoyage.yml](../config/nettoyage.yml)
