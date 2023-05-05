# Permettre l'utilisation des webservices

## Activer les Webservices
- Aller dans **Home > Site Administration > Advanced Features**
- Cocher **Enable web services**
- Sauvegarder


- Aller dans **Home > Site Administration > Plugins > Web services > Manage protocols**
- Activer le **_REST protocol_**
- Sauvegarder

## Créer un Webservice
- Aller dans **Home > Site Administration > Plugins > Web services > External services**
- Ajouter un nouveau service a l'aide du bouton **_Add_** en bas de la section **Custom services**
- Donner un nom au service (Par exemple: **_Synchronizer Service_**) et cocher les cases **_Enabled_** et **_Authorized users only_**
- Sauvegarder
- Accéder au menu d'ajout de fonctions à ce service a l'aide du bouton **_Add functions_**
- Ajouter les fonctions:
    - core_user_delete_users
    - core_course_delete_courses
    - core_cohort_delete_cohorts
    - core_enrol_get_users_courses
    - enrol_manual_unenrol_users
    - core_webservice_get_site_infos
- Sauvegarder

⚠Cas particulier - Environnement de Dev⚠

Il est possible qu'une erreur survienne sur l'écran d'ajout de fonction. Pour la faire disparaitre, il faut
modifier le code du fichier `/lib/externallib.php` de moodle à la ligne 87 tel que:
```php
if (!file_exists($function->classpath)) {
    return;                
    throw new coding_exception('Cannot find file with external function implementation');
}
```

## Créer le compte utilisateur pour utiliser le Webservice
- Aller dans **Home > Site Administration > Users > Accounts > Browse list of users**
- Créer un nouvel utilisateur avec les valeurs par défaut.

## Créer un nouveau rôle système
- Aller dans **Home > Site Administration > Users > Permissions > Define roles**
- Créer un nouveau rôle (Par exemple: **_Synchronizer Users_**)
- Cochez la case **_System_** pour la valeur de **_Context types where this role may be assigned_**
- Assigner les capacités suivantes au rôle:
    - webservice/rest:use
    - moodle/user:delete
    - moodle/course:delete
    - moodle/course:viewhiddencourses
    - moodle/course:view
    - moodle/course:viewparticipants
    - moodle/user:viewdetails
    - moodle/cohort:manage
    - enrol/manual:unenrol
- Sauvegarder

## Autoriser l'utilisateur à utiliser le service
- Aller dans **Home > Site Administration > Plugins > Web services > External services**
- Pour le service créé précédemment, cliquer sur **_Authorised users_**
- Choisir l'utilisateur créé précédemment et cliquer sur **_Add_**

## Assigner le rôle au compte utilisateur
- Aller dans **Home > Site administration > Users > Permissions > Assign system roles**
- Choisir l'utilisateur créé précédemment et cliquer sur **_Add_**

## Créer le token
- Aller dans **Home > Site Administration > Plugins > Web services > Manage tokens**
- Cliquer sur **_Add_**
- Sélectionnez l'utilisateur et le service créés précédemment
- Sauvegarder
- Fournir le token généré dans la configuration du script de synchronisation


Vous pouvez tester le bon fonctionnement du service en accédant à:

_https://votre-appli-moodle.com/webservice/rest/server.php?wstoken=**TOKEN**&moodlewsrestformat=json&wsfunction=core_webservice_get_site_info_

En remplaçant **TOKEN** par le token généré.

Ne pas oublier d'ajouter l'ID de l'utilisateur créé à la liste des IDs des utilisateurs à ne pas supprimer dans la configuration.
