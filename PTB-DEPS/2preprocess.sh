#!/usr/bin/env bash

echo "Coolating maxent entries"
rm *.data *.key *.predicted *.collated
#~ touch maxent.maxent;
touch maxent.key
section=$*
# for i in dev/*.maxent;
#do 
cut -d$'\t' -f 6 maxent.txt >> maxent.data;
cut -d$'\t' -f 1-5 maxent.txt >> maxent.key;
#done
echo "Predicting new dependencies using $section.cls"
#echo "Predicting new dependencies using train.cls"
# ./megam_i686.opt -nc -predict train.cls multitron maxent.data > maxent.predicted
./megam_i686.opt -nc -predict classifiers/$section.cls multitron maxent.data > maxent.predicted
echo "Collating"
cut -d$'\t' -f 1 maxent.predicted | paste maxent.key - > maxent.collated
echo "Finished"
