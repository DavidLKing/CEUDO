#!/usr/bin/env bash
#
# Runs the English PCFG parser on one or more files, printing trees only

if [ ! $# -ge 1 ]; then
  echo Usage: `basename $0` 'file(s)'
  echo
  exit
fi

scriptdir=`dirname $0`

# java -mx16G -cp "$scriptdir/*:" edu.stanford.nlp.parser.lexparser.LexicalizedParser \
#  -outputFormat "penn,typedDependencies" edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz $*
java -mx16G -cp "$scriptdir/*:" edu.stanford.nlp.trees.EnglishGrammaticalStructure \ #parser.lexparser.LexicalizedParser \
 -treeFile $* -keepPunct \
 -outputFormat "typedDependencies" # edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz $*
 #-outputFormat "penn,typedDependencies" # edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz $*
