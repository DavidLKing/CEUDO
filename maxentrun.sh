#!/usr/bin/env bash

for i in ./PTB-DEPS/data/*/*.parg
do c=`basename $i .parg`
    # | sed -e "s/^.*\///g"`
    d=`basename $i .parg | cut -c 5-6`
	cfile="$c.parg"
	dfile="$c.mrg.dep.withid"
	afile="$c.auto"
	ofile="$c.out"
        # echo "Starting $c":
	# python appears to be faster here. Very surprising
	python maxentprep.py ./PTB-DEPS/data/$d/$cfile ./PTB-DEPS/data/$d/$dfile ./PTB-DEPS/data/$d/$afile ./PTB-DEPS/data/$d/$ofile
	# pypy counts.py c00/$cfile d00/$dfile testpickle.pkl
done
