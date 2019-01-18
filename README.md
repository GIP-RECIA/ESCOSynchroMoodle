# ESCOSynchroMoodle

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

- Installer les prérequis pour OpenLDAP

Voir http://www.python-ldap.org/en/latest/installing.html#build-prerequisites

```bash
sudo apt-get install build-essential python3-dev python2.7-dev libldap2-dev libsasl2-dev
```

- Installer l'environnement virtuel avec les dépendances

```bash
pipenv install --dev --python=3.5
```

