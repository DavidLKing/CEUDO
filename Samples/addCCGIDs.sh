#!/usr/bin/env bash

# ran from CEUDO root directory
# for the noncollapsed basic
for i in ../PTB-DEPS/data/*
    do echo "Starting $i"
    for f in $i/*.mrg.noncollapsed
        do python ../rename.py $f $f.withid & 
    done
wait
done

# for the enhanced collapsed ones
for i in ../PTB-DEPS/data/*
    do echo "Starting $i"
    for f in $i/*.mrg.enhanced
        do python ../rename.py $f $f.withid & 
    done
wait
done
