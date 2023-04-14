# Note sur le build par docker

## compiler le docker python

```
docker-compose build
```

## compiler mon pex

Se rendre dans le bash puis compiler :
```
cd docker-build
docker-compose run --rm python bash
cd /usr/share/app
pipenv install --dev --python=3.5
pipenv run python setup.py clean build bdist bdist_wheel bdist_pex --pex-args="--disable-cache"
exit
```


scp ../dist/synchromoodle-1.1.5.3.pex esco_synchro@192.168.1.83:/home/esco_synchro/ESCOSynchroMoodle/dist/.

## Lancer le pex

Pour l'env de test :
```
dist/synchromoodle-version.pex -c config/config_test.yml -c config/config_prod.yml
```

## Mise en place de la sauvegarde d'un cours

https://docs.moodle.org/3x/fr/Sauvegarde_de_cours#Sauvegarde_via_CLI_pour_les_administrateurs