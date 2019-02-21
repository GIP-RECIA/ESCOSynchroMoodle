# ESCOSynchroMoodle

[![Build Status](http://img.shields.io/travis/GIP-RECIA/ESCOSynchroMoodle.svg)](https://travis-ci.org/GIP-RECIA/ESCOSynchroMoodle)
[![Coveralls](http://img.shields.io/coveralls/GIP-RECIA/ESCOSynchroMoodle.svg)](https://coveralls.io/github/GIP-RECIA/ESCOSynchroMoodle)

Ce script permet la synchronisation des données de l'annuaire LDAP avec Moodle. Il nécessite Python 3.5+.

# Usage

```bash
usage: __main__.py [-h] [-c CONFIG]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Chemin vers un fichier de configuration. Lorsque cette
                        option est utilisée plusieurs fois, les fichiers de
                        configuration sont alors fusionnés.
```

# Environnement de développement

### Prérequis

 - Python 3.5+
 - [Pipenv](https://github.com/pypa/pipenv)

##### Note sous windows

Il est possible d'installer l'environnement de développement et d'executer le script sous windows, via le wrapper `py`
installé par défaut. Il est alors nécessaire de préfixer les commandes qui suivent par `py -m`.

### Initialiser l'environnement virtuel et les dépendances

Les dépendances et l'environnement virtuel sont gérées par [pipenv](https://github.com/pypa/pipenv).

La commande suivante permet d'initialiser l'environnement et d'installer les dépendances.

```bash
pipenv install --dev --python=3.5
```

### Executer le script à partir des sources

```bash
pipenv run python -m synchromoodle -c config/test.yml
```

## Construire le binaire à partir des sources

```bash
pipenv run python setup.py bdist_wheel
```

# Déploiement

Le déploiement peut se faire au sein d'un Python installé directement sur le système, ou dans un virtualenv. Il est 
possible d'utiliser [pyenv](https://github.com/pyenv/pyenv) pour installer une version spécifique de Python sous Linux 
et créer un virtualenv pour le script.

La dernière version du package wheel est disponible dans l'onglet [Release du github](https://github.com/GIP-RECIA/ESCOSynchroMoodle/releases).

```
pip3 install synchromoodle-x.x.x-py3-none-any.whl
```

# Executer à partir du script installé

*Après avoir créé le fichier de configuration (voir section Configuration)*

```bash
python3 -m synchromoodle -c config/test.yml
```

# Configuration

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

#### actions

| Propriété            | Description                                                          | Type                 |
|----------------------|----------------------------------------------------------------------|:--------------------:|
| id                   | Identifiant de l'action (libre)                                      | Chaine de caractères |
| type                 | Type d'action à éxecuter (nom de la fonction dans `actions.py`)      | Chaine de caractères |
| timestamp_store      | Informations du fichier de stockage des dates de dernières exécution | Dictionnaire         |
| etablissements       | Informations générales sur les établissements                        | Dictionnaire         |
| inter_etablissements | Informations générales sur les inter-établissements                  | Dictionnaire         |
| inspecteurs          | Informations générales sur les inspecteurs                           | Dictionnaire         |


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
| id_role_enseignant         | Id pour le role enseignant                                               | 3                             |     Nombre entier    |
| id_role_eleve              | Id pour le role eleve                                                    | 5                             |     Nombre entier    |
| id_role_inspecteur         | Id pour le role inspecteur                                               | 9                             |     Nombre entier    |
| id_role_directeur          | Id pour le role directeur                                                | 18                            |     Nombre entier    |
| id_role_utilisateur_limite | Id pour le role d'utilisateur avec droits limites                        | 14                            |     Nombre entier    |
| type_structure_cfa         | Type de structure d'un CFA                                               | "CFA"                         | Chaine de caractères |
| type_structure_clg         | Type de structure d'un college                                           | "COLLEGE"                     | Chaine de caractères |

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

| Propriété     | Description                 | Valeur par défaut                                  |         Type         |
|---------------|-----------------------------|----------------------------------------------------|:--------------------:|
| uri           | URI du serveur LDAP         | "ldap://192.168.1.100:9889"                        | Chaine de caractères |
| username      | Utilisateur                 | "cn=admin,ou=administrateurs,dc=esco-centre,dc=fr" | Chaine de caractères |
| password      | Mot de passe                | "admin"                                            | Chaine de caractères |
| baseDN        | DN de base                  | "dc=esco-centre,dc=fr"                             | Chaine de caractères |
| structuresRDN | OU pour les structures      | "ou=structures"                                    | Chaine de caractères |
| personnesRDN  | OU pour les personnes       | "ou=people"                                        | Chaine de caractères |
| groupsRDN     | OU pour les groupes         | "ou=groups"                                        | Chaine de caractères |
| adminRDN      | OU pour les administrateurs | "ou=administrateurs"                               | Chaine de caractères |

###### timestamp_store

| Propriété | Description                                                                                                    | Valeur par défaut |         Type         |
|-----------|----------------------------------------------------------------------------------------------------------------|-------------------|:--------------------:|
| file      | Fichier contenant les dates de traitement précedent pour les établissements                                    | "timestamps.txt"  | Chaine de caractères |
| separator | Séparateur utilisé dans le fichier de traitement pour séparer l'etablissement des date de traitement précedent | "-"               | Chaine de caractères |

###### etablissements

| Propriété                     | Description                                                                                          | Valeur par défaut                  |                   Type                  |
|-------------------------------|------------------------------------------------------------------------------------------------------|------------------------------------|:---------------------------------------:|
| etabRgp                       | Regroupement d'etablissements                                                                        | []                                 | Liste de regroupements d'etablissements |
| inter_etab_categorie_name     | Nom de la catégorie inter-etablissement                                                              | "Catégorie Inter-Établissements"   |           Chaine de caractères          |
| inter_etab_categorie_name_cfa | Nom de la catégorie inter-etablissement pour les CFA                                                 | "Catégorie Inter-CFA"              |           Chaine de caractères          |
| listeEtab                     | Liste des établissements                                                                             | []                                 |      Liste de chaines de caractères     |
| listeEtabSansAdmin            | Etablissements sans administrateurs                                                                  | []                                 |      Liste de chaines de caractères     |
| listeEtabSansMail             | Etablissements dont le mail des professeurs n'est pas synchronise                                    | []                                 |      Liste de chaines de caractères     |
| prefixAdminMoodleLocal        | Préfixe de l'attribut "isMemberOf" indiquant que l'utilisateur est un administrateur local de Moodle | "(esco&#124;clg37):admin:Moodle:local:" |           Chaine de caractères          |
| prefixAdminLocal              | Prefix de l'attribut "isMemberOf" indiquant que l'utilisateur est un administrateur local            | "(esco&#124;clg37):admin:local:"        |           Chaine de caractères          |

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
| ldap_attribut_user        | Attribut utilisé pour determiner les inspecteurs                         | "ESCOPersonProfils" |      Chaine de caractères      |
| ldap_valeur_attribut_user | Valeur de l'attribute pour déterminer les inspecteurs                    | ["INS"]             | Liste de chaines de caractères |
| cle_timestamp             | Clé pour stocker le timestamp du dernier traitement inter-etablissements | "INSPECTEURS"       |      Chaine de caractères      |

#### Exemple de configuration

[config/exemple.yml](./config/exemple.yml)
