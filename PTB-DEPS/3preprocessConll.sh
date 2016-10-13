#!/usr/bin/env bash

for i in holdout/*/*.mrg.dep.withid;
do c=`basename $i .mrg.dep.withid`;
	d=`echo $c | cut -c 5-6`;
	echo "Starting $c";
	python3 ../collate.py -c holdout/$d/$c.mrg.dep.withid maxent.collated newconj.txt holdout/$d/$c.auto > holdout/$d/$c.conll &
done
wait
