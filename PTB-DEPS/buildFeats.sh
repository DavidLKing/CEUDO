#!/usr/bin/env bash

for i in data/*;
do d=`basename $i`;
    echo "making $d classifier";
    mv data/$d holdout;
    rm classifiers/$d.feats;
    touch classifiers/$d.feats;
    for f in data/*/*.out;
        do cat $f | egrep -v "cc_|conj_|dep_|acl.*_" | sed '/^\s*$/d' >> classifiers/$d.feats;
        done;
    mv holdout/$d data;
done
