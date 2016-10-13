#!/usr/bin/env bash

rm maxent.txt newconj.txt
for i in holdout/*/*.parg;
do c=`basename $i .parg`;
	d=`echo $c | cut -c 5-6`;
	echo "starting $c";
	python3 ../remap.py -n holdout/$d/$c.parg holdout/$d/$c.auto holdout/$d/$c.mrg.dep.withid &
done
wait
