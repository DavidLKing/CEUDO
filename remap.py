import sys
import re
import itertools
import os

#~ pipeline:
    #~ load files as dictionaries (change renaming script to work without the weird final sentences thing
    #~ sdtout = debug output
    #~ other output written to files -- always
    #~ only pull from pargs
        #~ remap conjes
        #~ 1.1.1) shared arguments (these will cause us to predict a new relation if SDs don't have it and finally create a 'sub' relation between args and the conjunct)
        #~ 1.1.2) shared functors/modifiers will cause the SD relation originally pointing to the head of the cc relation to point to the conjunct -- this will need no sub relations
        #~ 1.1.3) no shared functors or arguments -- this should be rarer and only occur with full phrasal coordination -- we will simply remap, and will probably need a 'sub' relation from the conjoined tokens to the conjunct to prevent the conjunct from becomming a second roots.

class remap():
    def __init__(rm):
        pass
        
    def actualstart(rm, outform, parg, auto, sdFile, debug):
        """
        A lot of this is not in __init__ since this class has other useful function.
        :param outform: -n, -c, -d <- "normal", "conll", or "SDC - dependency"
        :param parg: CCG parg file
        :param auto: CCG auto file
        :param sdFile: SDC output
        :param debug: debugging flag with extra output
        :return:
        """
        if outform not in ['-n', '-c', '-d']:
            formaterror = "output formats can only be:\n\t-c -- for CoNLL 2008 formatting\n\t-n -- for simple tab delimited dependency output\n\t-d -- for Stanford Dependency output"
        else:
            rm.of = outform
        #get basename:
        rm.basename = os.path.splitext(parg)[0]
        p = open(parg, 'r')
        a = open(auto, 'r')
        s = open(sdFile, 'r')
        rm.parg = rm.other2dict(p, 'p')
        rm.auto = rm.other2dict(a, 'a')
        rm.sdfi = rm.other2dict(s, 'd')
        # phrasal coord flag:
        rm.phrasal = False
        # maxent outfile
        me = 'maxent.txt'
        rm.maxout = open(me, 'a')
        # newconj file
        co = "newconj.txt"
        rm.conjOut = open(co, 'a')
        if debug == 'no':
            rm.debug = False
        elif debug == '--debug':
            rm.debug = True
            print('DEBUGGING IS TURNED ON')

    def checkoutput(rm):
        """
        # This function is not needed, but gives a good idea of what the data looks like
        :return:
        """
        for each in rm.parg:
            print("parg", each)
            for every in rm.parg[each]:
                print(every)
                # ['1', '0', '(S/S)/NP', '2', 'addition', 'In']
        for each in rm.auto:
            print("auto", each)
            for every in rm.auto[each]:
                print(every, rm.auto[each][every])
                # in [('((S\\NP)\\(S\\NP))/NP', 'IN'), ('(NP\\NP)/NP', 'IN')]
                # the [('NP[nb]/N', 'DT'), ('NP[nb]/N', 'DT'), ('NP[nb]/N', 'DT'), ('NP[nb]/N', 'DT')]
        for each in rm.parg:
            print("sdfi:", each)
            for every in rm.sdfi[each]:
                print(every)
                # ['case', 'addition', '2', 'In', '1']

    def lexbuilder(rm,autostring):
        """
        building a dictionary of lexical entries with their CCG cat. and PTB POS
        tag -- This is mostly used for pulling argument categories. Each line is
        broken into an array, and only the first 5 entries after an entry matching
        (<L. Note that this is the same as cdc.py's lexbuilder, but holds more info.
        :param autostring:
        :return:
        """
        broken = autostring.split()
        # Creating hash to associate category and pos tuple to lexical entry
        lex = {}
        i = 0
        while i < len(broken):
            if broken[i] == '(<L':
                if broken[i+4] not in lex:
                    lex[broken[i+4]] = []
                lex[broken[i+4]].append((broken[i+1],broken[i+3], broken[i+5]))
            i += 1
        return lex
        
    def other2dict(rm, depPargAuto, dpa):
        """
        This function creates dictionaries keyed on the ID.
        :param depPargAuto: an SD, a CCG Parg, or a CCG Auto file
        :param dpa: either 'd', 'p', or 'a' depending on whether
        :return: a dictionary
        """
        dict1 = {}
        # empty variable to write over
        placeID = ''
        # auto files
        if dpa == 'a':
            for line2 in depPargAuto:
                #~ print("other2dict, line2: ", line2)
                check1 = re.match('ID=(.*) PARSER=GOLD NUMPARSE=1',line2)
                if check1 != None:
                    placeID = check1.group().replace('ID=','').replace('PARSER=GOLD NUMPARSE=1', '').strip()
                    #~ print("other2dict, first case, dpa = a, PlaceID: ", placeID)
                    dict1[placeID] = {}
                else:
                    #~ dict1 = rm.lex2dict(depPargAuto)
                    #~ print("other2dict, second case, dpa = a, PlaceID: ", placeID)
                    dict1[placeID] = rm.lexbuilder(line2)
        # CCG or SDC dep files
        elif dpa == 'p' or dpa == 'd':
            for line0 in depPargAuto:
                #~ print("other2dict, p or d, line0: ", line0)
                check0 = re.match('<s id="(.*)">',line0)
                if check0 != None:
                    placeID = check0.group(0).replace('<s id="','').replace('">','')
                    assert(check0 not in dict1),"other2dict error: index already present in dictionary!"
                    dict1[placeID] = []
                elif check0 == None:
                    errormsg = "Duplicate line entries for " + line0 + "in" + str(dict1)
                    #~ print(line0)
                    if line0 in dict1:
                        print(errormsg)
                    if dpa == 'd':
                        dict1[placeID].append(rm.dep2split(line0.strip()).split())
                    elif dpa == 'p':
                        dict1[placeID].append(line0.strip().split())
                else:
                    print("I don't know what happened: ", line0, check0)
        return dict1
        
    def dep2split(rm,depstring):
        """
        The more useful function I've ever written. Converts
        det(cat-2, the-1) type representations to simply a
        string ready to be split: det cat 2 the 1 -- using
        split() then gives you an array
        :param depstring:
        :return:
        """
        # This used to be two lines:
        # depsplit = depstring.replace('(',' ').replace(')',' ').replace('-', ' ').replace(',', ' ')
        # but we were splitting hypenated words and punct(,-# type entries
        # splat is the passed tense of split ;-)
        splat = depstring.replace('(',' ').replace(')','').split()
        # ensure this is not a wsj_ string
        if len(splat) == 3:
            # remove the comma
            ind1 = splat[1].split('-')[-1][0:-1]
            ind2 = splat[2].split('-')[-1]
            # base case
            if len(splat[1].split('-')) == 2:
                word1 = splat[1].split('-')[0]
            # account for hyphenated words
            elif len(splat[1]) > 2:
                word1 = '-'.join(splat[1].split('-')[0:-1])
            # possible errors
            elif len(splat[1].split('-')) < 2:
                print("ERROR!!! Splitting the entry by hyphens has only generated one category [first split]", splat)
            if len(splat[2].split('-')) == 2:
                word2 = splat[2].split('-')[0]
            elif len(splat[2]) > 2:
                word2 = '-'.join(splat[2].split('-')[0:-1])
            elif len(splat[2].split('-')) < 2:
                print("ERROR!!! Splitting the entry by hyphens has only generated one category [second split]", splat)
            protoReady = (splat[0], word1, ind1, word2, ind2)
            depsplit = ' '.join(protoReady)
            # print(depsplit.split())
            return depsplit
        else:
            # print("Ignoring", depstring, splat)
            return  'ignore'
    
    def indexes(rm, ccg3, dep3):
        """
        This happens before we find the matches!
        Create a mapping from CCG indicies to SDC's.
        Very important for later on.
        :param ccg3:
        :param dep3:
        :return:
        """
        c2d = {}
        d2c = {}
        dephash = {}
        ccghash = {}
        ccgIndArray = []
        #~ doff = 0
        # split and create dictionaries with index as key and string as value
        for deps in dep3:
            if len(deps) >= 5:
                dephash[deps[4]] = deps[3]
        # add root for later code to not key-error on dephash[0]
        dephash['0'] = 'ROOT'
        for ccgs in ccg3:
            if len(ccgs) >= 6:
                ccghash[ccgs[0]] = ccgs[4]
                ccghash[ccgs[1]] = ccgs[5]
                ccgIndArray.append(int(ccgs[0]))
                ccgIndArray.append(int(ccgs[1]))
        ccgIndArray = sorted(set(ccgIndArray))
        """
        all CCG indicies have been loaded into ccgIndArray
        and dephash and ccgHash for tokens for each one
        now lets call the indexWalker function to get how
        off SDs are from CCG indicies and add those to c2d
        """
        for ind in ccgIndArray:
            ind, doff = rm.indexWalker(ind, 0, ccghash, dephash)
            c2d[ind] = ind + doff
        # Then invert that so we can access it faster later
        for i0 in c2d:
            d2c[c2d[i0]] = i0
        if rm.debug == True:
            print("indexes c2d and d2c\n", c2d, '\n', d2c, "\nccghash\n", ccghash, "\ndephash\n", dephash, "\nAnd the arrays")
            for c in ccg3:
                print(c)
            for d in dep3:
                print(d)
        return c2d, d2c
        
    def indexWalker(rm, i, offset, chash, dhash):
        """
        recursively find the offset for allign indicies
        Note: loading erroneous (non-matching) files into
        this program will cause the recursive loop to never
        ever terminate... like ever never.
        :param i: index
        :param offset: current offset
        :param chash: ccg hash keyed on index
        :param dhash: sdc hash keyed on index
        :return: index and new offset
        """
        if str(i) in chash and str(i + offset) in dhash:
            if chash[str(i)] == dhash[str(i + offset)]:
                pass
            else:
                offset += 1
                i, offset = rm.indexWalker(i, offset, chash, dhash)
        return i, offset
    
    def iterate(rm):
        """
        This isn't a real function. This is essentially where
        we iterate through all the iDs and process everything.
        Think of it more as a controller than a utility
        :return:
        """
        # iD is a sentnece
        for iD in rm.parg:
            if rm.debug == True:
                print('iD in iterate', iD)
            rm.sdfi[iD] = rm.conjremap(rm.parg[iD], rm.auto[iD], rm.sdfi[iD], iD)
            # getting index allignment
            c2d, d2c = rm.indexes(rm.parg[iD], rm.sdfi[iD])
            # shared functs -- whoops, this should have been set to args
            ### TODO change 'findSharedCCGFunctArgs' to 'findConjoinedFunctors' -- this is confusing
            # sharedFuncts = rm.findSharedCCGFunctArgs(rm.parg[iD], rm.auto[iD], rm.sdfi[iD], 'functors', c2d)
            # shared args
            # Do conjoined elements share an argument?
            sharedArgs = rm.findSharedCCGFunctArgs(rm.parg[iD], rm.auto[iD], rm.sdfi[iD], 'args', c2d)
            # Are they're any unbounded/conjoined dependency annotation?
            xbxu = rm.findXBXU(rm.parg[iD], rm.auto[iD], rm.sdfi[iD], c2d)
            """ Possibly still useful stuff -- probably not though """
            #~ if sharedFuncts != []:
                #~ oneups = rm.oneUpFuncts(sharedFuncts, rm.parg[iD], rm.auto[iD], c2d)
            #~ else:
                #~ oneups = [[]]
            #~ for each in sharedFuncts:
                #~ print("sharedFuncts:", each)
            #~ for each in sharedArgs:
                #~ print("sharedArgs:", each)
            # for the aclrelcls:
            #~ aclrelcl = rm.findAclRelCl(rm.parg[iD], rm.auto[iD], rm.sdfi[iD], c2d)
            # Find underspecified dep relations
            depRels = rm.findDeps(rm.parg[iD], rm.auto[iD], rm.sdfi[iD], d2c)
            # Additional free relative check
            relQs = rm.findRelQues(rm.parg[iD], rm.auto[iD], rm.sdfi[iD], c2d)
            if rm.debug:
                print("Before prunning:")
                #~ print("\t Shared functs:", sharedFuncts)
                print("\t Shared args:", sharedArgs)
                print("\t depRels:", depRels)
                print("\t relQs:", relQs)
                print("\t Shared xbxu:", xbxu)
                print("\t Deps:", depRels)
                #~ print("\t Shared oneups:", oneups)
            # sharedFuncts = rm.onlyPullNew(sharedFuncts, rm.sdfi[iD], c2d)
            sharedArgs = rm.onlyPullNew(sharedArgs, rm.sdfi[iD], c2d)
            # I don't think we want to prune the aclrelcls
            #~ aclrelcl = rm.onlyPullNew(aclrelcl, rm.sdfi[iD], c2d)
            xbxu = rm.onlyPullNew(xbxu, rm.sdfi[iD], c2d)
            #~ if oneups != [[]]:
                #~ oneups = rm.onlyPullNew(oneups, rm.sdfi[iD], c2d)
            if rm.debug == True:
                print("After prunning:")
                # print("\t Shared functs:", sharedFuncts)
                print("\t Shared args:", sharedArgs)
                print("\t relQs:", relQs)
                print("\t depRels:", depRels)
                #~ print("\t aclrelcl:", aclrelcl)
                print("\t Shared xbxu:", xbxu)
                print("\t Deps:", depRels)
                #~ print("\t Shared oneups:", oneups)
            # TODO finally give in and delete the triggers we're no long using
            # Time to write everything out to file
            #~ rm.maxWrite(sharedFuncts, c2d, rm.auto[iD], iD, 'n')
            if relQs != []:
                rm.maxWrite(relQs, c2d, rm.auto[iD], iD, 'n')
            if depRels != []:
                rm.maxWrite(depRels, c2d, rm.auto[iD], iD, 'n')
            rm.maxWrite(sharedArgs, c2d, rm.auto[iD], iD, 'n')
            # rm.maxWrite(sharedFuncts, c2d, rm.auto[iD], iD, 'n')
            # these are really deps
            #~ if aclrelcl != []:
                #~ rm.maxWrite(aclrelcl, c2d, rm.auto[iD], iD, 'rev')
            rm.maxWrite(xbxu, c2d, rm.auto[iD], iD, 'n')
            #~ if oneups != [[]]:
                #~ rm.maxWrite(oneups, c2d, rm.auto[iD], iD)
        print("rm.basename", rm.basename)
        print("Remember, the maxent and newconj files get appended to. Delete it if we're doing a new run.")
    
    def findXBXU(rm, pargs, lexes, depses, c2dDict):
        """
        This finds <XU> and <XB> annotations, then pulls them wholesale for prediction
        :param pargs: CCG parg array
        :param lexes: lexical info
        :param depses:
        :param c2dDict:
        :return:
        """
        match = []
        # TODO does the CCG side really need this weird data structure? [ [ [], [], [] ] ]?
        ccgFixer = []
        for parg in pargs:
            if len(parg) == 7:
                xBXU = parg[6]
                if xBXU == '<XB>' or xBXU == '<XU>':
                    ccgFixer.append(parg)
                    ### quick auxiliary scan for shared functors 
                    ### in case the conj remap fails
                    appended = False
                    for p in pargs:
                        if len(p) == 6:
                            try:
                                if p[0] == parg[0]:
                                    if p[2] == parg[2]:
                                        # TODO we should also match on p[3]
                                        # but the code errors out
                                        # possibly python mutable type issue
                                        # re: 2412.51 tradition.*undercut
                                        if p[4] == parg[4]:
                                            if rm.debug == True:
                                                print("adding shared functor with this XBXU", p)
                                            ccgFixer.append(p)
                                            appended = True
                            except:
                                if rm.debug == True:
                                    print("exception in findXBXU:", p, parg)
                    if rm.debug == True:
                        if appended == False:
                            print("No shared functors found for XBXU", parg)
        match.append(ccgFixer)
        return match
                    
    def maxWrite(rm, newArray,c2d0, lex1, placeID, rev):
        """
        Simply write everything to a file for maxent predict and collation later
        :param newArray: array of new predictions that need to be UDs
        :param c2d0: ccg to sdc index converter
        :param lex1: lexical dictionary
        :param placeID: ID so we know where these edits go later
        :param rev: Are we reversing this? y/n?
        :return:
        """
        if rm.debug == True:
            print("maxWrite c2d0 dump", c2d0)
        for c in newArray:
            #~ rm.maxout
            print("\t c ", c)
            try:
                aindex = int(c[0])
                findex = int(c[1])
                argNum = str(c[3])
                cat = c[2]
                chead = c[5]
                cdep = c[4]
                ccgPOS = lex1[chead][0][1]
                ccgargcat = lex1[cdep][0][0]
                argpos = lex1[cdep][0][1]
                # special feature
                # distance = 'functor-'
                # if (int(aindex) - int(findex)) > 0:
                #     distance = 'functor-first'
                # elif (int(aindex) - int(findex)) < 0:
                #     distance = 'functor-last'
                # else:
                #     if rm.debug == True:
                #         print("this shouldn't be happening, head index - dep index == 0", c)
                # sys.exit()
                # I think these kinds of lines can be cleaned up with 
                # an array and the .join() function, but would it be 
                # more efficient?
                # quick, for relacls, if rev = 1, switch functor and args, otherwise:
                if rev == 'rev':
                    poss = "functor-cat-is-" + ccgargcat + " " +  "functor-word-is-" + cdep + " " + "functor-pos-is-" + argpos + " " +  "arg-cat-is-" + cat + " " +  "arg-word-is-" + chead + " " +  "arg-pos-is-" + ccgPOS + " " + "functor-cat-and-word-" + ccgargcat + "-" + cdep + " " + "functor-cat-and-pos-" + ccgargcat + "-" + argpos + " " + "functor-cat-and-arg-cat-" + ccgargcat + "-" + cat + " " + "functor-cat-and-arg-word-" + ccgargcat + "-" + chead + " " + "functor-cat-and-arg-pos" + ccgargcat + "-" + ccgPOS + " argnum-is-" + argNum #+ " " + distance
                else:
                    poss = "functor-cat-is-" + cat + " " +  "functor-word-is-" + chead + " " + "functor-pos-is-" + ccgPOS + " " +  "arg-cat-is-" + ccgargcat + " " +  "arg-word-is-" + cdep + " " +  "arg-pos-is-" + argpos + " " + "functor-cat-and-word-" + cat + "-" + chead + " " + "functor-cat-and-pos-" + cat + "-" + ccgPOS + " " + "functor-cat-and-arg-cat-" + cat + "-" + ccgargcat + " " + "functor-cat-and-arg-word-" + cat + "-" + cdep + " " + "functor-cat-and-arg-pos" + cat + "-" + argpos + " argnum-is-" + argNum #+ " " + distance
                try:
                    daindex = str(c2d0[aindex])
                except:
                    daindex = str(aindex)
                try:
                    dfindex = str(c2d0[findex])
                except:
                    dfindex = str(findex)
                ###GET SKIPGRAM RELATIONS###
                # TODO these features made the classifier perform poorly -- delete or revisit
                # fauxDep = ' '.join(['rel', chead, dfindex, cdep, daindex])
                # skipGramRels = rm.otherRels(rm.sdfi[placeID], fauxDep, c)
                # if rm.debug:
                #     print("\tFauxdep =", fauxDep)
                #     print("\tskipGramRels:")
                # for s in skipGramRels:
                #     poss = poss + ' ' + s
                #     if rm.debug:
                #         print("\t\t", s)
                featset = "unk_nodep " + poss
                ###BEGIN WRITING###
                if rev == 'rev':
                    almostString0= placeID, cdep, daindex, chead, dfindex, featset
                else:
                    # Sometimes the parg files skip a word so we have no key
                    try:
                        almostString0= placeID, chead, str(c2d0[findex]), cdep, str(c2d0[aindex]), featset
                    except:
                        almostString0= placeID, chead, str(findex), cdep, str(aindex), featset
                outString0 = '\t'.join(almostString0) + '\n'
                if rm.debug == True:
                    print("\t\tMaxent feature dump:\n", outString0)
                rm.maxout.write(outString0)
            except:
                for ccgdeps in newArray:
                    if rm.debug == True:
                        print("Failure on pulling indexes:", ccgdeps)
    
    def onlyPullNew(rm, matched, deps3, c2d1):
        """
        Don't pull things that already exist or that are duplicated
        :param matched: new deps that might be good
        :param deps3: SDC output
        :param c2d1: CCG to SDC index converter
        :return:
        """
        # TODO this has become a general 'do not pull' list -- consider renaming
        # prune the matched deps -- delete them otherwise
        returnable = []
        #~ print(c2d1)
        # CCGs are a double list: [[[],[]]]
        for dubList in matched:
            for singleList in dubList:
                add = True
                # stop predicting extra case relations for (chairman of) the board
                if singleList[2] == '(NP\\NP)/NP' and \
                     int(singleList[0]) < int(singleList[1]):
                    if rm.debug == True:
                        print("\tnot adding -- wrong prep direction:\n\t", singleList)
                    add = False
                else:
                    for dList in deps3:
                        #~ if rm.debug == True:
                            #~ print("onlyPullnew dList:", dList)
                            #~ print("onlyPullnew singleList:", singleList)
                            #~ print("onlyPullnew c2d1:", c2d1)
                        #~ print(dList, singleList)
                        if len(dList) >= 3 and \
                           len(singleList) >= 6:
                            if dList[0] != 'acl:relcl' and \
                               dList[2] == str(c2d1[int(singleList[0])]) and \
                               dList[1] == singleList[4] and \
                               dList[4] == str(c2d1[int(singleList[1])]) and \
                               dList[3] == singleList[5]:
                                if rm.debug == True:
                                    print("\tnot adding -- exists 1:\n\t", singleList, dList)
                                add = False
                            elif dList[0] != 'acl:relcl' and \
                                 dList[4] == str(c2d1[int(singleList[0])]) and \
                                 dList[3] == singleList[4] and \
                                 dList[2] == str(c2d1[int(singleList[1])]) and \
                                 dList[1] == singleList[5]:
                                if rm.debug == True:
                                    print("\tnot adding -- exists 2:\n\t", singleList, dList)
                                add = False
                            # stop predicting extra nsubjs for these
                            elif dList[0] in ['cop', 'aux', 'auxpass'] and \
                                 dList[4] == str(c2d1[int(singleList[1])]) and \
                                 dList[3] == singleList[5]:
                                if rm.debug == True:
                                    print("\tnot adding -- aux, cop, or auxpas:\n\t", singleList, dList)
                                add = False
                            else:
                                pass
                    if add == True:
                        returnable.append(singleList)
        return returnable
    
    def findRelQues(rm, parg2, auto2, sdfi2, c2d):
        """
        A function for finding free relatives
        :param parg2: CCGBank dependency array
        :param auto2: CCGBank derivation file
        :param sdfi2: Stanford Dependency array
        :param c2d: CCGBank to SDC index converter
        :return: CCGs that fit the free relative regular expressions
        """
        # TODO clean unused variables in function call
        returnCCGs = []
        possibles = []
        for ccgs in parg2:
            if len(ccgs) > 5:
                # DO WE WANT TO MATCH THESE FROM ANYWHERE?
                if re.match('NP/.*S.*', ccgs[2]) != None:
                    possibles.append(ccgs)
                    if rm.debug == True:
                        print("FindRelQues: matched on NP/.*S.* regex", ccgs[2], ccgs[5], ">", ccgs[4])
        for ccgs in parg2:
            if len(ccgs) > 5:
                for poss in possibles:
                    if ccgs[4] == poss[5]:
                        returnCCGs.append(ccgs)
        return returnCCGs
    
    def findDeps(rm, parg2, auto2, sdfi2, d2c):
        """
        a function to get the 'dep' relations from SDC
        :param parg2:
        :param auto2:
        :param sdfi2:
        :param d2c:
        :return:
        """
        if rm.debug == True:
            print("\t CHECKING FOR dep relations")
        outs = []
        for deps in sdfi2:
            if deps[0] == 'dep':
                revamp = False
                for ccg in parg2:
                    # only pull deps we have CCGs for
                    if deps[1] in ccg and deps[3] in ccg:
                        dep = []
                        print(deps)
                        print(auto2[deps[1]])
                        print(auto2[deps[3]])
                        print(ccg)
                        # arg index
                        # adding for index mismatches
                        # TODO report SDC bug where indexes get an extra ' after them
                        try:
                            dep.append(d2c[int(deps[4].strip("'"))])
                        except:
                            dep.append(int(deps[4].strip("'")))
                        # funct index
                        try:
                            dep.append(d2c[int(deps[2].strip("'"))])
                        except:
                            dep.append(int(deps[2].strip("'")))
                        # funct cat
                        try:
                            dep.append(auto2[deps[1]][0][0].replace('/', '\/'))
                        except:
                            # TODO this is a hack re: Journal/Europe not matching
                            # Journal\/Europe
                            dep.append("N")
                        # unknown arg num
                        dep.append("UNK")
                        # arg token
                        dep.append(deps[3])
                        # funct token
                        dep.append(deps[1])
                        outs.append(dep)
                        if rm.debug == True:
                            print("revamping", deps, 'with', ccg)
                        revamp = True
                if rm.debug == True and revamp == False:
                    print("dep not changed -- no CCG for", deps)
        #~ if outs != []:
            #~ print(outs)
        return outs

    def findSharedCCGFunctArgs(rm, parg1, auto1, sdfi1, funarg, c2d):
        """
        This function scans a given pair of conjoined words and scans
        for any shared functors or arguments they might have.
        :param parg1: ccg parg file
        :param auto1: ccg auto file
        :param sdfi1: sdc output
        :param funarg: functor or args?
        :param c2d: ccg to sdc index converter
        :return: matches
        """
        # pull all the conj tokens and their indicies and safe them
        conjToks = []
        for deps1 in sdfi1:
            if deps1[0] == 'conj':
                # leftover from previous remaps
                assert(deps1[0] != 'conj1' or deps1[0] == 'conj2')
                # tuples like in binarize function (##, token)
                conjToks.append((deps1[2], deps1[1]))
                conjToks.append((deps1[4], deps1[3]))
        if funarg == 'functors':
            if rm.debug == True:
                print("\t CHECKING FOR SHARED FUNCTORS")
            matchTok = 4
            matchInd = 0
            otherTok = 5
            otherInd = 1
            if rm.debug == True:
                print("\t matchTok:", matchTok, "matchInd:", matchInd)
        # depreciated
        elif funarg == 'args':
            if rm.debug == True:
                print("\t CHECKING FOR SHARED ARGS")
            matchTok = 5
            matchInd = 1
            otherTok = 4
            otherInd = 0
            if rm.debug == True:
                print("\t matchTok:", matchTok, "matchInd:", matchInd)
        else:
            errorMsg = "Error: funargs variable in findSharedCCGFunctArgs can only be 'functors' or 'args': " + funarg
            sys.exit(errorMsg)
        # Save all the CCG deps from the PARG file, then prune
        matches = {}
        # if the count increments to equal the length of conjToks, then we have a match
        #~ count = 0
        for ccgDeps in parg1:
            if len(ccgDeps) >= 6:
                # get the correct index:
                depMatInd = c2d[int(ccgDeps[matchInd])]
                assert(type(depMatInd) == int), 'Error with c2d not giving us an index'
                depMatInd = str(depMatInd)
                for cT in conjToks:
                    if (depMatInd, ccgDeps[matchTok]) == cT:
                        if rm.debug == True:
                            print("\t\tsingle match, key ((ccgDeps[otherInd], ccgDeps[otherTok])):\n\t\t", (ccgDeps[otherInd], ccgDeps[otherTok]), "\n\t\tcT", cT, "\n\t\tccgDeps", ccgDeps, "\n\t\tdepMatInd:", depMatInd)
                        # create array with tuple as key.
                        if (ccgDeps[otherInd], ccgDeps[otherTok]) not in matches:
                            matches[(ccgDeps[otherInd], ccgDeps[otherTok])] = []
                        matches[(ccgDeps[otherInd], ccgDeps[otherTok])].append(ccgDeps)
        # only pull matches whose count is > 1
        shared = []
        if matches != {}:
            for m in matches:
                if rm.debug == True:
                    print("\t### matches", m, "len(matches[m])", len(matches[m]), "###")
                    for ccgs in matches[m]:
                        print('\tin matches =', ccgs)
                deplist = matches[m]
                deplist.sort()
                if len(deplist) > 1:
                    if rm.debug:
                        print("match[m] is longer than one! Proceed!")
                    # this gives us a list of unique elements
                    # sorted(set()) won't work on a list of lists : (
                    new = list(deplist for deplist,_ in itertools.groupby(deplist))
                    """
                    We're going to try and reimplement this...
                    this killed us -- prepositional verbs got really weird
                    """
                    if rm.debug == True:
                        print("\tStarting traversal")
                    traversed = rm.traverse(parg1, auto1, new, funarg)
                    if traversed != []:
                        for t in traversed:
                            if rm.debug == True:
                                print("\tadding from traversed:", t)
                            new.append(t)
                    if rm.debug == True:
                        print("\tlen(matches) as new:", len(new), "len(conjToks)", len(conjToks), "m", m,)
                        for n in new:
                            print("\t\tin new:", n)
                    if len(new) >= 2:
                        shared.append(new)
                        if rm.debug == True:
                            print("\tFound a match:", m)
                        for ccgdeps in new:
                            if rm.debug == True:
                                print('\t', ccgdeps)
                    elif len(new) < 2:
                        if rm.debug == True:
                            print("\tNot a shared match:", m)
                        for each in new:
                            print('\t', each)
                else:
                    if rm.debug:
                        print("match[m] is not longer than one! Shall not pass!!")
        else:
            if rm.debug == True:
                print("\tNo matches found")
        # this is the result of that naming issue
        #~ if funarg == 'args':
            #~ shared = rm.pruneArgForMods(parg1, auto1, sdfi1, funarg, c2d, shared)
        return shared
    
    def traverse(rm, parg, auto, matches, fa):
        """
        Try and traverse some to some depth and see whether we can build
        predictions for examples like "applied for and got bonus pay."
        CCG will have a different structure, so we'll need to traverse the
        dependency structure a little bit.
        :param parg: list of CCG dependencies for the whole sentence
        :param matches: new, from findShared, and is a list of CCGdeps with a conjTok in them
        :param fa: functor or argument, should be 'functors' or 'args'
        :return: array of faux CCG dependencies where NP/PP cats have been traversed over
        target = wsj_0044.parg:11         7       PP/NP   1       pay for <XU>
        """
        functs = []
        args = []
        functArgPairs = []
        build = []
        returnThese = []
        # somethhing to build a fake ccg dep
        functors = {}
        for m in matches:
            functs.append((m[5], m[1]))
            args.append((m[4], m[0]))
        # pull all args
        for ccg in parg:
            if len(ccg) > 4:
                functArgPairs.append(((ccg[5], ccg[1]), (ccg[4], ccg[0])))
                functors[ccg[5]] = ccg[2]
                #~ print("CCGS", ccg)
                if (ccg[5], ccg[1]) in functs:
                    print("\t\tfound the first match", ccg)
                args.append((ccg[4], ccg[0]))
        # find ones whose matching funct and arg are both in args
        for ccg in parg:
            if len(ccg) > 4:
                if (ccg[5], ccg[1]) in args and \
                   (ccg[4], ccg[0]) in args and \
                   ccg[2] == 'PP/NP' and \
                   (ccg[5], ccg[1]) not in functs:
                    # enumerate all possible funct arg combos, and pull the
                    # ones where 'for' in 'applied for pay' alligns
                    for poss in functs:
                        if (poss, (ccg[4], ccg[0])) not in functArgPairs and \
                           (poss, (ccg[5], ccg[1])) in functArgPairs:
                            # presumably this won't always be '2', but for now
                            fauxdep = [ccg[0], poss[1], functors[poss[0]], '2', ccg[4], poss[0]]
                            if rm.debug == True:
                                print("\t\tfound a matching one:", fauxdep)
                            build.append(fauxdep)
        # quickly adding the conj portion of this
        # we forgot the 'won pay' portion
        conjPair = []
        for firstConj in build:
            if firstConj not in conjPair:
                conjPair.append(firstConj)
            for ccg in parg:
                if ccg[0] == firstConj[0] and \
                   ccg[4] == firstConj[4] and \
                   ccg != firstConj and \
                   (ccg[5], ccg[1]) in functs:
                    if ccg not in conjPair:
                        conjPair.append(ccg)
                        if rm.debug:
                            print("\t\tfound a conjoined match for", firstConj, ",", ccg)
        return conjPair

    def pruneArgForMods(rm, parg, auto, sdfi, funarg, c2d, shared):
        """
        Old modifier function. Not used. Possibly delete this.
        :param parg:
        :param auto:
        :param sdfi:
        :param funarg:
        :param c2d:
        :param shared:
        :return:
        """
        # pull out the functors and see if they're modifiers
        shortList = []
        if rm.debug == True:
            print("\tpruneArgsForMods shared", shared)
        for sh in shared:
            for ccgdep in sh:
                #~ print("pruneArgsForMods lex entires", auto)
                print("\t\t", ccgdep)
                shortList.append((ccgdep[5], auto[ccgdep[5]][0][2]))
        shortList = sorted(set(shortList))
        if rm.debug == True:
            print("\tShortlist!!!!", shortList)
        regex = '([0-9]+)'
        r = re.compile(regex)
        returnArray = []
        for sL in shortList:
            addIt = False
            found = r.findall(sL[1])
            if rm.debug == True:
                print("\t\tFound from shortlist", found)
            counts = {}
            for index in found:
                if index not in counts:
                    counts[index] = 1
                    if rm.debug == True:
                        print("\t\tADDIT STATE:", addIt)
                else:
                    counts[index] += 1
                    addIt = True
                    print("\t\tADDIT STATE:", addIt)
            if rm.debug == True:
                print("\t\tIndex counts for", sL, ":", counts)
            if addIt == True:
                for sh in shared:
                    for ccgdep in sh:
                        print("ccgdep[5] and sL[0]", ccgdep[5], sL[0])
                        if ccgdep[5] == sL[0]:
                            if rm.debug == True:
                                print("\t\tAdding", sh, "-- it should be a modifier")
                            returnArray.append(sh)
        if rm.debug == True:
            print("\tShared mods from Shared args:", returnArray)
        return returnArray
        
    def conjremap(rm, parg0, auto0, sdfi0, placeID0):
        """
        Although currently not used by collate.py, this idea here
        was to binarize conjunction. The Scala and induction code
        does that now.
        :param parg0:
        :param auto0:
        :param sdfi0:
        :param placeID0:
        :return:
        """
        # sentence level
        # isolate the cc and conj rels.
        ccconj = []
        for deps1 in sdfi0:
            #~ if rm.debug == True:
                #~ print("\tdeps1", deps1)
            #~ conjmatch = re.match('conj.*', deps1[0])
            if deps1[0] == 'conj' or deps1[0] == 'cc':
                if rm.debug == True:
                    print("\t\tFound cc or conj:", deps1)
                ccconj.append(deps1)
                # I have no idea why, but this somehow preemptively deletes all cc rels... 
                # do not activate
                # do investigate
                #~ sdfi0.pop(sdfi0.index(deps1))
            else:
                if rm.debug == True:
                    print("\t\tNo cc or conj found:", deps1)
        remapThese = {}
        remappable = {}
        # temp check 
        deletethis = []
        # create a dictionary based on cc heads as the head so conjes are grouped correctly
        for c0 in ccconj:
            ### problems, SDs flatten multi-conj structure
            ### FIX THIS 
            ### w, x, & y ... and z > cc w &; conj w x; conj w y; cc w and; conj w z
            ### see: wsj_0029.7
            if c0[0] == 'cc':
                # using a / to avoid confict with hyphenated words
                if rm.debug == True:
                    print("found cc for key", c0)
                newkey = "/".join(c0) #'/'.join([c0[1], c0[2]])
                conjunctKey = '/'.join([c0[3], c0[4]])
                remapThese[newkey] = c0
                remappable[conjunctKey] = []
                # temp check
                deletethis.append(c0)
        # add conjes to appropriate conjunct
        for c1 in ccconj:
            key = '/'.join([c1[1], c1[2]])
            #~ c1match = re.match('conj.*', c1[0])
            for r in remapThese:
                rArray = r.split("/")
                rT = "/".join([rArray[1], rArray[2]])
                if c1[0] == 'conj' and key == rT:
                    # this will stop us from getting gaps, but will
                    # also give us strange conj structure
                    ### XXX Fix TODO ###
                    actualKey = "/".join([rArray[1], rArray[2]])
                    conjKey = "/".join([rArray[3], rArray[4]])
                    if rm.debug == True:
                        print("are we getting this far? ct", c1, "\n\trT", rT, rArray, "/".join([rArray[3], rArray[4]]), "\n\tkey", key, "\n\tremappable before adding", remappable, "\n\tremapThese[actualKey]", remapThese[r], "\n\tactualKey", actualKey, "conjKey", conjKey)
                    remappable[conjKey].append(key)
                    remappable[conjKey].append('/'.join([c1[3], c1[4]]))
                    # temp check
                    deletethis.append(c1)
        # sort unique them for cleanliness
        for r in remappable:
            remappable[r] = sorted(set(remappable[r]))
        if rm.debug == True:
            print("All conj and cc found:", deletethis)
            print("RemapThese:", remapThese)
            print("Remappable:", remappable)
        # delete the duplicates and remove empties
        key2del0 = []
        for cj in remappable:
            remappable[cj] = sorted(set(remappable[cj]))
            if remappable[cj] == []:
                key2del0.append(cj)
            else:
                errorMsg0 = ' '.join([cj, str(remappable[cj]), "len =", str(len(remappable[cj]))])
                assert(len(remappable[cj]) > 0),"" + errorMsg0
        for k2d0 in key2del0:
            del remappable[k2d0]
        # find the puncts
        # this one's kind of wonky, but basically we 
        # iterate once more, find all puncts with indicies between 
        # the max and min of the conjunction in question, prefix
        # it to the conjuct's key in remappable, then edit the dict.
        for deps2 in sdfi0:
            if deps2[0] == 'punct' and deps2[3] in [',', ';']:
                goAhead = True
            # this should handle weird X and Y and Z situations
            elif deps2[0] == 'cc' and deps2[3] + "/" + deps2[4] not in remappable:
                goAhead = True
            else:
                goAhead = False
            if goAhead == True:
                key2del = []
                # these should be tuples
                key2add = []
                for conj0 in remappable:
                    # should we only have 2 things being conjoined, we can just forget the puncts
                    # btw, this took us down from 68 errors, to 9
                    if len(remappable[conj0]) == 2:
                        pass
                    elif len(remappable[conj0]) > 2:
                        ranges = []
                        for tokens0 in remappable[conj0]:
                            ranges.append(int(tokens0.split('/')[1]))
                        #~ print(ranges, deps2)
                        # added auxiliary check to make sure max([]) doesn't error out
                        if ranges != []:
                            if int(deps2[4]) < max(ranges) and int(deps2[4]) > min(ranges):
                                # we have found an another conjunct in the form of ','
                                # add as prefix, then we'll sort it out during remapping
                                newConj0 = deps2[3] + '/' + deps2[4] + '--' + conj0
                                key2add.append((newConj0, remappable[conj0]))
                                # we can't delete keys as we're iterating through them
                                key2del.append(conj0)
                # first add then delete
                for k2a in key2add:
                    remappable[k2a[0]] = k2a[1]
                # removed unneeded keys
                for k2d in key2del:
                    del remappable[k2d]
        remappable = rm.semiColonCheck(remappable)
        print("remappable", remappable)
        # just a check to see how binarization might fare, then binarize
        for conjuncts0 in remappable:
            print('\t',conjuncts0, remappable[conjuncts0])
            lenCC = len(conjuncts0.split('--'))
            lenConj = len(remappable[conjuncts0])
            diff = lenCC - lenConj
            if diff in [0, -1]:
                if rm.debug == True:
                    print("\tOK: lenCC", lenCC, "lenConj", lenConj, "and the diff", diff)
            elif diff not in [0, -1]:
                errorArray = ["\tNot OK: lenCC", str(lenCC), "lenConj", str(lenConj), "and the diff", str(diff)]
                errorMsg = ' '.join(errorArray)
                # We will sort this out later, during binarization
                print(errorMsg)
            # Now that we have appropriately grouped the conjunctions, let's hope binarize still works
            # First, we'll need to make tuples:
            # everything in the form of (##, string)
            conjTuple = []
            # just an array of strings
            conjuncts = []
            for newhead in conjuncts0.split('--'):
                headString = newhead.split('/')[0]
                headIndex = newhead.split('/')[1]
                conjTuple.append((int(headIndex), headString))
                conjuncts.append(headString)
            for oldheads in remappable[conjuncts0]:
                oldString = oldheads.split('/')[0]
                oldIndex = oldheads.split('/')[1]
                #~ print("oldString", oldString, "oldIndex", oldIndex)
                # Removing apostrophes -- not sure where they're coming from
                conjTuple.append((int(oldIndex.strip("'")), oldString))
            conjTuple = sorted(set(conjTuple))
            if rm.debug == True:
                print("Before cleaning Tuples:", conjTuple)
            # remove extra cstring (oxford commas, etc.):
            conjTuple = rm.cleanTuple(conjTuple, conjuncts)
            if rm.debug == True:
                print("After cleaning Tuples:", conjTuple)
            binarized = rm.binarize(conjTuple, conjuncts, [])
            for bi in binarized:
                # untuple
                sdfi0.append([bi[0], bi[1][1], bi[1][0], bi[2][1], bi[2][0]])
                almostString = (placeID0, bi[0], bi[1][1], str(bi[1][0]), bi[2][1], str(bi[2][0]))
                outString = ' '.join(almostString) + '\n'
                rm.conjOut.write(outString)
                if rm.debug == True:
                    print("\tBINARIZED:", bi)
                    print("\toutString:", outString)
        return sdfi0
    
    def cleanTuple(rm, conjTupes1, cstrings1):
        """
        Used by conj remap (so not used anymore) to clean tuples of duplicates
        :param conjTupes1:
        :param cstrings1:
        :return:
        """
        newtupes = []
        # The goal here is to remove extraneous commas and other conjunctions
        for n in range(len(conjTupes1)):
            if n + 1 != len(conjTupes1):
                # "x , y..."
                if conjTupes1[n][1] not in cstrings1:
                    newtupes.append(conjTupes1[n])
                # ", , y"
                elif conjTupes1[n][1] in cstrings1:
                    if conjTupes1[n+1][1] in cstrings1:
                        pass
                        # , y
                    elif conjTupes1[n+1][1] not in cstrings1:
                        newtupes.append(conjTupes1[n])
            elif n + 1 == len(conjTupes1):
                #this should be the last stage
                if conjTupes1[n][1] not in cstrings1:
                    newtupes.append(conjTupes1[n])
                elif conjTupes1[n][1] in cstrings1:
                    pass
        if rm.debug == True:
            print("\tbefore CleanTuple\n\t\t", conjTupes1)
            print("\tafter cleanTuple\n\t\t", newtupes)
        return newtupes
    
    def semiColonCheck(rm, conjDict):
        """
        Used by conjremap (so no used anything) to make sure coordination
        didn't use a ; instead of a ,
        :param conjDict:
        :return:
        """
        for each in conjDict:
            if rm.debug == True:
                print("\tBefore", each, conjDict[each])
        # if we find a semiColon AND a comma in a coordinated construction, remove the commas
        key2del1 = []
        # these are tuples
        key2add1 = []
        for cD in conjDict:
            semiColonFlag = False
            conjuncts1 = cD.split('--')
            if rm.debug == True:
                print("\tconjuncts1", conjuncts1)
            # we don't care if the length is less than 1, there should be no punct
            if len(conjuncts1) > 1:
                for cd0 in conjuncts1:
                    if rm.debug == True:
                        print("\tcd0.split('/')", cd0.split('/'))
                    if cd0.split('/')[0] == ';':
                        semiColonFlag = True
                newKeyArr = []
                if semiColonFlag == True:
                    if rm.debug == True:
                        print("\tsemiColonFlag is True")
                    key2del1.append(cD)
                    for cd1 in conjuncts1:
                        if cd1.split('/')[0] != ',':
                            if rm.debug == True:
                                print("\tcd1.split('/')", cd0.split('/'))
                            newKeyArr.append(cd1)
                    newKey = '--'.join(newKeyArr)
                    key2add1.append((newKey, conjDict[cD]))
                else:
                    if rm.debug == True:
                        print("\tsemiColonFlag is False")
        # first add then delete
        for k2a1 in key2add1:
            conjDict[k2a1[0]] = k2a1[1]
        # removed unneeded keys
        for k2d1 in key2del1:
            del conjDict[k2d1]
        for each in conjDict:
            if rm.debug == True:
                print("\tAfter", each, conjDict[each])
        return conjDict
                    
    def binarize(rm, conjTupes, cstrings, bincon):
        """
        Used by conj remap (so not used anymore) to binarize coordination in SDC
        :param conjTupes:
        :param cstrings:
        :param bincon:
        :return:
        """
        # new binarize function -- should be simpler
        if len(conjTupes) == 3:
            # exception error handling case for mis-parses 'and X Y'
            #~ if conjTupes[0][1] in cstrings:
                #~ c1 = ("conj1", conjTupes[0], conjTupes[1])
                #~ c2 = ("conj2", conjTupes[0], conjTupes[2])
                #~ conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0)
                #~ bincon.append(c1); bincon.append(c2)
                #~ rm.binarize(conjTupes,cstrings, bincon)
            # normal case X and Y
            #~ elif conjTupes[2][1] not in cstrings:
            if conjTupes[2][1] not in cstrings:
                c1 = ("conj1", conjTupes[1], conjTupes[0])
                c2 = ("conj2", conjTupes[1], conjTupes[2])
                #~ sub1 = ("sub", conjTupes[1], conjTupes[0])
                #~ sub2 = ("sub", conjTupes[1], conjTupes[2])
                conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0)
                bincon.append(c1); bincon.append(c2)
                #~ bincon.append(sub1); bincon.append(sub2)
                rm.binarize(conjTupes,cstrings, bincon)
            else:
                print("    ERROR length was exactly 3, but the last element was in cstrings")
                print("    binarize -- conjTupes: ", conjTupes)
        elif len(conjTupes) == 4:
            if conjTupes[1][1] in cstrings and conjTupes[2][1] not in cstrings:
                # maybe hacky, but if we have an X Y and Z, chances are 
                # we actually have just Y and Z -- and earlier there's 
                # probably a X and Y
                c1 = ("conj1", conjTupes[1], conjTupes[0])
                c2 = ("conj2", conjTupes[1], conjTupes[2])
                #~ sub1 = ("sub", conjTupes[0], conjTupes[1])
                #~ sub2 = ("sub", conjTupes[3], conjTupes[1])
                conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0)
                bincon.append(c1); bincon.append(c2)
                #~ bincon.append(sub1); bincon.append(sub2)
                rm.binarize(conjTupes,cstrings,bincon)
            elif conjTupes[2][1] in cstrings and conjTupes[1][1] not in cstrings:
                # maybe hacky, but if we have an X Y and Z, chances are 
                # we actually have just Y and Z -- and earlier there's 
                # probably a X and Y
                c1 = ("conj1", conjTupes[2], conjTupes[1])
                c2 = ("conj2", conjTupes[2], conjTupes[3])
                #~ sub1 = ("sub", conjTupes[0], conjTupes[1])
                #~ sub2 = ("sub", conjTupes[3], conjTupes[1])
                conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0)
                bincon.append(c1); bincon.append(c2)
                #~ bincon.append(sub1); bincon.append(sub2)
                rm.binarize(conjTupes,cstrings,bincon)
            elif conjTupes[2][1] in cstrings and conjTupes[1][1] in cstrings:
                # special, just in case, case for oxford commas
                c1 = ("conj1", conjTupes[2], conjTupes[1])
                c2 = ("conj2", conjTupes[2], conjTupes[3])
                #~ sub1 = ("sub", conjTupes[0], conjTupes[1])
                #~ sub2 = ("sub", conjTupes[3], conjTupes[1])
                conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0)
                bincon.append(c1); bincon.append(c2)
                #~ bincon.append(sub1); bincon.append(sub2)
                rm.binarize(conjTupes,cstrings,bincon)
        elif len(conjTupes) > 3:
            # multiple conj case
            # for weird "difficult, if not impossible, construction
            if conjTupes[1][1] in cstrings and conjTupes[2][1] in cstrings and len(conjTupes) >= 4:
                c1 = ("conj1", conjTupes[2], conjTupes[0])
                c2 = ("conj2", conjTupes[2], conjTupes[3])
                #~ sub1 = ("sub", conjTupes[2], conjTupes[0])
                #~ sub2 = ("sub", conjTupes[2], conjTupes[3])
                conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0)
                bincon.append(c1); bincon.append(c2)
                #~ bincon.append(sub1); bincon.append(sub2)
                rm.binarize(conjTupes,cstrings,bincon)
            # multiple with oxford commas -- X, Y, and Z
            #~ elif conjTupes[1][1] in cstrings and conjTupes[3][1] in cstrings:
                #~ c1 = ("conj1", conjTupes[1], conjTupes[0])
                #~ c2 = ("conj2", conjTupes[1], conjTupes[2])
                #~ conjTupes.pop(0); conjTupes.pop(0)
                #~ bincon.append(c1); bincon.append(c2)
                #~ rm.binarize(conjTupes,cstrings,bincon)
            #final normal x , 3 and...
            elif conjTupes[3][1] in cstrings:
                c1 = ("conj1", conjTupes[1], conjTupes[0])
                c2 = ("conj2", conjTupes[1], conjTupes[3])
                #~ sub1 = ("sub", conjTupes[0], conjTupes[1])
                #~ sub2 = ("sub", conjTupes[3], conjTupes[1])
                conjTupes.pop(0); conjTupes.pop(0)
                bincon.append(c1); bincon.append(c2)
                #~ bincon.append(sub1); bincon.append(sub2)
                rm.binarize(conjTupes,cstrings,bincon)
            else:
                print("    ERROR length was 4 or more, but the 4th element was not in cstrings", cstrings, conjTupes)
                print("    binarize -- conjTupes: ", conjTupes, "len(conjTupes)", len(conjTupes))
                # return "multiple"
        elif len(conjTupes) == 0:
            print("    Okay, we found the end")
            #~ print("    binarize -- conjTupes: ", conjTupes)
        else:
            print("    Error with conjTupes ", conjTupes)
        return bincon

    def otherRels(rm, depblock, dep, ccg):
        """
        Find other rels related to the one in question and output those as features
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

    # TODO depreciate this
    def oldbinarize(rm, conjTupes, cstrings, bincon):
        """
        oldbinarization function
        :param conjTupes:
        :param cstrings:
        :param bincon:
        :return:
        """
        if len(conjTupes) == 5 and conjTupes[1][1] in cstrings and conjTupes[2][1] in cstrings and conjTupes[3][1] in cstrings:
            c1 = ("conj1", conjTupes[3], conjTupes[0])
            c2 = ("conj2", conjTupes[3], conjTupes[4])
            conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0)
            bincon.append(c1); bincon.append(c2)
            rm.binarize(conjTupes, cstrings, bincon)
        elif len(conjTupes) == 4:
            # added sub relations for subordination 
            # removed sub -- here's not the place
            # oxford comma or coordinated clause nncase 
            if conjTupes[1][1] in cstrings and conjTupes[2][1] in cstrings:
                c1 = ("conj1", conjTupes[2], conjTupes[0])
                c2 = ("conj2", conjTupes[2], conjTupes[3])
                conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0)
                bincon.append(c1); bincon.append(c2)
                rm.binarize(conjTupes, cstrings, bincon)
            # for phrasal ', X and Y':
            elif conjTupes[2][1] in cstrings and conjTupes[0][1] in cstrings:
                c1 = ("conj1", conjTupes[2], conjTupes[1])
                c2 = ("conj2", conjTupes[2], conjTupes[3])
                #~ sub1 = ("sub", conjTupes[1], conjTupes[2])
                #~ sub2 = ("sub", conjTupes[3], conjTupes[2])
                conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0), 
                bincon.append(c1); bincon.append(c2)
                #~ bincon.append(sub1); bincon.append(sub2)
                rm.binarize(conjTupes,cstrings,bincon)
            # for titles 'Grace and Co.,' X and Y,
            elif conjTupes[1][1] in cstrings and conjTupes[3][1] in cstrings:
                c1 = ("conj1", conjTupes[1], conjTupes[0])
                c2 = ("conj2", conjTupes[1], conjTupes[2])
                #~ sub1 = ("sub", conjTupes[0], conjTupes[1])
                #~ sub2 = ("sub", conjTupes[2], conjTupes[1])
                conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0), 
                bincon.append(c1); bincon.append(c2)
                #~ bincon.append(sub1); bincon.append(sub2)
                rm.binarize(conjTupes,cstrings,bincon)
            else:
                print("    length was 4, but the two middle elements were not in cstrings, nor were the first and third")
                print("    binarize -- conjTupes: ", conjTupes)
        elif len(conjTupes) == 3:
            # normal case X and Y
            if conjTupes[2][1] not in cstrings:
                c1 = ("conj1", conjTupes[1], conjTupes[0])
                c2 = ("conj2", conjTupes[1], conjTupes[2])
                #~ sub1 = ("sub", conjTupes[1], conjTupes[0])
                #~ sub2 = ("sub", conjTupes[1], conjTupes[2])
                conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0)
                bincon.append(c1); bincon.append(c2)
                #~ bincon.append(sub1); bincon.append(sub2)
                rm.binarize(conjTupes,cstrings, bincon)
            else:
                print("    length was exactly 3, but the last element was in cstrings")
                print("    binarize -- conjTupes: ", conjTupes)
        elif len(conjTupes) > 3:
            # multiple conj case
            # for weird "difficult, if not impossible, construction
            if conjTupes[1][1] in cstrings and conjTupes[2][1] in cstrings and len(conjTupes) >= 4:
                c1 = ("conj1", conjTupes[2], conjTupes[0])
                c2 = ("conj2", conjTupes[2], conjTupes[3])
                #~ sub1 = ("sub", conjTupes[2], conjTupes[0])
                #~ sub2 = ("sub", conjTupes[2], conjTupes[3])
                conjTupes.pop(0); conjTupes.pop(0); conjTupes.pop(0)
                bincon.append(c1); bincon.append(c2)
                #~ bincon.append(sub1); bincon.append(sub2)
                rm.binarize(conjTupes,cstrings,bincon)
            # multiple with oxford commas -- X, Y, and Z
            #~ elif conjTupes[1][1] in cstrings and conjTupes[3][1] in cstrings:
                #~ c1 = ("conj1", conjTupes[1], conjTupes[0])
                #~ c2 = ("conj2", conjTupes[1], conjTupes[2])
                #~ conjTupes.pop(0); conjTupes.pop(0)
                #~ bincon.append(c1); bincon.append(c2)
                #~ rm.binarize(conjTupes,cstrings,bincon)
            #final normal x , 3 and...
            elif conjTupes[3][1] in cstrings:
                c1 = ("conj1", conjTupes[1], conjTupes[0])
                c2 = ("conj2", conjTupes[1], conjTupes[3])
                #~ sub1 = ("sub", conjTupes[0], conjTupes[1])
                #~ sub2 = ("sub", conjTupes[3], conjTupes[1])
                conjTupes.pop(0); conjTupes.pop(0)
                bincon.append(c1); bincon.append(c2)
                #~ bincon.append(sub1); bincon.append(sub2)
                rm.binarize(conjTupes,cstrings,bincon)
            else:
                print("    length was 4 or more, but the 4th element was not in cstrings", cstrings, conjTupes)
                print("    binarize -- conjTupes: ", conjTupes, "len(conjTupes)", len(conjTupes))
                # return "multiple"
        elif len(conjTupes) == 0:
            print("    Okay, we found the end")
            #~ print("    binarize -- conjTupes: ", conjTupes)
        else:
            print("    Error with conjTupes ", conjTupes)
        return bincon
                
                
# input = PARG, AUTO, DEPS
if __name__ == '__main__':
    if len(sys.argv) < 5:
        runerror = "This program requires four arguments:" \
                   "\n\t1) an output option (-c for CoNLL, -d for Stanford Dependency, and -n for a tradition dependency list" \
                   "\n\t2) a PARG file" \
                   "\n\t3) an AUTO file" \
                   "\n\t4) an Stanford dependency output file renamed" \
                   "\nexample:    python3 rempay.py -n wsj_0001.parg wsj_0001.auto wsj_0111.mrg.dep.withid" \
                   "\nAdditionally, megam and morpha should be located in the same directory as this program is invoked from."
        print(runerror)
    elif len(sys.argv) >= 5:
        r = remap()
        if len(sys.argv) == 6:
            r.actualstart(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        elif len(sys.argv) == 5:
            fauxdebug = "no"
            r.actualstart(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], fauxdebug)
        else:
            sys.exit("The final argument must be nothing or '--debug'")
        r.iterate()
        #~ r.checkoutput()
