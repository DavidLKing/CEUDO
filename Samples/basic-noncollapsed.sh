#!/usr/bin/env bash

# ran from the data directory and assuming the SDC is in:
# ../../../StanfordDeps/stanford-parser-full-2015-04-20/
# with lexparserDEPSfrmTREES.sh file in it

for i in ../PTB-DEPS/data/*
    do echo "Starting $i"
    for f in $i/*.mrg
        do echo "Now starting file $f"; 
        nice -n 10 ../../StanfordDeps/stanford-parser-full-2015-04-20/lexparserDEPSfrmTREES.sh $f | sed -e 's/nmod:.*(/nmod(/g' | sed -e 's/conj:.*(/conj(/g' > $f.noncollapsed & 
    done
wait
done
