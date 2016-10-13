import sys
import subprocess
import os
import fileinput
import re
from remap import remap

"""
A lot of this is old depreciated code from the project was new..
I kept it around because it still builds the classifier well, and
has some support code. Don't be surprised if over time this gets
shorter and shorter, if not fully rolled into another class.
"""

class counter():
    def __init__(self,countdict,ccgfile,depfile):
        # TODO depreciate arguments and maxentprep code
        """
        basic initialization
        :param countdict: no longer used
        :param ccgfile: no longer used
        :param depfile: no longer used
        """
        self.counts = countdict
        """ This is used to pull code required from remap.py """
        self.rm = remap()

    def addDepSeqNumbers(self,depfile,outfile):
        """
        This code is used by rename.py to add CCGbank like numbering
        to SDC output. This is pretty easy since CCGbank skipped a
        number when they skipped sentences. Simply iterating does the
        trick.
        :param depfile: Raw SDC converter output where sentences are
                        separated by empty lines
        :param outfile: Any arbitrary output filename.
                        This system prefer just adding '.withid'
        :return: '.withid' file written out
        """
        dep = open(depfile,'r')
        out = open(outfile,'w')
        writeout = []
        """
        This assumes that deps have already been generated from
        a tree file using a command like the following:
        ./lexparserDEPSRaw.sh treefile
        """
        prebase = os.path.splitext(depfile)[0]
        base = re.sub('.*/','',prebase)
        baseperiod = '<s id="' + base.rsplit('.')[0] + "."
        count = 1
        newline = baseperiod + str(count) + '">' + "\n"
        out.write(newline)
        for line in dep:
            check = re.match('\n',line)
            if check != None:
                count +=1
                assert(count >= 2),"Count is not incrementing"
                newline = "</s>\n" + baseperiod + str(count) + '">' + "\n"
            else:
                newline = line
            writeout.append(newline)
        #~ remove final seq. num:
        for wo in writeout[0:-1]:
            out.write(wo)
        out.write("<\s>")
        dep.close()
        out.close()
        
    def adddict(self,revnor,cat,dep):
        # TODO depreciate this? Used by fileloader and arrayloader
        try:
            self.counts[revnor][cat][dep] += 1
        except:
            try:
                self.counts[revnor][cat][dep] = {}
            except:
                try:
                    self.counts[revnor][cat] = {}
                    self.counts[revnor][cat][dep] = {}
                except:
                    self.counts[revnor] = {}
                    self.counts[revnor][cat] = {}
                    self.counts[revnor][cat][dep] = {}
            self.counts[revnor][cat][dep] = 1

    def altfileload(self, ccgfile, depfile, autofile):
        """
        Used by maxentprep to load files as arrays
        :param ccgfile: parg file for dependencies
        :param depfile: SDC output
        :param autofile: CCGbank derivation for easily getting POS-type info
        :return: arrays of lines from these files
        """
        ccgs = open(ccgfile,'r')
        deps = open(depfile,'r')
        autos = open(autofile,'r')
        ccgblock = []
        depblock = []
        autblock = []
        for cline in ccgs:
            ccgblock.append(cline)
        for dline in deps:
            depblock.append(dline)
        for aline in autos:
            autblock.append(aline)
        return ccgblock,depblock,autblock
        
    
    def fileloader(self,ccgs,deps):
        """
        Old possibly deletable function used by counts.py to create pickles of CCG and SDC dep correlations
        :param ccgs: CCGbank parg file
        :param deps: SDC output with IDs (from rename.py)
        :return: null
        """
        # TODO possibly depreciate this -- originally used for counts.py which is no longer in the pipeline
        # DEP - head first
        # CCG - head second
        ccgfile = open(ccgs,'r')
        depfile = open(deps,'r')
        ccgblock = []
        depblock = []
        for cline in ccgfile:
            # print cline.split()
            ccgblock.append(cline.split())
        for predline in depfile:
            dline = predline.replace('(',' ').replace('-',' ').replace(')','').replace(',','')
            # print dline.split()
            depblock.append(dline.split())
        for ccgdep in ccgblock:
            if len(ccgdep) == 6:
                cat = ccgdep[2] + "_" + str(ccgdep[3])
                cdep = ccgdep[4]
                chead = ccgdep[5]
                for depdep in depblock:
                    if len(depdep) == 5:
                        rel = depdep[0]
                        dhead = depdep[1]
                        ddep = depdep[3]
                        if chead == dhead and cdep == ddep:
                            self.adddict('normal',cat,rel)
                        elif chead == ddep and cdep == dhead:
                            self.adddict('reverse',cat,rel)

    def arrayloader(self,ccgs,deps):
        """
        Used by makeMatchingArrays. Load all lines as an array
        :param ccgs: CCG parg file
        :param deps: SDC output
        :return: ???
        """
        # TODO Depreciate this?
        ccgblock = []
        depblock = []
        for cline in ccgs:
            ccgblock.append(cline.split())
        for predline in deps:
            # dline = predline.replace('(',' ').replace('-',' ').replace(')','').replace(',','')
            dline = self.rm.dep2split(predline)
            depblock.append(dline.split())
        for ccgdep in ccgblock:
            if len(ccgdep) == 6:
                cat = ccgdep[2] + "_" + str(ccgdep[3])
                cdep = ccgdep[4]
                chead = ccgdep[5]
                for depdep in depblock:
                    if len(depdep) == 5:
                        rel = depdep[0]
                        dhead = depdep[1]
                        ddep = depdep[3]
                        if chead == dhead and cdep == ddep:
                            self.adddict('normal',cat,rel)
                        elif chead == ddep and cdep == dhead:
                            self.adddict('reverse',cat,rel)

    def makeMatchingArrays(self, ccgfile,depfile, autofile):
        # TODO depreciate this -- only newcounts.py uses this and it's no different from counts.py
        cblock, dblock, _ = self.altfileload(ccgfile, depfile, autofile)
        cchunks = []
        dchunks = []
        for c in cblock:
            #print c
            ccheck = re.match('<s id="(.*)">',c)
            if ccheck != None:
                cchunks.append(cblock.index(c))
        for d in dblock:
            dcheck = re.match('<s id="(.*)">',d)
            if dcheck != None:
                dchunks.append(dblock.index(d))
        if len(cchunks) != (len(dchunks) - 1):
            print("unequal number of sentences entered to be compared", len(cchunks),len(dchunks))
        else:
            pass
        for i in range(len(cchunks) - 1):
            self.arrayloader(cblock[cchunks[i] : cchunks[i+1]],dblock[dchunks[i] : dchunks[i+1]])

    # tnt = test/no test
    def maxentprep(self,ccgf,depf,autf, tnt):
        """
        This file compares CCG and SDC dependencies and builds a feature structure from them for
        training and testing.
        :param ccgf: ccgbank parg file
        :param depf: sdc output with IDs
        :param autf: ccgbank auto file
        :param tnt: test or not test? True or False
        :return:
        """
        results = []
        # Load sentences in file as arrays
        cblock,dblock,ablock = self.altfileload(ccgf,depf,autf)
        # find matching sentence chunks and load the indicies to a separate array
        cchunks = []
        dchunks = []
        achunks = []
        # add sentences to
        for c in cblock:
            ccheck = re.match('<s id="(.*)">',c)
            if ccheck != None:
                cchunks.append(cblock.index(c))
        for d in dblock:
            dcheck = re.match('<s id="(.*)">',d)
            if dcheck != None:
                dchunks.append(dblock.index(d))
        for a in ablock:
            acheck = re.match('ID=(.*) PARSER=GOLD NUMPARSE=1',a)
            if acheck != None:
                achunks.append(ablock.index(a))
        # print cblock,'\n',cchunks,'\n',dblock,'\n',dchunks, '\n', ablock,'\n',achunks
        if len(cchunks) != len(dchunks):
            print("unequal number of sentences entered to be compared", len(cchunks),len(dchunks))
        elif len(cchunks) != len(achunks):
            print("Auto indexing off from CCG deps")
        if len(cchunks) == 1:
            lexicals = self.lexbuilder(ablock[1])
            feat = self.meprepreader(cblock,dblock,lexicals,tnt)
            for each in feat:
                results.append(each)
        else:
            for i in range(len(cchunks)):
                lexicals = self.lexbuilder(ablock[achunks[i]+1])
                cplace = cblock[cchunks[i]].split('"')[1]
                dplace = dblock[dchunks[i]].split('"')[1]
                aplace = ablock[achunks[i]].replace('=',' ').split()[1]
                corrector = self.checkPlace(cplace, dplace, dblock, dchunks, i, aplace, 0)
                dplace = dblock[dchunks[i + corrector]].split('"')[1]
                #~ print cplace, dplace, corrector
                # to get the last one
                try:
                    endblock = cblock[cchunks[i] : cchunks[i+1]]
                except:
                    endblock = cblock[cchunks[i] : ]
                try:
                    depblock = dblock[dchunks[i+corrector] : dchunks[i+1+corrector]]
                except:
                    depblock = dblock[dchunks[i+corrector] : ]
                feat = self.meprepreader(endblock,depblock,lexicals, tnt)
                for each in feat:
                    results.append(each)
        return results

    def checkPlace(self,cp, dp, dparr, dc, ay, ap, cor):
        """
        This function checks where we are and creates a corrector number.
        This number is used to make sure we're pulling from the correct
        sentences across files. As sentences in CCG were skipped, the
        corrector tell us how much that offset should be. Basically, the
        current place in SDC output - CCGbank's current place = corrector.
        This also assumes that sentences were only skipped in CCGbank.
        :param cp: CCG parg file place
        :param dp: SDC output file place
        :param dparr: SDC parse array
        :param dc: SDC chunks -- arrays based on IDs
        :param ay: 'i' from maxentprep, starts as 0 in range(len(cchunks) -- CCG arrays based on ID
        :param ap: CCG auto file place -- should always be in sync with cp
        :param cor: This is the output, initialized at 0
        :return:
        """
        # This is the sanity check to make sure
        # all the files are in sync with one another 
        # based on the identifier.
        if ap != cp:
            print("Error: Auto file is misalligned from Parg file!")
        if cp != dp:
            cor += 1
            dp = dparr[dc[ay + cor]].split('"')[1]
            if cp != dp:
                self.checkPlace(cp, dp, dparr, dc, ay, ap, cor)
        return cor

    def meprepreader(self,csent, dsent, ldict, tnt):
        """
        This function compares the same sentence (block) in CCG and SDC.
        Lexical overlap is used to generate features for training the
        maxent model. tnt was originally used for evaluating the classifier.
        :param csent: ccg parg sent as array
        :param dsent: sdc dep sent as array
        :param ldict: lexical dictionary with POS tags from CCGbank auto files
        :param tnt: test or not test
        :return:
        """
        # Note: this function takes sentences as arrays
        # Establish empty arrays for sentence block
        ccgblock = []
        depblock = []
        # Add feature set for pulling out unks
        feats = []
        # Add lines to arrays as arrays
        for cline in csent:
            ccgblock.append(cline.split())
        for predline in dsent:
            # dline = predline.replace('(',' ').replace('-',' ').replace(')','').replace(',','')
            dline = self.rm.dep2split(predline)
            depblock.append(dline.split())
        # Iterate through and pull info from match sentences
        knowndep = []
        for ccgdep in ccgblock:
            if len(ccgdep) >= 6:
                # print "yes"
                cat = ccgdep[2]
                argNum = str(ccgdep[3])
                # print cat
                cdep = ccgdep[4]
                cdepindex = ccgdep[0]
                cheadindex = ccgdep[1]
                chead = ccgdep[5]
                ccgPosArr = ldict.get(chead)
                ccgPOS = ccgPosArr[0][1]
                ccatpos = ldict.get(cdep)
                # special feature
                # distance = 'functor-'
                # if (int(cdepindex) - int(cheadindex)) > 0:
                #     distance = 'functor-first'
                # elif (int(cdepindex) - int(cheadindex)) < 0:
                #     distance = 'functor-last'
                # else:
                #     print("this shouldn't be happening, head index - dep index == 0", ccgdep)
                # If a sentense has multiple categories for the same word, choose the right one
                if len(ccatpos) > 1:
                    chosen = self.disambiguate(ccgblock,cdep,cdepindex)
                    # print chosen
                    try:
                        # print chosen, ccatpos
                        ccgargcat = ccatpos[chosen][0]
                        argpos = ccatpos[chosen][1]
                        # print ccargcat
                    except:
                        # Or the first in the case of errors
                        # TODO Why is chosen returning None?
                        print("Exception -- variable 'chosen' is empty somehow.")
                        ccgargcat = ccatpos[0][0]
                        argpos = ccatpos[0][1]
                else:
                    ccgargcat = ccatpos[0][0]
                    argpos = ccatpos[0][1]
                # self.direction(cat,ccgargcat)
                # poss = "functor-cat-is-" + cat + " " +  "functor-word-is-" + chead + " " + "functor-pos-is-" + ccgPOS + " " +  "arg-cat-is-" + ccgargcat + " " +  "arg-word-is-" + cdep + " " +  "arg-pos-is-" + argpos + " " +
                poss = "functor-cat-is-" + cat + " " +  "functor-word-is-" + chead + " " + "functor-pos-is-" + ccgPOS + " " +  "arg-cat-is-" + ccgargcat + " " +  "arg-word-is-" + cdep + " " +  "arg-pos-is-" + argpos + " " + "functor-cat-and-word-" + cat + "-" + chead + " " + "functor-cat-and-pos-" + cat + "-" + ccgPOS + " " + "functor-cat-and-arg-cat-" + cat + "-" + ccgargcat + " " + "functor-cat-and-arg-word-" + cat + "-" + cdep + " " + "functor-cat-and-arg-pos" + cat + "-" + argpos + " " 
                # poss += distance
                poss += " argnum-is-" + argNum
                # search = ".*" + poss
                # print search
                # pattern = re.compile(re.escape(search))
                featset = ''
                # printthese = []
                for depdep in depblock:
                    if len(depdep) == 5:
                        rel = depdep[0]
                        dhead = depdep[1]
                        ddep = depdep[3]
                        if chead == dhead and cdep == ddep:
                            featset = rel + "_normal " + poss
                            # print("otherRel:", depdep, self.otherRels(depblock, depdep, ccgdep))
                            # TODO these features performed worse -- delete or revisit
                            # otherRels = self.otherRels(depblock, depdep, ccgdep)
                            # for oR in otherRels:
                            #     if oR not in featset:
                            #         featset = featset + ' ' + oR
                            knowndep.append([rel , dhead , ddep])
                            #pass
                            # return featset
                            # print featset
                            # printthese.append(featset)
                        elif chead == ddep and cdep == dhead:
                            featset = rel + "_reverse " + poss
                            # print("otherRel:", depdep, self.otherRels(depblock, depdep, ccgdep))
                            # TODO these features performed worse -- delete or revisit
                            # otherRels = self.otherRels(depblock, depdep, ccgdep)
                            # for oR in otherRels:
                            #     if oR not in featset:
                            #         featset = featset + ' ' + oR
                            knowndep.append([rel , dhead , ddep])
                            #pass
                            # return featset
                            # print featset
                            # printthese.append(featset)
                        elif featset == '' and tnt == 'test':
                            featset = "unk_nodep " + poss
                            # print("otherRel:", depdep, self.otherRels(depblock, depdep, ccgdep))
                            # TODO these features performed worse -- delete or revisit
                            # otherRels = self.otherRels(depblock, depdep, ccgdep)
                            # for oR in otherRels:
                            #     if oR not in featset:
                            #         featset = featset + ' ' + oR
                            # return featset
                            # print featset
                            # printthese.append(featset)
                # returning it here seems to remove some data.
                # The above was a bug. It seemingly arbitrarily duplicates certain matchs,
                # one with the dep relation, the other as unk. Now it selects the correct one
                feats.append(featset)
        if tnt == 'test':
            # TODO depreciate this or keep for updating the classier subsequent eval?
            for unknowns in self.unkdeps(depblock, knowndep):
                feats.append(unknowns)
        return feats

    def otherRels(self, depblock, dep, ccg):
        """
        Find other rels related to the one in question and output those as features
        Didn't work really -- maybe in a neural model?
        :param depblock: dep sentence
        :param dep: dependency in question
        :return: set of other rels: [ccg-head-as-gov-REL1, ccg-head-as-dep-REL2, ccg-dep-as-gov-REL3, ccg-dep-...
        """
        # govRels = set()
        # depRels = set()
        otherRels = set()
        # no need for dep2split, it's already done
        for deps in depblock:
            if len(deps) > 1:
                rel = deps[0]
                head = deps[1]
                dependent = deps[3]
                if head == ccg[5] and rel != dep[0]:
                    otherRels.add('ccg-head-as-head-' + rel)
                elif dependent == ccg[5] and rel != dep[0]:
                    otherRels.add('ccg-head-as-dep-' + rel)
                elif head == ccg[4] and rel != dep[0]:
                    otherRels.add('ccg-dep-as-head-' + rel)
                elif dependent == ccg[4] and rel != dep[0]:
                    otherRels.add('ccg-dep-as-dep-' + rel)
        return otherRels

    def unkdeps(self, depblock, knowndep):
        """
        This function finds where for any SDC dep pair, there was no
        CCG dep pair. The goal of these was to see if we could predict
        the right dependency even if there was no lexical overlap.
        This was to evaluate the classifier's predictability in general.
        :param depblock: SDC output as array
        :param knowndep: triples that we've seen and have overlap with CCG
        :return: array of 'rel_noccg' with primitive feature set
        """
        unks = []
        for deps in depblock:
            unkdep = ''
            if len(deps) == 5:
                dhead = deps[1]
                ddep = deps[3]
                for known in knowndep:
                    if known[1] == dhead and known[2] == ddep:
                        unkdep = 'No'
                        # print 'No', known, dhead, ddep
            if unkdep == '' and len(deps) == 5:
                # print "It's triggered", deps[1], deps[3], "unkdep is: ", unkdep
                unk = deps[0] + "_noccg" + " functor-word-is-" + deps[1] + " arg-word-is-" + deps[3]
                unks.append(unk)
        # print unks
        return set(sorted(unks))
                            
    def lexbuilder(self,autostring):
        """
        Pulls in the auto file and builds a dictionary keyed of the words
        :param autostring: ccg auto file
        :return: dictionary of words with POS tags and categories
        """
        broken = autostring.split()
        # Creating hash to associate category and pos tuple to lexical entry
        lex = {}
        i = 0
        while i <= (len(broken) - 1):
            if broken[i] == '(<L':
                if broken[i+4] not in lex:
                    lex[broken[i+4]] = []
                # store them as an array so we can disambiguate later.
                lex[broken[i+4]].append((broken[i+1],broken[i+3]))
            i += 1
        neatlex = {}
        for lists in lex:
            neatlex[lists] = sorted(set(lex[lists]))
        # print neatlex
        return neatlex
        
    
    def disambiguate(self,ccgb,lex,inde):
        """
        This disambiguates when a lexical entry has multiple POS tags.
        Matches on lexical token and index.
        or categories in a sentence.
        :param ccgb: ccg block (sentence)
        :param lex: lexical dict
        :param inde: current index
        :return:
        """
        disamb = {}
        for entry in ccgb:
            if len(entry) == 6:
                if entry[4] == lex:
                    if lex not in disamb:
                        disamb[lex] = []
                    disamb[lex].append((int(entry[0])))
        choice = sorted(set(disamb[lex])).index(int(inde))
        return choice
                            
    def presults(self, reses, outfile):
        """
        Old print results function. Still useful?
        :param reses:
        :param outfile:
        :return:
        """
        o = open(outfile, 'w')
        for each in reses:
            if not each == None:
                o.write(each + '\n')
