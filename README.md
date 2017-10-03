# Overview
This is the implementation as described in King and White's 2016 INLG short on enhancing SDC output ("Enhancing PTB Universal Dependencies for Surface Realization"). Essentially, these files provide a platform to integrate both Stanford Dependency Converter (SDC) output with CCGbank to get a representation closer to Universal Dependencies as described in Nivre et al. 2016 and in the manual at universaldependencies.org. Once everything is set up, and there is a lot of setup, this entire system takes about 20 minutes, resources permitting. Please send any questions to the repo owner (currently David L. King) via the github contact information provided.

Sidenote: I'm still cleaning this and testing this on new builds.

# Prerequisites

#### SHORT VERSION:
1. Run David Vadas' scripts
2. move PTB to ./PTB-DEPS/data
3. move CCGbank AUTO and PARG files to the same directories
4. convert the PTB using the SDC (and combine if necessary)
5. Train classifiers and place in ./PTB-DEPS/classifiers
6. Build morpha
7. Ready!

### David Vadas CCGbank and PTB enhancements:
Before we start anything, make sure, if you want it, to have already ran David Vadas' NP patches for the [PTB and CCGbank](http://schwa.org/projects/resources/wiki/NounPhrases). Obviously you will need to have access to the PTB and CCGbank.

### Penn Treebank (PTB):
To start, keeping the section folders intact, move the PTB sections to the folder named CEUDO/PTB-DEPS/data. This hierarchy should look like so:
```
CEUDO
│
└PTB-DEPS
   └─data
      └─00
      └─01
      └─02
      └─03
      └─04
      └─05
      └─06
      └─07
      └─08
      └─09
      └─10
      └─11
      └─12
      └─13
      └─14
      └─15
      └─16
      └─17
      └─18
      └─19
      └─20
      └─21
      └─22
      └─23
      └─24
```

### CCGbank
Move the CCGbank AUTO and PARG files to that they are in the same directories as their PTB counterparts. The same file hierarchy as specified above should still apply.

### Stanford Dependency Converter:
Obviously you're going to need output from the SDC. Included in this repo are customized lexparser.sh files which run the SDC over PTB trees. One is for enhanced output, and the other for basic. The original implementation actually combines these with combine.py. Feasibly, you should just need to run one the lexparser files and pipe their output to the data directory (`./lexparserDepsFrmTrees.sh wsj_0001.mrg > wsj_0001.mrg.dep`). See `CEUDO/Samples` files `basic-noncollapsed.sh` and `enhanced-collapsed.sh` for an example of how to convert the entire PTB using the SDC. You will also need to add CCGbank like naming to the rest of the pipeline to work with `rename.py`, for which the file `CEUDO/Samples/addCCGIDs.sh` also provides an example.

Please make sure to edit lexparserDepsEnhancedFrmTrees.sh and lexparserDepsFrmTrees.sh before running them. They are both currently set to use 200MB of RAM. Please adjust accordingly so you don't break your system.

For the sample scripts, be sure to adjust the paths ('../../StanfordDeps/stanford-parser-full-2015-04-20/') to wherever you've stored the SDC on your system.

### Maxent Software:
Although there is talk about pulling out the maxent classifier for something more sophisticated, currently the system is configured to use a maxent classifier. Be sure that you have [Hal Daume's](https://www.umiacs.umd.edu/~hal/megam/version0_3/) maxent implementation downloaded and installed to your PATH. The script just calls 'megam_i686.opt' not './megam_i686.opt'.

#### Build the Classifiers:
`cdc.py` is the script that builds all the maxent features for training. You shouldn't need to worry about opening and running it manually unless you are really curious. Building the maxent classifiers takes three steps:

1. Getting feature output:
./maxentrun.sh

2. Building hold-one-out classifiers:
./buildFeats.sh

3. Training:
See `maxentTrain.sh` in the `CEUDO/Samples` directory, but remember that is spins up 25 megam sessions at once. Make sure your system can handle that, or change the sample code to adjust for your system. Also note that these 25 megam sessions will all spew text to stdout all at the same time, so I recommend running it in a separate terminal and subsequently monitoring the progress through something like `top` or `htop` in your main terminal.

### Morpha
Finally, for the running the whole system, conll and normal output require the morpha program for producing lemmas. This requires [morpha](https://github.com/knowitall/morpha) to be working and for the noninteractive version to be called morphaNoI in the root directory of CEUDO.

# Running the system

##Possible outputs:
The system is designed to output a conll-like format, an SDC type format, and what we call 'normal' format, which is just a more legable format we liked to use for debugging. Use whichever you want to (from `CEUDO/PTB-DEPS`):
####Normal:
./wholerun.sh
####CoNLL:
./wholerunConll.sh
####SDC/UD:
./wholerunDeps.sh
####Additional debugging output
./wholerunDEBUG.sh

Note that the CoNLL formatting was designed for subsequent realization and induction work. It specifically finds cases that were skipped in CCGbank, often marked in the PTB with an '=' notation, and removes them from the final output. Should you want a similar functionality from wholerunDeps.sh, simply use wholerunDepsNoTMP.sh instead. Likewise, the bottom half of those scripts have the processes listed for calling this functionality should you prefer it with any other output.

### Samples
See the `Samples` directory for sample workflows, including converting the PTB using the SDC, combining enhanced collapsed and basic non-collapsed dependencies, adding CCG identifiers, and training the classifiers. 

## Some examples of manually runing the files:
#### `combine.py`
`combine.py` takes two arguments, and those are the two files you're trying to merge. The first argument will have no dependencies removed from it, but the second one will. Ideally, or rather by design, this program supplements basic non-collapsed dependency representations with collapsed enhanced SDC output.
`python3 combine.py PTB-DEPS/data/00/wsj_0003.mrg.collapsed.withid PTB-DEPS/data/00/wsj_0003.mrg.enhanced.withid`

#### `rename.py`
`rename.py` takes simple SDC output and adds CCGlink labelling to it. This works because when CCGbank skipped a sentence, they still incremented the sentence count. Regardless of SDC output you're using, this script should work. The only caveat is that you need to specify an output file.
`python3 rename.py PTB-DEPS/data/00/wsj_0003.mrg.collapsed PTB-DEPS/data/00/wsj_0003.mrg.collapsed.withid`

#### `cdc.py`
The `cdc.py` file is actually just a class file and is not executable on its own. `maxentrun.sh` is what calls it, and that's where you can find examples of what class methods are useful to call. 

#### `remap.py`
`remap.py` is were the triggers get processed. Note that here is where most of the old conjunction binarization code still exists. I'm still ripping all that out, so bear with me. That said, the '-n' argument is depreciated, as is the newconj.txt output file. As is though, this script still builds a list of predictions for the maxent classifier.
`python3 remap.py -n wsj_0001.parg wsj_0001.auto wsj_0111.mrg.dep.withid`

#### `collate.py`
`collate.py` is where the final magic happens. Since we've already generated the predictions, everything now is just a matter of collation and coping with syntactic anomalies. Be aware that the `-n` option can only be `-n` for normal, `-d` for SDC output, and `-c` for CoNLL. Additionally, the newconj.txt file is still depreciated. Sorry about that.
`python3 collate.py -n wsj_0111.mrg.dep.withid maxent.collated newconj.txt wsj_1111.auto`
