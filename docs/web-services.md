# Permettre l'utilisation des webservices

## Activer les Webservices
- Aller dans **Administration du site > Fonctions avancées**
- Cocher **_Activer les services web_**
- Sauvegarder


- Aller dans **Administration du site > Plugins > Services Web > Gérer les protocoles**
- Activer le **_Protocole REST_**
- Sauvegarder

## Créer un Webservice
- Aller dans **Administration du site > Plugins > Services Web > Services externes**
- Ajouter un nouveau service a l'aide du bouton **_Ajouter_** en bas de la section **Services personnalisés**
- Donner un nom au service (Par exemple: **_synchromoodle_**) et cocher les cases **_Activé_** et **_Uniquement utilisateurs autorisés_**
- Sauvegarder
- Accéder au menu d'ajout de fonctions à ce service a l'aide du bouton **_Fonctions_**
- Cliquer sur **_Ajouter des fonctions_** et ajouter :
    - core_user_delete_users
    - core_course_delete_courses
    - core_cohort_delete_cohorts
    - core_enrol_get_users_courses
    - core_webservice_get_site_infos
- Sauvegarder

⚠Cas particulier - Environnement de Dev⚠

Il est possible qu'une erreur survienne sur l'écran d'ajout de fonction. Pour la faire disparaître, il faut
modifier le code du fichier `/lib/externallib.php` de moodle à la ligne 87 tel que:
```php
if (!file_exists($function->classpath)) {
    return;                
    throw new coding_exception('Cannot find file with external function implementation');
}
```

## Créer le compte utilisateur pour utiliser le Webservice
- Aller dans **Administration du site > Utilisateurs > Comptes > Liste des utilisateurs**
- Créer un nouvel utilisateur avec les valeurs par défaut.

## Créer un nouveau rôle système
- Aller dans **Administration du site > Utilisateurs > Permissions > Définition des rôles**
- Créer un nouveau rôle (Par exemple: **_Webservice_**)
- Cocher la case **_Système_** pour la valeur de **_Types de contextes où ce rôle peut être attribué_**
- Assigner les capacités suivantes au rôle:
    - webservice/rest:use
    - moodle/user:delete
    - moodle/course:delete
    - moodle/course:viewhiddencourses
    - moodle/course:view
    - moodle/course:viewparticipants
    - moodle/user:viewdetails
    - moodle/cohort:manage
    - mod/dataform:managetemplates
    - mod/dataform:managefields
- Sauvegarder

## Autoriser l'utilisateur à utiliser le service
- Aller dans **Administration du site > Plugins > Services Web > Services externes**
- Pour le service créé précédemment, cliquer sur **_Utilisateurs autorisés_**
- Choisir l'utilisateur créé précédemment et cliquer sur **_Ajouter_**

## Assigner le rôle au compte utilisateur
- Aller dans **Administration du site > Utilisateurs > Permissions > Attribution des rôles système**
- Cliquer sur le rôle précédemment créé
- Choisir l'utilisateur créé précédemment et cliquer sur **_Ajouter_**

## ⚠ Cas particulier - Rôle utilisateur authentifié ⚠
Il est possible que le rôle utilisateur authentifié, donné de base à tous les utilisateurs authentifiés écrase la permission pour supprimer un utilisateur et empêche ainsi l'utilisateur WebService de pouvoir réaliser cette action.
Si c'est le cas, pour résoudre le problème il faut :
- Aller dans **Administration du site > Utilisateurs > Permissions > Définition des rôles**
- Choisir le rôle **_Utilisateur authentifié_**
- Cliquer sur **_Modifier_**, puis **_Afficher éléments supplémentaires_**
- Cocher la case **_Empêcher_** pour la capacité **_moodle/user:delete_**

## Créer le token
- Aller dans **Administration du site > Plugins > Services Web > Gérer les jetons**
- Cliquer sur **_Ajouter_**
- Sélectionnez l'utilisateur et le service créés précédemment
- Sauvegarder
- Fournir le token généré dans la configuration du script de synchronisation


Vous pouvez tester le bon fonctionnement du service en accédant à:

_https://votre-appli-moodle.com/webservice/rest/server.php?wstoken=**TOKEN**&moodlewsrestformat=json&wsfunction=core_webservice_get_site_info_

En remplaçant **TOKEN** par le token généré.

Ne pas oublier d'ajouter l'ID de l'utilisateur créé à la liste des IDs des utilisateurs à ne pas supprimer dans la configuration.
