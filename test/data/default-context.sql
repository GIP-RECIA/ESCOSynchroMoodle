/*!40101 SET character_set_client = utf8 */;

INSERT INTO mdl_user_info_field (id, shortname, name, datatype, description, descriptionformat, categoryid, sortorder, required, locked, visible, forceunique, signup, defaultdata, defaultdataformat, param1, param2, param3, param4, param5) VALUES(1, 'classe', 'Classe', 'text', NULL, 0, 1, 1, 0, 1, 2, 0, 0, '', 1, '30', '512', NULL, NULL, NULL);
INSERT INTO mdl_user_info_field (id, shortname, name, datatype, description, descriptionformat, categoryid, sortorder, required, locked, visible, forceunique, signup, defaultdata, defaultdataformat, param1, param2, param3, param4, param5) VALUES(2, 'depot', 'depot', 'text', 'numero du depot', 1, 1, 2, 0, 1, 2, 0, 0, NULL, 0, '30', '2048', NULL, NULL, NULL);
INSERT INTO mdl_user_info_field (id, shortname, name, datatype, description, descriptionformat, categoryid, sortorder, required, locked, visible, forceunique, signup, defaultdata, defaultdataformat, param1, param2, param3, param4, param5) VALUES(3, 'Domaine', 'Domaine', 'text', '<p>Domaine utilisé par l''utilisateur (qui permettra de définir les liens dans les courriels envoyés par Moodle)</p>', 1, 1, 3, 0, 1, 1, 0, 0, 'lycees.netocentre.fr', 0, '25', '25', '0', '', '');
INSERT INTO mdl_user_info_field (id, shortname, name, datatype, description, descriptionformat, categoryid, sortorder, required, locked, visible, forceunique, signup, defaultdata, defaultdataformat, param1, param2, param3, param4, param5) VALUES(4, 'avatar', 'Avatar Portail', 'text', '', 1, 1, 4, 0, 1, 0, 0, 0, '', 0, '30', '2048', '0', '', '');
INSERT INTO mdl_user_info_field (id, shortname, name, datatype, description, descriptionformat, categoryid, sortorder, required, locked, visible, forceunique, signup, defaultdata, defaultdataformat, param1, param2, param3, param4, param5) VALUES(5, 'etablissementuai', 'Etablissement UAI', 'text', '', 1, 1, 5, 0, 1, 0, 0, 0, '', 0, '30', '2048', '0', '', '');

INSERT INTO mdl_course_categories (id, name, idnumber, description, descriptionformat, parent, sortorder, coursecount, visible, visibleold, timemodified, `depth`, `path`, theme) VALUES(1, 'Catégorie Inter-Établissements', NULL, 'Utilisation de Moodle', 1, 0, 3050000, 417, 1, 1, 0, 1, '/1', NULL);
INSERT INTO mdl_course_categories (id, name, idnumber, description, descriptionformat, parent, sortorder, coursecount, visible, visibleold, timemodified, `depth`, `path`, theme) VALUES(1163, 'Catégorie Inter-CFA', '', '<p>Catégorie partagée entre tous les CFA de l''ENT</p>', 1, 0, 20960000, 16, 1, 1, 1380112940, 1, '/1163', NULL);

INSERT INTO mdl_context (id, contextlevel, instanceid, `path`, `depth`) VALUES(2, 50, 1, '/1/2', 2);
INSERT INTO mdl_context (id, contextlevel, instanceid, `path`, `depth`) VALUES(3, 40, 1, '/1/3', 2);
INSERT INTO mdl_context (id, contextlevel, instanceid, `path`, `depth`) VALUES(4, 80, 1, '/1/2/4', 3);
INSERT INTO mdl_context (id, contextlevel, instanceid, `path`, `depth`) VALUES(150433, 30, 1, '/1/150433', 2);

INSERT INTO mdl_context (id, contextlevel, instanceid, `path`, `depth`) VALUES(4802, 30, 1163, '/1/4802', 2);
INSERT INTO mdl_context (id, contextlevel, instanceid, `path`, `depth`) VALUES(35895, 50, 1163, '/1/9775/16544/16545/35895', 5);
INSERT INTO mdl_context (id, contextlevel, instanceid, `path`, `depth`) VALUES(343065, 40, 1163, '/1/343065', 2);

INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(2, 'Créateur de cours', 'coursecreator', '<p>Les créateurs des cours peuvent créer de nouveaux cours.</p>', 3, 'coursecreator');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(3, 'Enseignant', 'editingteacher', '<p>Les enseignants peuvent tout faire dans un cours, y compris ajouter et modifier les activités et donner des notes aux étudiants.</p>', 4, 'editingteacher');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(5, 'Elève', 'student', '<p>Les étudiants ont en général moins de privilèges dans un cours.</p>', 7, 'student');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(6, 'Visiteur anonyme', 'guest', '<p>Les visiteurs anonymes ont très peu de privilèges et ne peuvent normalement saisir de texte à aucun endroit.</p>', 13, 'guest');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(7, 'Utilisateur authentifié', 'user', '<p>Tous les utilisateurs connectés.</p>', 8, 'user');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(8, 'Administrateur de ressources', 'adminressources', 'Les administrateurs de ressources peuvent administrer les établissements dans le Moodle.', 2, '');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(11, 'Propriétaire de cours', 'courseowner', '<p>Le propriétaire du cours peut supprimer ses cours</p>', 9, '');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(12, 'Administrateur délégué', 'adminlocal', '<p>L''administrateur délégué peut créer des catégories et supprimer des cours pour son établissement</p>', 10, '');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(13, 'Enseignant étendu', 'extendedteacher', 'Ajoute des droits aux enseignants dans les établissements ayant choisit de ne pas avoir d''administrateur local ', 11, '');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(14, 'Utilisateur authentifié avec droits limités', 'limiteduser', '<p>Rôle avec des droits en moins par rapport à un utilisateur authentifié classique :<br />- pas de modification de son profil<br />- pas de participation aux blogs<br />Demandé pour les élèves de collège dans le département d''Indre et Loire.</p>', 12, 'student');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(15, 'Gardien de clé', 'gardien', 'Enseignant en charge de fournir la clé d''inscription.', 6, '');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(16, 'Utilisateur Mahara', 'maharauser', '<p>Utilisateur de Mahara et des liens vers Mahara dans les cours.</p>', 14, 'user');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(18, 'Personnel de direction', 'directeur', '<p>Le personnel de direction est un rôle que peuvent attribuer les enseignants dans leurs cours.</p>', 15, 'editingteacher');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(19, 'Enseignant non éditeur', 'noneditingteacher', '<p>Les enseignants non éditeurs peuvent accéder aux cours comme les enseignants mais ne peuvent pas éditer le contenu des cours.</p>', 5, 'teacher');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(20, 'Enseignant avancé', 'advancedteacher', '<p>L''enseignant avancé dispose de plus d''activités et de ressources que l''enseignant "classique".</p>', 16, '');
INSERT INTO mdl_role (id, name, shortname, description, sortorder, archetype) VALUES(21, 'Temporaire pour Compétences', 'tempcomp', 'Rôle temporaire pour mettre en place les compétences', 17, '');
