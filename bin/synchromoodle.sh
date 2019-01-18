#!/bin/sh
SRCPATH="src"

export PYTHONPATH="$SRCPATH:$PYTHONPATH"

DATE=`/bin/date +%Y%m%d`
REP_LOGS="logs"

SYNC_LOG=${REP_LOGS}/${DATE}_majMoodle.log
SYNC_ERR=${REP_LOGS}/${DATE}_majMoodle.err

mkdir -p logs

echo "Debut du script : `date`" >>$SYNC_LOG 2>>$SYNC_ERR
echo "Lycees de l'academie :" >>$SYNC_LOG 2>>$SYNC_ERR
python3 -m synchromoodle -c config/academique.yml >>$SYNC_LOG 2>>$SYNC_ERR
echo "Inspecteurs de l'academie :" >>$SYNC_LOG 2>>$SYNC_ERR
python3 -m synchromoodle -c config/inspecteurs.yml >>$SYNC_LOG 2>>$SYNC_ERR
echo "Lycees agricoles :" >>$SYNC_LOG 2>>$SYNC_ERR
python3 -m synchromoodle -c config/agricole.yml >>$SYNC_LOG 2>>$SYNC_ERR
echo "CFA :" >>$SYNC_LOG 2>>$SYNC_ERR
python3 -m synchromoodle -c config/cfa.yml >>$SYNC_LOG 2>>$SYNC_ERR
echo "Etablissements du Social :" >>$SYNC_LOG 2>>$SYNC_ERR
python3 -m synchromoodle -c config/sanitaire.yml* >>$SYNC_LOG 2>>$SYNC_ERR
echo "Inter établissements :" >>$SYNC_LOG 2>>$SYNC_ERR
python3 -m synchromoodle -c config/intererab-all.yml* >>$SYNC_LOG 2>>$SYNC_ERR
python3 -m synchromoodle -c config/intererab-cfa.yml* >>$SYNC_LOG 2>>$SYNC_ERR
echo "Utilisateurs Mahara :" >>$SYNC_LOG 2>>$SYNC_ERR
python3 -m synchromoodle -c config/mahara.yml* >>$SYNC_LOG 2>>$SYNC_ERR
echo "================================" >>$SYNC_LOG 2>>$SYNC_ERR
