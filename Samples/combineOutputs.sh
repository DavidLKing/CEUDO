#!/usr/bin/env bash

for i in ../PTB-DEPS/data/*/*.mrg
    do python3 ../combine.py $i.noncollapsed.withid $i.enhanced.withid > $i.dep.withid & 
done
wait
