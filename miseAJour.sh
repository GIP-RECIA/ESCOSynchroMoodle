#!/bin/sh
export PYTHONPATH=/home/esco_synchro/esco-synchro-moodle2:$PYTHONPATH
export LANG=fr_FR.UTF-8
export LC_ALL=fr_FR.UTF-8
export REP_EXE=/home/esco_synchro/esco-synchro-moodle2
export DATE=`/bin/date +%Y%m%d`
export REP_LOGS=/home/esco_synchro/logs/Moodle2
export SYNC_LOG=${REP_LOGS}/${DATE}_majMoodle.log
export SYNC_ERR=${REP_LOGS}/${DATE}_majMoodle.err

echo "Debut du script : `date`" >>$SYNC_LOG 2>>$SYNC_ERR
echo "Lycees de l'academie :" >>$SYNC_LOG 2>>$SYNC_ERR
python $REP_EXE/miseAJour_academique.py $* >>$SYNC_LOG 2>>$SYNC_ERR
echo "Inspecteurs de l'academie :" >>$SYNC_LOG 2>>$SYNC_ERR
python $REP_EXE/miseAJour_inspecteurs.py $* >>$SYNC_LOG 2>>$SYNC_ERR
echo "Lycees agricoles :" >>$SYNC_LOG 2>>$SYNC_ERR
python $REP_EXE/miseAJour_agricole.py $* >>$SYNC_LOG 2>>$SYNC_ERR
echo "CFA :" >>$SYNC_LOG 2>>$SYNC_ERR
python $REP_EXE/miseAJour_cfa.py $* >>$SYNC_LOG 2>>$SYNC_ERR
echo "Etablissements du Social :" >>$SYNC_LOG 2>>$SYNC_ERR
python $REP_EXE/miseAJour_sanitaire.py $* >>$SYNC_LOG 2>>$SYNC_ERR
echo "Inter établissements :" >>$SYNC_LOG 2>>$SYNC_ERR
python $REP_EXE/miseAJour_inter_etabs.py $* >>$SYNC_LOG 2>>$SYNC_ERR
echo "Utilisateurs Mahara :" >>$SYNC_LOG 2>>$SYNC_ERR
python $REP_EXE/miseAJour_mahara.py $* >>$SYNC_LOG 2>>$SYNC_ERR
echo "================================" >>$SYNC_LOG 2>>$SYNC_ERR
