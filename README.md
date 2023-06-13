# ESCOSynchroMoodle

[![Build Status](http://img.shields.io/travis/GIP-RECIA/ESCOSynchroMoodle.svg)](https://travis-ci.org/GIP-RECIA/ESCOSynchroMoodle)
[![Coveralls](http://img.shields.io/coveralls/GIP-RECIA/ESCOSynchroMoodle.svg)](https://coveralls.io/github/GIP-RECIA/ESCOSynchroMoodle)

Ce script permet la synchronisation des données de l'annuaire LDAP avec Moodle. Il nécessite Python 3.9+.

# Environnement de développement

### Prérequis

 - Python 3.9+
 - [Pipenv](https://github.com/pypa/pipenv)

##### Note sous windows

Il est possible d'installer l'environnement de développement et d'executer le script sous windows, via le wrapper `py`
installé par défaut. Il est alors nécessaire de préfixer les commandes qui suivent par `py -m`.

### Initialiser l'environnement virtuel et les dépendances

Les dépendances et l'environnement virtuel sont gérées par [pipenv](https://github.com/pypa/pipenv).

La commande suivante permet d'initialiser l'environnement et d'installer les dépendances.

```bash
pipenv install --dev
```

### Executer le script à partir des sources

```bash
pipenv run python -m synchromoodle -c config/test.yml
```

## Construire les binaires à partir des sources

```bash
pipenv run python setup.py clean build bdist bdist_wheel bdist_pex --pex-args="--disable-cache"
```

# Déploiement et exécution

Les packages du script sont disponibles dans l'onglet
[Release du github](https://github.com/GIP-RECIA/ESCOSynchroMoodle/releases).

Deux formats sont disponibles:

 - PEX, pour une exécution autonome
 - Wheel, pour une installation via pip sur un environnement Python existant.

## PEX

Le fichier `.pex` est un executable qui contient l'environnement virtuel, les dépendances et le script. Cela permet de
déployer le script sans avoir à se soucier de l'installation de Python.

```
./synchromoodle-x.x.x.pex -c config/test.yml
```

## Wheel

Le fichier `.whl` peut être installé via pip sur un Python système ou dans un virtualenv.

Il est possible d'utiliser [pyenv](https://github.com/pyenv/pyenv) pour installer une version spécifique de Python sous
Linux et créer un virtualenv pour le script.

```
pip3 install synchromoodle-x.x.x-py3-none-any.whl
python3 -m synchromoodle -c config/test.yml
```

## Documentation

Il est possible de générer une documentation sous forme de fichiers `.html` grâce à Sphinx. Il faut se placer dans le répertoire autodocs et taper la commande :

```
pipenv run make html
```

## Vérification de la qualité

Le code suit au mieux les recommandations officielles PEP8. Il est possible de vérifier la qualité du code avec la librairie pylint :

```
pipenv run python -m pylint [nom du package]
```

# Usage

```bash
usage: __main__.py [-h] [-v] [-c CONFIG]

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -c CONFIG, --config CONFIG
                        Chemin vers un fichier de configuration. Lorsque cette
                        option est utilisée plusieurs fois, les fichiers de
                        configuration sont alors fusionnés.
```

# Configuration

Voir [docs/config.md](./docs/config.md)
