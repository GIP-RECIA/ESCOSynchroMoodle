
# Module de tests

## Librairies utilisées
Les librairies utilisées pour l’exécution des tests sont les librairies suivantes :
- pytest : https://pypi.org/project/pytest/
- pytest-docker : https://pypi.org/project/pytest-docker/
- pytest-mock : https://pypi.org/project/pytest-mock/

## Composition
Le module de test se compose de 2 dossiers et d'un ensemble de fichiers :
- À la racine du dossier **test** se trouve les fichiers contenants les fonctions de test qui vont être exécutées par pytest ;
- Dans le dossier **utils** se trouvent des fichiers contenant des fonctions auxiliaires permettant le bon déroulement des tests (insertion dans la base de données, chargement des fichiers ldif, etc..) ;
- Dans le dossier **data** se trouvent les fichiers de données à insérer dans la base de données ou dans le ldap.

## Utilisation
Pour lancer une série de tests, il faut lancer la commande : `python3 -m pipenv run python -m pytest` à la racine du projet. Il est possible de lancer seulement certaines fonctions choisies en rajoutant l'option `-k` de la manière suivante : `python3 -m pipenv run python -m pytest -k <nom_fonction>`.

L'option `-s` peut elle être utilisée à des fins de debug (de manière à voir les écritures dans la console, pour des `print()` par exemple). La commande est alors : `python3 -m pipenv run python -m pytest -s`.

## Synchronisation
Tous les tests vis à vis de la synchronisation suivent les mêmes principes :
- Création d'un docker LDAP et MariaDB
- Insertion des données dans le ldap avec un fichier ldif
- Insertion des tables dans MariaBD avec des fichiers .sql
- Insertion des données minimales dans MariaBD (rôles, contextes, ect..) afin de simuler un moodle
- Initialisation du `synchronizer`
- Appels aux méthodes du `synchronizer` pour la synchronisation des objets sur lesquels porte le test
- Vérification des résultats de la synchronisation

Pour chaque test, un nouveau docker est lancé. Ainsi, tous les tests sont complètements indépendants les uns des autres et les modifications d'un test dans la base de données ou dans le LDAP ne peuvent en aucun cas influencer sur le comportement d'un autre test.

## Mocks
Des mocks sont utilisés pour les tests de suppression. Comme aucun moodle n'est rééllement lancé, il n'est pas possible de faire des appels aux web service de moodle. Ainsi, ce sont les appels à ces fonctions (celles du web service) qu'on teste plutôt que les web service en eux-même.

## Nettoyage : comportement attendu
⚠ Abréviations pour les délais ⚠
- anon représente le délai d'anonymisation
- delete représente le délai de suppression conditionnée
- force représente le délai de suppression forcée
- backup représente le délai de backup d'un cours

### Elèves
Le tableau ci-dessous répertorie les **identifiants internes** des élèves pour les tests de nettoyage :
|Identifiant dans le code et identifiant en BD|Inscrit à un cours|Possède des références|Ni références ni inscriptions|
|-|-|-|-|
|D < anon|(K, 492296)|(L, 492297)|(M, 492298)|
|anon < D < delete|(J, 492295)|(D, 492289)|(G, 492292)|
|delete < D < force|(A, 492286)|(B, 492287)|(C, 492288)|
|force < D|(E, 492290)|(H, 492293)|(I, 492294)|
_L'utilisateur n'ayant jamais utilisé moodle porte les identifiants (F, 492291)._

Le tableau ci-dessous décrit le **comportement attendu** pour les tests de nettoyage vis à vis des élèves :
|Comportement attendu en fonction du délai|Inscrit à un cours|Possède des références|Ni références ni inscriptions|
|-|-|-|-|
|D < anon|Aucun|Aucun|Aucun|
|anon < D < delete|Anonymiser|Anonymiser|Anonymiser|
|delete < D < force|Anonymiser|Anonymiser|Supprimer|
|force < D|Supprimer|Supprimer|Supprimer|

### Enseignants
Le tableau ci-dessous répertorie les **identifiants internes** des enseignants pour les tests de nettoyage :
|Identifiant dans le code et identifiant en BD|Inscrit à un cours|Possède un cours|Possède des références|Ni références ni inscriptions|
|-|-|-|-|-|
|D < anon|(A, 492216)|(B, 492217)|(C, 492218)|(D, 492219)|
|anon < D < backup|(E, 492220)|(F, 492221)|(G, 492222)|(H, 492223)|
|backup D < delete|(I, 492224)|(J, 492225)|(K, 492226)|(L, 492227)|
|delete < D|(M, 492228)|(N, 492229)|(O, 492230)|(P, 492231)|
_L'utilisateur n'ayant jamais utilisé moodle porte les identifiants (Q, 492232)._

Le tableau ci-dessous répertorie les **identifiants internes** des cours créés pour les tests de nettoyage des enseignants :
|Identifiant en BD|Inscrit à un cours|Possède un cours|
|-|-|-|
|D < anon|37000|37001|
|anon < D < backup|37002|37003|
|backup D < delete|37004|37005|
|delete < D|37006|370007|

Le tableau ci-dessous décrit le **comportement attendu** pour les tests de nettoyage vis à vis des enseignants :
|Comportement attendu en fonction du délai|Inscrit à un cours|Possède un cours|Possède des références|Ni références ni inscriptions|
|-|-|-|-|-|
|D < anon|Rien|Rien|Rien|Rien|
|anon < D < backup|Anonymiser|Rien|Anonymiser|Anonymiser|
|backup D < delete|Anonymiser|Traitement|Anonymiser|Anonymiser|
|delete < D|Anonymiser|Traitement|Anonymiser|Supprimer|
Le cas _"Inscrit à un cours"_ correspondant aux enseignants inscrits à des cours avec des rôles autres que _enseignant_ ou _propriétaire de cours_. Le cas _"Possède un cours"_ correspondant aux enseignants inscrits à des cours avec un rôle _enseignant_ ou _propriétaire de cours_.

### Cours
⚠ Enseignants créés pour les tests des cours ⚠
_L'enseignant X n'est plus présent dans le LDAP et n'a pas utilisé moodle depuis plus de backup_delay jours._
_L'enseignant Y est présent dans le LDAP._

Le tableau ci-dessous répertorie les **identifiants internes** des cours pour les tests de nettoyage :
|Identifiant dans le code et identifiant en BD|Prof X seul propriétaire|Prof X propriétaire avec Y enseignant|Prof X enseignant avec Y propriétaire|
|-|-|-|-|
|D < backup|(1, 37000)|(2, 37001)|(3, 37002)|
|backup < D|(4, 37003)|(5, 37004)|(6, 37005)|
_L'enseignant X possède l'identifiant 492216, et l'enseignant Y l'identifiant 492217._

Le tableau ci-dessous décrit le **comportement attendu** pour les tests de nettoyage vis à vis des cours :
|Comportement attendu en fonction du délai|Prof X seul propriétaire|Prof X propriétaire avec Y enseignant|Prof X enseignant avec Y propriétaire|
|-|-|-|-|
|D < backup|Rien|Désinscrire X|Désinscrire X|
|backup < D|Supprimer|Désinscrire X|Désinscrire X|
