#!/usr/bin/env bash

for i in data/*;
do d=`basename $i`
	echo "starting with section $d";
	mv data/$d holdout;
	./1preprocess.sh;
	./2preprocess.sh $d;
	./3preprocess.sh;
	mv holdout/$d data;
	echo "finished with section $d"
done
