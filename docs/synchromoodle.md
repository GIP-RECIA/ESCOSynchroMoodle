
# Module synchromoodle

## Librairies utilisées
Les librairies spécifiquement utilisées pour le module synchromoodle sont :
- mysql-connector-python : https://pypi.org/project/mysql-connector-python/
- ruamel-yaml : https://pypi.org/project/ruamel.yaml/
- ldap3 : https://pypi.org/project/ldap3/

## Description fichier par fichier
### \_\_main__.py
Ce fichier constitue le point d'entrée unique du programme, Concrètement, lorsque le script sera lancé, c'est ce fichier qui sera exécuté. C'est donc lui qui doit lancer toute la synchronisation en ayant bien chargé la configuration et les arguments sur la ligne de commande au préalable.

Les lignes :
```python
if __name__ == "__main__":
    main()
```
permettent de lancer la fonction main, qui contient le code qui va lancer la synchronisation.

Dans le code qui lance la synchronisation, on retrouve :

```python
for action in config.actions:
        try:
            action_func = getattr(actions, action.type)
        ...
        try:
            action_func(config, action)
```
Le principe est de lancer chaque action présente dans la configuration une par une. ``getattr`` retourne un objet représentant la fonction à lancer (parmi les différentes actions). Il suffit ensuite de faire un appel sur ce objet pour faire appel à la fonction représentant l'action configurée dans le fichier de config.

Le bloc entier est dans un ``try except`` afin de ne pas stopper tout le programme s'il y a une erreur lors de l’exécution d'une action, mais plutôt de continuer en passant à l'action suivante.

### actions.py
Ce fichier décrit les opérations réalisées par les différentes actions. Il définit une fonction par type d'action. Chaque action étant indépendantes des autres actions, au début de chaque action il faut se reconnecter à la BD et au LDAP, ainsi qu’initialiser le synchronizer :

 ```python
db = Database(config.database, config.constantes)
ldap = Ldap(config.ldap)

try:
	   db.connect()
	   ldap.connect()
	   synchronizer = Synchronizer(ldap, db, config, action)
	   synchronizer.initialize()
 ```

Ensuite, le corps de chaque fonction dépend de ce qui doit être réalisé par chaque action, mais toutes les fonctions s'appuient sur des appels au LDAP pour récupérer les données, puis des appels au synchronizer pour synchroniser les données. Ici, l'objectif est de ne pas avoir d'appels directs à la BD mais de passer le plus possible par le synchronizer.

### arguments.py
Ce fichier définit un ``ArgumentParser`` qui va se charger de décrire quels sont les arguments valides sur la ligne de commande et de les parser lorsque le programme est lancé. Il sert notamment à définir le nom du fichier de configuration utilisé.

### config.py
Ce fichier déclare les différentes classes nécessaires à la configuration. Chaque classe hérite de ``_BaseConfig``, et définit dans sa méthode ``__init__`` les différents éléments de configuration ainsi que leurs valeurs par défaut.  La méthode ``update`` permet de mettre à jour les attributs de la classe en fonction d'un fichier de configuration (lorsqu'on écrase les valeurs par défaut).

 La classe ``Config`` est la classe qui regroupe tous les différents objets de configuration. Pour ajouter un nouvel objet de configuration, il faut donc créer une classe héritant de``_BaseConfig``, définir ses attributs et ne pas oublier d'ajouter un attribut avec le type de la nouvelle classe créée dans  ``Config``.


### dbutils.py
Ce fichier définit l'objet ``Database`` est la couche d'accès à la base de données Moodle. Il contient également l'ensemble des fonctions dont la synchronisation a besoin pour insérer, modifier, ou supprimer des données dans la BD.

Toutes les requêtes à la BD suivent la même structure :
```python
#Définition d'une requête paramétrée sous forme d'une chaine de caractères
s = "REQUETE SQL"

#Exécution de la requête
self.mark.execute(s, params={'param': valeur}))

#Récupération de la valeur si besoin
ligne = self.mark.fetchall()
```
Pour ajouter une nouvelle requête à la base de données, il suffira d'ajouter une méthode dans la classe ``Database``.

### ldaputils.py
Ce fichier décrit les différentes classes représentant des objets du LDAP ainsi que la classe ``Ldap`` servant de couche d'accès au LDAP. La classe ``Ldap`` définit un ensemble de méthodes permettant de récupérer des données depuis le LDAP. Ces méthodes suivent toutes la même structure :
```python
#Définition du filtre
ldap_filter = "FILTRE LDAP"

#Récupération des données sous forme brute
self.connection.search(dn, ldap_filter, LEVEL, attributes= ['attribut1'])

#Transformation des données en objets python manipulables
return [MaClasseLdap(entry) for entry in self.connection.entries]
```
Pour ajouter une nouvelle requête au LDAP, il suffira d'ajouter une méthode dans la classe ``Ldap``.

### synchronizer.py
Ce fichier définit une classe ``Synchronizer`` qui est l'élément central de toute la synchronisation. C'est elle qui va décrire le comportement de la synchronisation : elle contient toutes les méthodes qui vont être appelées par les actions, et notamment la :

 - Synchronisation d'un établissement -> ``handle_etablissement``
 - Synchronisation d'un élève -> ``handle_eleve``
 - Synchronisation d'un enseignant- > ``handle_enseignant``
 - Synchronisation de la Dane -> ``handle_dane``
 - Synchronisation des cohortes spécifiques -> ``handle_specific_cohorts``
 - Synchronisation des inspecteurs -> ``handle_inspecteurs``
 - Synchronisation des utilisateurs Inter-Etablissements -> ``handle_user_interetab``
 - Suppression des cohortes en doublon -> ``handle_doublons``
 - Purge des cohortes -> ``purge_cohorts``
 - Suppression des cohortes vides -> ``delete_empty_cohorts``
 - Suppression/Anonymisation des utilisateurs inutiles -> ``anonymize_or_delete_users``
 - Suppression des cours -> ``check_and_process_user_courses``


### timestamp.py
Ce fichier définit une classe ``TimestampStore``qui gère les intéractions (écriture/lecture) avec le fichier permettant de stocker les Timestamps.

### webserviceutils.py
Ce fichier définit une classe  ``WebService`` servant de couche d'accès aux WebServices Moodle. Chaque méthode de cette classe représente un appel au WebService sur une URL particulière. Tous les appels aux WebServices suivent la même structure :
```python
#Définition des paramètres à passer à la requête au WebService
params = {}
params["param1"] = valeur1

#Appel au WebService
res = requests.get(url=self.url,
                   params={
                       'wstoken': self.config.token,
                       'moodlewsrestformat': "json",
                       'wsfunction': "fonction_du_ws_moodle",
                       **params
                   },
                   timeout=600)

try:
    #Récupération de la réponse en format JSON
    json_data = json.loads(res.text)
    #Levée d'une exception si on a une erreur dans le message de retour
    if json_data is not None and 'exception' in json_data:
        raise Exception(json_data['message'])
    #Si tout est correct, on retourne juste le message de retour
    return json_data
#Traitement d'un cas spécifique ou le message de retour est mal formaté par moodle    
except json.decoder.JSONDecodeError as exception:
    log.warning("Problème avec appel au WebService delete_courses. "
                "Message retourné : %s. Cours traités : %s",
                res.text, str(courseids))
    return None
```
Pour ajouter une nouvelle requête aux WebServices, il suffira d'ajouter une méthode dans la classe ``WebService``.
