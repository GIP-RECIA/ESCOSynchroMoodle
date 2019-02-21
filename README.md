# ESCOSynchroMoodle

[![Build Status](http://img.shields.io/travis/GIP-RECIA/ESCOSynchroMoodle.svg)](https://travis-ci.org/GIP-RECIA/ESCOSynchroMoodle)
[![Coveralls](http://img.shields.io/coveralls/GIP-RECIA/ESCOSynchroMoodle.svg)](https://coveralls.io/github/GIP-RECIA/ESCOSynchroMoodle)

# Installation de l'environnement python

## Prérequis

 - Python 3.5
 - [Pipenv](https://github.com/pypa/pipenv)

## Sous windows

- Installer l'environnement virtuel avec les dépendances

```bash
py -m pipenv install --dev --python=3.5
```

## Sous linux

- Installer l'environnement virtuel avec les dépendances

```bash
pipenv install --dev --python=3.5
```

# Utilisation

## Usage

```bash
usage: __main__.py [-h] [-c CONFIG]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Chemin vers un fichier de configuration.
```

## Exécution à partir des sources
```bash
pipenv run python -m synchromoodle -c config/test.yml
```

## Construction du binaire (wheel) à partir des sources
```bash
pipenv run python setup.py bdist_wheel
```

## Installation du package (wheel)

La dernière version du package wheel est disponible dans l'onglet [Release du github](https://github.com/GIP-RECIA/ESCOSynchroMoodle/releases).

```
pip3 install synchromoodle-x.x.x-py3-none-any.whl
```

## Execution à partir du package installé

(Après avoir créé le fichier de configuration)

```bash
python3 -m synchromoodle -c config/test.yml
```


## Configuration

Le script fonctionne à l'aide d'un (ou plusieurs) fichier de configuration au format YAML.

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

#### Exemple

```yaml
database:
  database: moodle
  user: moodle
  password: moodle
  host: 192.168.1.100
  port: 9806
  entete: mdl_
  charset: utf8
ldap:
  uri: "ldap://192.168.1.100:9889"
  username: "cn=admin,ou=administrateurs,dc=esco-centre,dc=fr"
  password: "admin"
  baseDN: "dc=esco-centre,dc=fr"
  structuresRDN: "ou=structures"
  personnesRDN: "ou=people"
  groupsRDN: "ou=groups"
  adminRDN: "ou=administrateurs"
actions:
- id: academique
  timestampStore:
    file: "trtAcademique_precedent.txt"
  etablissements:
    listeEtab: ["0450822X", "0410031L", "0371122U", "0450066C", "0451483T", "0410593X", "0410030K", "0370001A", "0360003H",
                "0370040T", "0370036N", "0451304Y", "0450051L", "0180008L", "0360011S", "0280657M", "0280036M", "0450062Y",
                "0280021W", "0360024F", "0410959V", "0371417P", "0280864M", "0450042B", "0370009J", "0360002G", "0370039S",
                "0180006J", "0410017W", "0450790P", "0451442Y", "0281047L", "0450064A", "0280925D", "0180007K", "0180042Y",
                "0371418R", "0360008N", "0180024D", "0180026F", "0280044W", "0360009P", "0281077U", "0410832G", "0180823X",
                "0180777X", "0360658V", "0180036S", "0180010N", "0180005H", "0180009M", "0280009H", "0280015P", "0280957N",
                "0280022X", "0360026H", "0360019A", "0360005K", "0371211R", "0370037P", "0370038R", "0370053G", "0370054H",
                "0371100V", "0410002E", "0410899E", "0410718H", "0410036S", "0451484U", "0451526P", "0450750W", "0450050K",
                "0450782F", "0451067R", "0280659P", "0360050J", "0451104F", "0180025E", "0180035R", "0280007F", "0280019U",
                "0280700J", "0281021H", "0360043B", "0370016S", "0370032J", "0370035M", "0370771M", "0370888P", "0371099U",
                "0371123V", "0371258S", "0410001D", "0450029M", "0450040Z", "0450043C", "0450049J", "0450786K", "0451037H",
                "0451462V", "0410860M", "0371159J", "0371204H", "0371316E", "0370011L", "0370991B", "0370041U", "0377777U",
                "0370006F", "0370015R", "0370768J", "0370791J", "0370792K", "0370799T", "0370886M", "0370887N", "0370994E",
                "0371101W", "0371158H", "0371191U", "0371248F", "0371391L", "0371397T", "0371403Z", "0371124W", "0370995F",
                "0370007G", "0370010K", "0371098T", "0370013N", "0371378X", "0370993D", "0370022Y", "0370034L", "0370766G",
                "0370044X", "0370045Y", "0370769K", "0370886M", "0370884K", "0371189S", "0370024A"]
    listeEtabSansMail: ["0371204H", "0371159J", "0370011L", "0370041U", "0370991B", "0371316E"]
- id: agricole
  timestampStore:
    file: "trtAgricole_precedent.txt"
  etablissements:
    prefixAdminMoodleLocal: "agri:admin:Moodle:local:"
    prefixAdminLocal: "agri:admin:local:"
    listeEtab: ["0410018X", "0180585N", "0280706R", "0370878D", "0450094H", "0451535Z", "0450027K", "0410629L", "0370781Y",
                "0360017Y", "0370794M", "0410626H"]
- id: cfa
  timestampStore:
    file: "trtCfa_precedent.txt"
  etablissements:
    prefixAdminMoodleLocal: "cfa:admin:Moodle:local:"
    prefixAdminLocal: "cfa:admin:local:"
    listeEtab: ["0180755y", "0180939y", "0180865t", "0180877f", "0280738a", "0280904f", "0281155d", "0333333y", "0360548a",
                "0360777z", "0360709a", "0370811f", "0370983t", "0370984u", "0371686g", "0371710h", "0371711j", "0371723x",
                "0410590u", "0410592w", "0410892y", "0411059d", "0411064j", "0450807h", "0450808j", "0450809k", "0450810l",
                "0450810q", "0451583b", "0451691u", "0451693w", "0451694x", "0451715v"]
    etabRgp:
      - nom: "CFA DU CHER"
        uais: ["0180755y", "0180939y", "0410892y"]
      - nom: "FORMASAT CFA Sport Animation Tourisme"
        uais: ["0451583b", "0281155d", "0411064j"]
      - nom: "CFA MFR Centre et Île-de-France"
        uais: ["0451715v", "0370983t", "0371686g", "0371710h", "0371711j", "0371723x", "0411059d", "0451691u",
                 "0451693w", "0451694x"]
- id: interetab-cfa
  type: interetab
  timestampStore:
    file: "trtInteretabCfa_precedent.txt"
  interEtablissements:
    categorie_name: 'Catégorie Inter-CFA'
    cohorts:
      "cfa:Inter_etablissements:Tous_Admin_local": "CFA : Tous les formateurs",
      "cfa:Inter_etablissements:Tous_Direction": "CFA : Tout le personnel de direction",
      "cfa:Inter_etablissements:Tous_Mediateur": "CFA : Tous les mediateurs",
      "cfa:Inter_etablissements:Tous_Documentation": "CFA : Tous les documentalistes",
      "cfa:Inter_etablissements:Tous_Profs": "CFA : Tous les formateurs",
      "cfa:Inter_etablissements:Tous_Responsable_Pedagogique": "CFA : Tous les responsables pedagogiques",
      "cfa:Inter_etablissements:Tous_Referent_DIMA": "CFA : Tous les referents DIMA",
      "cfa:Inter_etablissements:Tous_Referent_SCB": "CFA : Tous les referents savoirs et competences de base",
      "cfa:admin:local:*": "CFA : Tous les administrateurs ENT"
- id: interetab-all
  type: interetab
  timestampStore:
    file: "trtInteretabAll_precedent.txt"
  inter_etablissements:
    cohorts:
      "cfa:Inter_etablissements:Tous_Admin_local": "CFA : Tous les formateurs",
      "cfa:Inter_etablissements:Tous_Direction": "CFA : Tout le personnel de direction",
      "cfa:Inter_etablissements:Tous_Mediateur": "CFA : Tous les mediateurs",
      "cfa:Inter_etablissements:Tous_Documentation": "CFA : Tous les documentalistes",
      "cfa:Inter_etablissements:Tous_Profs": "CFA : Tous les formateurs",
      "cfa:Inter_etablissements:Tous_Responsable_Pedagogique": "CFA : Tous les responsables pedagogiques",
      "cfa:Inter_etablissements:Tous_Referent_DIMA": "CFA : Tous les referents DIMA",
      "cfa:Inter_etablissements:Tous_Referent_SCB": "CFA : Tous les referents savoirs et competences de base",
      "cfa:admin:local:*": "CFA : Tous les administrateurs ENT",
      "esco:Etablissements:*:Profs": "LYC : Tous les profs",
      "esco:admin:local:*": "LYC : Tous les administrateurs ENT",
      "esco:*:DIRECTION": "LYC : Tous les chefs d\'établissement",
      "esco:*:EDUCATION": "LYC : Tous les CPE",
      "agri:Etablissements:*:Profs": "LA : Tous les profs",
      "agri:admin:local:*": "LA : Tous les administrateurs ENT",
      "clg37:Etablissements:*:Profs": "CLG37 : Tous les profs",
      "clg37:admin:local:*": "CLG37 : Tous les administrateurs ENT",
      "clg37:*:DIRECTION": "CLG37 : Tous les chefs d\'établissement",
      "clg37:*:EDUCATION": "CLG37 : Tous les CPE"
- id: inspecteurs
  type: inspecteurs
  timestampStore:
    file: "trtInspecteurs_precedent.txt"
- id: nettoyage
  type: nettoyage

