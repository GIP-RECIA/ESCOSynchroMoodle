# Note sur le build par docker

## compiler le docker python

```
docker-compose build
```

## compiler mon pex

Se rendre dans le bash puis compiler :
```
docker-compose run --rm python bash
cd /usr/share/app
pipenv install --dev --python=3.5
pipenv run python setup.py clean build bdist bdist_wheel bdist_pex --pex-args="--disable-cache"
exit
```

## Lancer le pex

Pour l'env de test :
```
dist/synchromoodle-version.pex -c config/config_test.yml -c config/config_prod.yml
```