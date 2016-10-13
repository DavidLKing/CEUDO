#!/usr/bin/env bash

for i in ../PTB-DEPS/classifiers/*.feats
    do c=`basename $i .feats`
    megam_i686.opt -nc -pa multitron $i > ../PTB-DEPS/classifiers/$c.cls & 
done
wait
