#!/usr/bin/env bash

for i in holdout/*/*.mrg.dep.withid;
do c=`basename $i .mrg.dep.withid`;
	d=`echo $c | cut -c 5-6`;
	echo "Starting $c";
	python3 ../collate.py -n holdout/$d/$c.mrg.dep.withid maxent.collated newconj.txt holdout/$d/$c.auto --debug > holdout/$d/$c.debug &
done
wait
