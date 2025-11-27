#!/bin/bash
SELBASE=$PWD/selenzyme2
python ${SELBASE}/selenzyPro/flaskform.py -uploaddir ${SELBASE}/selenzyPro/uploads -datadir ${SELBASE}/selenzyPro/data -logdir ${SELBASE}/selenzyPro/log2 -d 
