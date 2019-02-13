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

## Exécution
```bash
python __main__.py [ -c config-file-name ] [ --purge-cohortes ]
```
```bash
options:
    -c, --config config-file-name
        Charge le fichier spécifié comme fichier de configuration.
        L'option est cumulable pour fusionner plusieurs fichiers de configuration différents.
        Par défaut, les fichiers chargés sont: "config.yml" et "config.yaml"
        
    --purge-cohortes
        Active la purge des cohortes et la suppression de celles devenues inutiles (vides)
```


## Configuration

Le script fonctionne à l'aide d'un (ou plusieur) fichier de configuration au format YAML.

#### Propriétés

| Propriété            | Description                                                          | Type         |
|----------------------|----------------------------------------------------------------------|:------------:|
| constantes           | Constantes utilisées par le script                                   | Dictionnaire |
| database             | Informations de connexion à la bdd                                   | Dictionnaire |
| ldap                 | Informations de connexion au LDAP                                    | Dictionnaire |
| timestamp_store      | Informations du fichier de stockage des dates de dernières exécution | Dictionnaire |
| etablissements       | Informations générales sur les établissements                        | Dictionnaire |
| inter_etablissements | Informations générales sur les inter-établissements                  | Dictionnaire |
| inspecteurs          | Informations générales sur les inspecteurs                           | Dictionnaire |
| actions              | Liste des actions a exécuter                                         | Tableau      |

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

| Propriété | Description                              | Valeur par défaut |              Type              |
|-----------|------------------------------------------|-------------------|:------------------------------:|
| nom       | Nom du regroupement d'etablissements     | ""                |      Chaine de caractères      |
| uais      | Liste des UAI consituant le regroupement | []                | Liste de chaines de caractères |

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
actions: ['default','interetab']
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
etablissements:
  prefixAdminMoodleLocal: "cfa:admin:Moodle:local:"
  prefixAdminLocal: "cfa:admin:local:"
  listeEtab: ["0180755y", "0180939y", "0180865t", "0180877f", "0280738a", "0280904f", "0281155d", "0333333y", "0360548a",
              "0360777z", "0360709a", "0370811f", "0370983t", "0370984u", "0371686g", "0371710h", "0371711j", "0371723x",
              "0410590u", "0410592w", "0410892y", "0411059d", "0411064j", "0450807h", "0450808j", "0450809k", "0450810l",
              "0450810q", "0451583b", "0451691u", "0451693w", "0451694x", "0451715v"]
  listeEtabSansMail: ["0371204H", "0371159J", "0370011L", "0370041U", "0370991B", "0371316E"]
  etabRgp:
    - nom: "CFA DU CHER"
      uais: ["0180755y", "0180939y", "0410892y"]
    - nom: "FORMASAT CFA Sport Animation Tourisme"
      uais: ["0451583b", "0281155d", "0411064j"]
    - nom: "CFA MFR Centre et Île-de-France"
      uais: ["0451715v", "0370983t", "0371686g", "0371710h", "0371711j", "0371723x", "0411059d", "0451691u",
               "0451693w", "0451694x"]
```
