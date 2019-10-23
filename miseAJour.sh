#!/bin/sh
export PYTHONPATH=/home/esco_synchro/esco-synchro-moodle2:$PYTHONPATH
export LANG=fr_FR.UTF-8
export LC_ALL=fr_FR.UTF-8
export REP_EXE=/home/esco_synchro/esco-synchro-moodle2
export DATE=`/bin/date +%Y%m%d`
export REP_LOGS=/home/esco_synchro/logs/Moodle2
#export SYNC_LOG=${REP_LOGS}/${DATE}_majMoodle.log
#export SYNC_ERR=${REP_LOGS}/${DATE}_majMoodle.err
export SYNC_LOG_ACA=${REP_LOGS}/${DATE}_majMoodleAca.log
export SYNC_ERR_ACA=${REP_LOGS}/${DATE}_majMoodleAca.err
export SYNC_LOG_INS=${REP_LOGS}/${DATE}_majMoodleIns.log
export SYNC_ERR_INS=${REP_LOGS}/${DATE}_majMoodleIns.err
export SYNC_LOG_AGRI=${REP_LOGS}/${DATE}_majMoodleAgri.log
export SYNC_ERR_AGRI=${REP_LOGS}/${DATE}_majMoodleAgri.err
export SYNC_LOG_CFA=${REP_LOGS}/${DATE}_majMoodleCFA.log
export SYNC_ERR_CFA=${REP_LOGS}/${DATE}_majMoodleCFA.err
export SYNC_LOG_SAN=${REP_LOGS}/${DATE}_majMoodleSan.log
export SYNC_ERR_SAN=${REP_LOGS}/${DATE}_majMoodleSan.err
export SYNC_LOG_INTER=${REP_LOGS}/${DATE}_majMoodleInter.log
export SYNC_ERR_INTER=${REP_LOGS}/${DATE}_majMoodleInter.err
export SYNC_LOG_MAH=${REP_LOGS}/${DATE}_majMoodleMahara.log
export SYNC_ERR_MAH=${REP_LOGS}/${DATE}_majMoodleMahara.err

echo "Debut du script pour Etablissements de l'academie : `date`" >>$SYNC_LOG_ACA 2>>$SYNC_ERR_ACA
python $REP_EXE/miseAJour_academique.py $* >>$SYNC_LOG_ACA 2>>$SYNC_ERR_ACA
echo "Debut du script pour Inspecteurs de l'academie :" >>$SYNC_LOG_INS 2>>$SYNC_ERR_INS
python $REP_EXE/miseAJour_inspecteurs.py $* >>$SYNC_LOG_INS 2>>$SYNC_ERR_INS
echo "Debut du script pour Lycees agricoles :" >>$SYNC_LOG_AGRI 2>>$SYNC_ERR_AGRI
python $REP_EXE/miseAJour_agricole.py $* >>$SYNC_LOG_AGRI 2>>$SYNC_ERR_AGRI
echo "Debut du script pour CFA :" >>$SYNC_LOG_CFA 2>>$SYNC_ERR_CFA
python $REP_EXE/miseAJour_cfa.py $* >>$SYNC_LOG_CFA 2>>$SYNC_ERR_CFA
echo "Debut du script pour Etablissements du Social :" >>$SYNC_LOG_SAN 2>>$SYNC_ERR_SAN
python $REP_EXE/miseAJour_sanitaire.py $* >>$SYNC_LOG_SAN 2>>$SYNC_ERR_SAN
echo "Debut du script pour Inter établissements :" >>$SYNC_LOG_INTER 2>>$SYNC_ERR_INTER
python $REP_EXE/miseAJour_inter_etabs.py $* >>$SYNC_LOG_INTER 2>>$SYNC_ERR_INTER
#echo "Debut du script pour Utilisateurs Mahara :" >>$SYNC_LOG_MAH 2>>$SYNC_ERR_MAH
#python $REP_EXE/miseAJour_mahara.py $* >>$SYNC_LOG_MAH 2>>$SYNC_ERR_MAH
#echo "================================" >>$SYNC_LOG 2>>$SYNC_ERR
