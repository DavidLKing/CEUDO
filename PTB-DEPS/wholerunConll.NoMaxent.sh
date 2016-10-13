for i in data/*;
do d=`basename $i`
	echo "starting with section $d";
	mv data/$d holdout;
	./1preprocess.sh;
	./2preprocess.sh classifiers/$d;
	# cheap way of wiping out predictions
	rm maxent.collated
	touch maxent.collated
	./3preprocessConll.sh;
	mv holdout/$d data;
	echo "finished with section $d"
done
echo "removing TMP=s"
rm temps.txt
touch temps.txt
for j in data/*; 
	do m=`basename $j`; 
	for n in $j/*.mrg;
		do o=`basename $n .mrg`;
			python3 ../findTMPs.py $j/$o.mrg $j/$o.auto $j/$o.mrg.dep.withid > temps/$o.temp &
	 done;
 done; wait
cat temps/*.temp > temps.txt
for k in data/*;
	do echo "separating TMP= from $k";
	for l in $k/*.conll;
		do python3 ../sepTMP.py $l temps.txt > $l.tempequals &
		wait
	done
done
echo "Done"

