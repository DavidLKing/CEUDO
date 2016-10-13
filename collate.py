import sys
import re
import os
import subprocess


class collate():
    def __init__(co):
        pass

    def actualstart(co, outform, sdFile, maxent, newconj, auto, debug, rev):
        if outform not in ['-n', '-c', '-d']:
            formaterror = "output formats can only be:\n\t-c -- for CoNLL 2008 formatting\n\t-n -- for simple tab delimited dependency output\n\t-d -- for Stanford Dependency output"
        else:
            co.of = outform
        # get basename:
        co.basename = os.path.splitext(sdFile)[0]
        s = open(sdFile, 'r')
        m = open(maxent, 'r')
        n = open(newconj, 'r')
        a = open(auto, 'r')
        c = open(auto.replace('auto', 'parg'), 'r')
        co.sdfi = co.other2dict(s, 'd')
        co.auto = co.other2dict(a, 'a')
        co.maxent = co.collated2dict(m)
        co.newconj = co.collated2dict(n)
        co.ccgs = co.other2dict(c, 'p')
        if debug == 'no':
            co.debug = False
        elif debug == '--debug':
            co.debug = True
            print('DEBUGGING IS TURNED ON')
        if rev == 'yes':
            co.rev = True
        else:
            co.rev = False
        if co.debug == True:
            print("copula/aux reversal is:", co.rev)
            # co.stats = open('stats.txt', 'a')

    def collated2dict(co, lines):
        dict0 = {}
        for l in lines:
            lArray = l.split()
            iD = lArray.pop(0)
            try:
                dict0[iD].append(lArray)
            except:
                dict0[iD] = []
                dict0[iD].append(lArray)
        return dict0

    def other2dict(co, depPargAuto, dpa):
        # dpa is either 'd', 'p', or 'a' depending on whether
        # depPargAuto is an SD, a CCG Parg, or a CCG Auto file
        dict1 = {}
        # empty variable to write over
        placeID = ''
        if dpa == 'a':
            for line2 in depPargAuto:
                # print("other2dict, line2: ", line2)
                check1 = re.match('ID=(.*) PARSER=GOLD NUMPARSE=1', line2)
                if check1 != None:
                    placeID = check1.group().replace('ID=', '').replace('PARSER=GOLD NUMPARSE=1', '').strip()
                    # print("other2dict, first case, dpa = a, PlaceID: ", placeID)
                    dict1[placeID] = {}
                else:
                    # dict1 = co.lex2dict(depPargAuto)
                    # print("other2dict, second case, dpa = a, PlaceID: ", placeID)
                    dict1[placeID] = co.lexbuilder(line2)
        elif dpa == 'p' or dpa == 'd':
            for line0 in depPargAuto:
                # print("other2dict, p or d, line0: ", line0)
                check0 = re.match('<s id="(.*)">', line0)
                if check0 != None:
                    placeID = check0.group(0).replace('<s id="', '').replace('">', '')
                    assert (check0 not in dict1), "other2dict error: index already present in dictionary!"
                    dict1[placeID] = []
                elif check0 == None:
                    errormsg = "Duplicate line entries for " + line0 + "in" + str(dict1)
                    # print(line0)
                    if line0 in dict1:
                        print(errormsg)
                    if dpa == 'd':
                        dict1[placeID].append(co.dep2split(line0.strip()).split())
                    elif dpa == 'p':
                        dict1[placeID].append(line0.strip().split())
                else:
                    print("I don't know what happened: ", line0, check0)
        return dict1

    def dep2split(co, depstring):
        # changes rel(word-#, word-#) format to rel word # word #, which is
        # easier for the split() method
        # This used to be two lines:
        # depsplit = depstring.replace('(',' ').replace(')',' ').replace('-', ' ').replace(',', ' ')
        # but we were splitting hypenated words and punct(,-# type entries
        splat = depstring.replace('(', ' ').replace(')', '').split()
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
                print("ERROR!!! Splitting the entry by hyphens has only generated on category [first split]", splat)
            if len(splat[2].split('-')) == 2:
                word2 = splat[2].split('-')[0]
            elif len(splat[2]) > 2:
                word2 = '-'.join(splat[2].split('-')[0:-1])
            elif len(splat[2].split('-')) < 2:
                print("ERROR!!! Splitting the entry by hyphens has only generated on category [second split]", splat)
            protoReady = (splat[0], word1, ind1, word2, ind2)
            depsplit = ' '.join(protoReady)
            # print(depsplit.split())
            return depsplit
        else:
            # print("Ignoring", depstring, splat)
            return 'ignore'

    def checkoutput(co):
        for iD in co.sdfi:
            # print(iD + 'test')
            for deps in co.sdfi[iD]:
                print(iD, deps)
                # if iD in co.maxent:
                # print(co.maxent[iD])
                # for pred in co.maxent[iD]:
                # print(pred)
                # else:
                # print(iD, "not in co.maxent")
                # if iD in co.newconj:
                # print(co.newconj[iD])
                # for insert in co.newconj[iD]:
                # print(insert)
                # else:
                # print(iD, "not in co.newconj")
                # print(iD + 'test')
                # for each in co.maxent:
                # print(each, co.maxent[each])
                # print(each + 'test')

    def removeRelwDep(co, deps, maxentries, rel):
        """
        super useful function.
        :param deps: dependencies from SDC
        :param maxentries: overgenerated list of predictions to be pruned
        :param rel: relation of interest to remove
        :return:
        """
        checkagainst = []
        returnable = []
        for d in deps:
            if d[0] == rel:
                checkagainst.append((d[3], d[4]))
        if co.debug == True:
            print("\t\tbefore pruning maxent entries:", maxentries)
            print("\t\tchecking against:", checkagainst)
        for maxes in maxentries:
            if len(maxes) == 5:
                mhead = maxes[1]
                mhindex = maxes[2]
                mdep = maxes[3]
                mdindex = maxes[4]
                # both heads and deps?
                if (mhead, mhindex) in checkagainst:
                    if co.debug == True:
                        print("\t\tRemoving:", rel, maxes)
                        # maxentries.pop(maxentries.index(maxes))
                elif (mdep, mdindex) in checkagainst:
                    if co.debug == True:
                        print("\t\tRemoving:", rel, maxes)
                        # maxentries.pop(maxentries.index(maxes))
                else:
                    if co.debug == True:
                        print("\t\tno match -- should this have been caught?", rel, maxes)
                    returnable.append(maxes)
        if co.debug == True:
            print("\t\tafter pruning maxent entries for", rel, ":", returnable)
        return returnable

    def trustSD(co, sentArray, maxentArray):
        # the goal here is to prune to maxent predictions of anything that has a head-depentant match to what already exists in the SDs
        # maxent head = 0, head index = 1, depend. = 2, dep index = 3
        # SDs rel = 0, head = 1, head index = 2, dependant = 3, dep index = 4, headPOS = 5, dep POS = 6
        # the only exception is if we find a dep( rel.
        if co.debug == True:
            print("\tCurrent maxents:", len(maxentArray))
        maxReturn = []
        for mA in maxentArray:
            addCheck = True
            for sA in sentArray:
                if len(mA) > 4 and len(sA) > 4:
                    if sA[0] == 'dep' and \
                                    mA[0] == sA[1] and \
                                    mA[1] == sA[2] and \
                                    mA[2] == sA[3] and \
                                    mA[3] == sA[4]:
                        relDir = mA[4].split("_")
                        assert (len(relDir) == 2)
                        mA[4] = "_".join([relDir[0], 'normal'])
                        if co.debug == True:
                            print("\t\tKeeping with dep direction", "sA", sA, "mA", mA, addCheck)
                        maxReturn.append(mA)
                    elif mA[0] == sA[1] and \
                                    mA[1] == sA[2] and \
                                    mA[2] == sA[3] and \
                                    mA[3] == sA[4]:
                        addCheck = False
                        if co.debug == True:
                            print("\t\tRemoving", "sA", sA, "mA", mA, addCheck)
                            # else:
                            # if co.debug == True:
                            # print("\t\tKeeping", "sA", sA, "mA", mA, addCheck)
            if addCheck == True:
                maxReturn.append(mA)
        if co.debug == True:
            print("\tAfter trustSD funct, len of maxents:", len(maxReturn))
        return maxReturn

    def checkArgs(co, deps, iD):
        """
        check arguments and convert if needed
        :param array: final out array
        :param iD: wsj_ format
        :return: array in the same format as the input
        """
        if co.debug:
            print("### BEGINNING ARG CHECKS WITH checkArg()###", iD)
        for dep in deps:
            if dep[0] in ['nsubj', 'nsubjpass', 'dobj', 'iobj', 'obj', 'obj2']:
                if co.debug:
                    print("arg", dep)
                pargs, verb, arg = co.findRelatedCCGs(iD, dep)
                assert(len(verb) == 1); assert(len(arg) == 1)
                # match verb and see if subjects match and what what the arg nums are
                # this is currently only working for nsubj errors
                # TODO expand to iobj/dobj/obj/obj2 > nsubj errors
                # TODO not having indicies is causing this to error out
                check = False
                for ccg in pargs:
                    # does the CCG functor and DEP governor match and is it an nsubj
                    if dep[1] == ccg[5] and \
                       dep[0] == 'nsubj':
                        # is either the index 1 and the dependencts don't match
                        # or the index not 1 and the dependents match?
                        if (dep[3] == ccg[4] and ccg[3] != '1') or \
                           (dep[3] != ccg[4] and ccg[3] == '1'):
                            check = True
                            if co.debug:
                                print("\tccg", ccg)
                if check == True:
                    if co.debug == True:
                        print("\tpossibly change this one!")
                    dep[0] = 'obj'
            if co.debug:
                print("### FINISHED ARG CHECKS WITH checkArg()###")
        return deps

    def findRelatedCCGs(co, iD, relArray):
        """
        find and return CCGs related to the relation in question
        :param iD: wsj_
        :param relArray: [rel, word1, index1, word2, index2] format
        :return: set of CCGs
        """
        relatedParg = []
        argAuto = []
        verbAuto = []
        # print("\tauto", co.auto[iD][relArray[1]])
        verbAuto.append(co.auto[iD][relArray[1]])
        # print("\tauto", co.auto[iD][relArray[3]])
        argAuto.append(co.auto[iD][relArray[3]])
        for ccg in co.ccgs[iD]:
            if len(ccg) > 1:
                if ccg[4] == relArray[3] or ccg[5] == relArray[1]:
                    relatedParg.append(ccg)
        return relatedParg, verbAuto, argAuto

    def iterate(co):
        # add maxents, if newconjes exist, remap all deps to conj head, remove cc and conj, check for gabs
        # this should sort things
        # for iD in od.items()
        order = {}
        keys = []
        for iD in co.auto:
            # print("ID =", iD)
            # print("split =", iD.split('.'))
            afterDot = int(iD.split('.')[1])
            assert (afterDot not in order)
            assert (afterDot not in keys)
            order[afterDot] = iD
            keys.append(afterDot)
        for k in sorted(set(keys)):
            iD = order[k]
            # clean this
            tempmax = []
            finalout = []
            # add maxent predictions
            if iD in co.maxent:
                co.maxent[iD] = co.trustSD(co.sdfi[iD], co.maxent[iD])
                for newdep in co.maxent[iD]:
                    assert (len(newdep) == 5), newdep
                    reldir = newdep[4].split('_')
                    rel = reldir[0]
                    dire = reldir[1]
                    mhead = newdep[0]
                    mhindex = newdep[1]
                    mdep = newdep[2]
                    mdindex = newdep[3]
                    if dire == 'normal':
                        add = [rel, mhead, mhindex, mdep, mdindex]  # , 'max1']
                    elif dire == 'reverse':
                        add = [rel, mdep, mdindex, mhead, mhindex]  # , 'max2']
                    else:
                        sys.exit("dire is neither normal or revers")
                    if co.debug == True:
                        print("\tadding maxent prediction", add)
                    tempmax.append(add)
            # clean maxes:
            ### revisit this. This is removing certain auxpass' we want. Try without.
            if co.debug == True:
                print("Checking for aux")
            # if iD in so.sdfi:
            tempmax = co.removeRelwDep(co.sdfi[iD], tempmax, 'aux')
            if co.debug == True:
                print("Checking for auxpass")
            tempmax = co.removeRelwDep(co.sdfi[iD], tempmax, 'auxpass')
            if co.debug == True:
                print("Checking for cop")
            tempmax = co.removeRelwDep(co.sdfi[iD], tempmax, 'cop')
            if co.debug == True:
                print("Checking for appos")
            tempmax = co.removeRelwDep(co.sdfi[iD], tempmax, 'appos')
            if co.debug == True:
                print("Length after scanning for rels of interest", len(tempmax))
            for add in tempmax:
                co.sdfi[iD].append(add)
            # add new conj mapping -- we're not binarizing conjunction
            # if iD in co.newconj:
            #     for nc in co.newconj[iD]:
            #         co.sdfi[iD].append(nc)
            #         if co.debug == True:
            #             print("\tadding new conj", nc)
            # check to make sure everything was added
            # if iD in co.newconj:
            #     for nc in co.newconj[iD]:
            #         if nc not in co.sdfi[iD]:
            #             assert(nc in co.sdfi[iD])
            # remapping conj1/2 head and deps
            # first build conjheads and conjdeps
            conjuncts = set()
            conjoined = set()
            for deps in co.sdfi[iD]:
                if deps[0] in ['conj1', 'conj2']:
                    conjuncts.add(deps[1])
                    conjoined.add(deps[3])
                elif deps[0] == 'cc':
                    conjuncts.add(deps[3])
                    conjoined.add(deps[1])
            # if co.debug == True:
            #     print("\tConjuncts fed to remapdepargs", conjuncts, conjoined)
                # if co.debug == True:
                #     print("Starting remapdepargs function")
                # bigDels = []
                # for deps in co.sdfi[iD]:
                #     if deps[0] == 'conj1' or deps[0] == 'conj2':
                #         if co.debug == True:
                #             print("\tfound conj1 or conj2, should be remapping", deps)
                #         removes, changed = co.remapdepargs(co.sdfi[iD], deps, iD, conjuncts, conjoined)
                #         for r in removes:
                #             r = co.getLex(r, co.auto, iD)
                #             if r not in bigDels:
                #                 bigDels.append(r)
                #                 if co.debug == True:
                #                     print("\tcon1/2 check removes")
                #         for c in changed:
                #             if co.debug == True:
                #                 print('\tadded from conj1/2 check', c)
                #             c = co.getLex(c, co.auto, iD)
                #             finalout.append(c)
                #         deps = co.getLex(deps, co.auto, iD)
                #         finalout.append(deps)
                #     elif deps[0] == 'ignore':
                #         if co.debug == True:
                #             print("\tconj, ignore, or cc found -- removing:", deps)
                #     else:
                #         deps = co.getLex(deps, co.auto, iD)
                #         finalout.append(deps)
                # quick clean
                # for bD in bigDels:
                #     while bD in finalout:
                #         if co.debug == True:
                #                 print('\tremoved from conj1/2 check', r)
                #         finalout.remove(bD)
                #     while bD in co.sdfi[iD]:
                #         if co.debug == True:
                #             print('\tremoved from conj1/2 check in sdfi', r)
                #         co.sdfi[iD].remove(bD)
                #     assert(bD not in finalout)
                ### XXX Somehow conj1s keep getting removed, so we're going
                ### re-add them if their missing -- hacky TODO FIX:
                # add new conj mapping
                # if iD in co.newconj:
                # for nc in co.newconj[iD]:
                # if nc not in finalout:
                # finalout.append(co.getLex(nc, co.auto, iD))
                # if co.debug == True:
                # print("\tadding new conj since something ate it", nc)
            # HERE IS WHERE THE POST PROCESSING BEGINS
            for deps in co.sdfi[iD]:
                # gets rid of 'ignores'
                if len(deps) > 1:
                    newdep = co.getLex(deps, co.auto, iD)
                    finalout.append(newdep)
            finalout = co.postProcess(finalout, iD)
            # probably unnecessary
            ordered = co.sortThem(finalout)
            # for each in ordered:
            # print(iD, each, ordered[each])
            # I don't think these need to be sorted
            ordered, isGap = co.checkForGaps(ordered, iD)
            if isGap == False or co.debug == True:
                if co.of == '-d':
                    newiD = '<s id="' + iD + '">'
                    print(newiD)
                # conll gets no IDs -- breaks induction
                # normal output just get wsj_####.## format
                elif co.of in ['-n', '-c']:
                    print(iD)
                for dep3 in sorted(ordered):
                    # print(len(ordered[dep3]))
                    # print(ordered[dep3])
                    if len(ordered[dep3]) == 1:
                        for individ0 in ordered[dep3]:
                            co.ready4Tabs(individ0, co.of)
                            pass
                    elif len(ordered[dep3]) > 1:
                        if co.of == '-d':
                            for d in ordered[dep3]:
                                co.ready4Tabs(d, co.of)
                        else:
                            initial = ordered[dep3].pop(0)
                            others = ''
                            for individ1 in ordered[dep3]:
                                # print("ordered[dep3]", ordered[dep3], "individ1", individ1)
                                if others == '':
                                    others = others + individ1[0] + ',' + individ1[2]
                                else:
                                    others = others + ';' + individ1[0] + ',' + individ1[2]
                            initial.append(others)
                            co.ready4Tabs(initial, co.of)
                if co.of == '-d':
                    print("</s>")
                else:
                    print()

    def checkForConj(co, sentArray, iD, depArray):
        """
        if there is any coordination after making a new rel, propegate it to the new rel
        :param sentArray: sentence
        :param iD: iD in wsj_ format
        :param depArray: the dependency in question
        :return: array of new relation if the conj matches
        """
        matches = []
        for conj in sentArray:
            newDep = []
            if len(conj) > 1 and conj[0] == 'conj':
                # conj(x, Y) and acl:relcl(X, Z), make acl(Y, Z)
                if conj[1] == depArray[1] and conj[2] == depArray[2]:
                    newDep = [depArray[0], conj[1], conj[2], depArray[3], depArray[4], conj[5], depArray[6]]
                    # conj(x, Y) and acl:relcl(Y, Z), make acl(X, Z)
                if conj[1] == depArray[3] and conj[2] == depArray[4]:
                    newDep = [depArray[0], conj[3], conj[4], depArray[3], depArray[4]], conj[6], depArray[6]
                # conj(X, Y) and nsubj(Z, X), make nsubj(Z, Y)
                elif conj[1] == depArray[3] and conj[2] == depArray[4]:
                    newDep = [depArray[0], depArray[1], depArray[2], conj[3], conj[4], depArray[5], conj[6]]
                # conj(X, Y) and nsubj(Z, Y), make nsubj(Z, X)
                elif conj[3] == depArray[3] and conj[4] == depArray[4]:
                    newDep = [depArray[0], depArray[1], depArray[2], conj[1], conj[2], depArray[5], conj[5]]
                if newDep not in matches and newDep != []:
                    matches.append(newDep)
        return matches

    def postProcess(co, sentArray, iD):
        """
        This function adds the final maxent predictions. There is still some
        legacy code from where it used to binarize conjunction.
        :param sentArray: array as imported from SDC file
        :param iD:  CCG like iD for keeping disperate information in sync
        :return: a version of the original array supplemented with new info
        """
        # relQues = ['what', 'where', 'who', 'when', 'what', 'which', 'how', 'that', 'What', 'Where', 'Who', 'When', 'What', 'How', 'That']
        outArray = []
        # remember dependency arrays are of length 7
        for dependency in sentArray:
            if dependency[0] == 'dep':
                delete = False
                # print("HERE'S THE ID", iD, iD in co.maxent)
                if iD in co.maxent:
                    for m in co.maxent[iD]:
                        reldir = m[4].split('_')
                        rel = reldir[0]
                        dire = reldir[1]
                        mhead = m[0]
                        mhindex = m[1]
                        mdep = m[2]
                        mdindex = m[3]
                        if dependency[1] == mhead and dependency[2] == mhindex and \
                                        dependency[3] == mdep and dependency[4] == mdindex:
                            if co.debug == True:
                                print("removing dep", dependency, m)
                            delete = True
                        elif dependency[3] == mhead and dependency[4] == mhindex and \
                                        dependency[1] == mdep and dependency[2] == mdindex:
                            if co.debug == True:
                                print("removing dep", dependency, m)
                            delete = True
                if delete == False:
                    if co.debug == True:
                        print("keeping dep", dependency)
                    outArray.append(dependency)
            elif dependency[0] == 'csubj':
                # if csubj is a relative, remap for
                # we'll add it now, and delete it later if necessary
                outArray.append(dependency)
                for lex in co.auto[iD]:
                    if re.match('NP/.*S.*', co.auto[iD][lex][0][0]) != None:
                        if co.debug:
                            print("\tFound relative with csubj", dependency, lex, co.auto[iD][lex])
                        for arg in co.sdfi[iD]:
                            for xcomp in co.sdfi[iD]:
                                if len(arg) > 1 and len(xcomp) > 1:
                                    if arg[3] == lex and \
                                       xcomp[0] == 'xcomp' and \
                                       xcomp[3] == arg[1] and \
                                       xcomp[4] == arg[2] and \
                                       xcomp[1] == dependency[3] and \
                                       xcomp[2] == dependency[4]:
                                        newNsubj = co.getLex(['nsubj', dependency[1], dependency[2], arg[3], arg[4]], co.auto[iD], iD)
                                        newSub = co.getLex(['sub', arg[3], arg[4], dependency[3], dependency[4]], co.auto[iD], iD)
                                        if co.debug:
                                            print("\t###OF INTEREST###", arg)
                                            print("\t###ADDING", newNsubj)
                                            print("\t###ADDING", newSub)
                                            print("\t###REMOVING", dependency)
                                        if newNsubj not in outArray:
                                            outArray.append(newNsubj)
                                            conjoined = co.checkForConj(sentArray, iD, newNsubj)
                                            if conjoined != []:
                                                for c in conjoined:
                                                    if c not in outArray:
                                                        outArray.append(c)
                                                        if co.debug:
                                                            print("\t### conjoined with:", conjoined)
                                        if newSub not in outArray:
                                            outArray.append(newSub)
                                            conjoined = co.checkForConj(sentArray, iD, newSub)
                                            if conjoined != []:
                                                for c in conjoined:
                                                    if c not in outArray:
                                                        outArray.append(c)
                                                        if co.debug:
                                                            print("\t### conjoined with:", conjoined)
                                        if dependency in outArray:
                                            outArray.pop(outArray.index(dependency))
            elif dependency[0] == 'ccomp':
                # if ccomp is a relative, remap for acl:relcl
                # we'll add it now, and delete it later if necessary
                if dependency not in outArray:
                    outArray.append(dependency)
                for lex in co.auto[iD]:
                    if re.match('NP/.*S.*', co.auto[iD][lex][0][0]):
                        if co.debug:
                            print("\tFound relative with ccomp", dependency, lex, co.auto[iD][lex])
                        for arg in co.sdfi[iD]:
                            for xcomp in co.sdfi[iD]:
                                if len(arg) > 1 and len(xcomp) > 1:
                                    if arg[3] == lex and \
                                       xcomp[0] == 'xcomp' and \
                                       xcomp[3] == arg[1] and \
                                       xcomp[4] == arg[2] and \
                                       xcomp[1] == dependency[3] and \
                                       xcomp[2] == dependency[4]:
                                        newAcl = co.getLex(['acl:relcl', arg[3], arg[4], dependency[3], dependency[4]], co.auto[iD], iD)
                                        if co.debug:
                                            print("\t###OF INTEREST###", arg)
                                            print("\t###ADDING", newAcl)
                                            print("\t###REMOVING", dependency)
                                        if newAcl not in outArray:
                                            outArray.append(newAcl)
                                            conjoined = co.checkForConj(sentArray, iD, newAcl)
                                            if conjoined != []:
                                                for c in conjoined:
                                                    if c not in outArray:
                                                        outArray.append(c)
                                                        if co.debug:
                                                            print("\t### conjoined with:", conjoined)
                                        if dependency in outArray:
                                            outArray.pop(outArray.index(dependency))
            # remove redundancy from ref relations
            # TODO is this still needed? I don't think so
            elif dependency[0] == 'ref':
                # this duplicate removal might be better if used outside of this particular instance
                delEm = co.scanForDuplicateRel(sentArray, dependency)
                if len(delEm) > 0:
                    for dE in delEm:
                        if dE in outArray:
                            outArray.pop(outArray.index(dE))
                        sentArray.pop(sentArray.index(dE))
                # Generalize so we remap all pronouns in relative clauses
                if co.debug == True:
                    print("Starting to look for refs")
                # generalize below in to 'remaps old dep' function
                for deps in sentArray:
                    if deps[3] == dependency[3] and deps[4] == dependency[4] and deps[0] != 'ref':
                        if co.debug == True:
                            print('ref deps', deps)
                            print('ref dependency', dependency)
                        # make the below code into a 'purge' function
                        if deps in outArray:
                            outArray.pop(outArray.index(deps))
                        # Does this need to be both?
                        if deps in sentArray:
                            # if dels in sentArray:
                            sentArray.pop(sentArray.index(deps))
                        if co.debug == True:
                            print("ref adding",
                                  [deps[0], deps[1], deps[2], dependency[1], dependency[2], deps[5], dependency[6]])
                            print("ref deleting", deps)
                        outArray.append(
                            [deps[0], deps[1], deps[2], dependency[1], dependency[2], deps[5], dependency[6]])
                outArray.append(dependency)
            # currently causing trouble
            elif dependency[0] == 'aux' or dependency[0] == 'auxpass':
                if co.rev == True:
                    addThese, delThese = co.remapRel(sentArray, dependency)
                    for aT in addThese:
                        if co.debug == True:
                            print("\tadding from rel remap:", aT)
                        outArray.append(aT)
                    for dT in delThese:
                        if co.debug == True:
                            print("\tdeleting from rel remap:", aT)
                        if dT in outArray:
                            outArray.pop(outArray.index(dT))
                        # Does this need to be both?
                        if dT in sentArray:
                            # if dels in sentArray:
                            sentArray.pop(sentArray.index(dT))
                else:
                    outArray.append(dependency)
            else:
                outArray.append(dependency)
        return outArray

    def remapRel(co, sentArray, relArray):
        """
        This function originally remapped relation labels, governors, and dependents
        in a way that didn't produce skipped words in the sentence. It's only used
        by the aux/auxpass labels in postprocess, so until that functionality is fully
        implemented, you can ignore this function as it will not be called.
        :param sentArray: sentence as an array
        :param relArray: dependency to have its gov./dep. flipped
        :return: two lists of additions and deleteions
        """
        adds = []
        dels = []
        if co.debug == True:
            print("reverse rel", relArray[0], "with dependency", relArray)
            print("\tMatching against:", relArray)
        passRel = relArray[0]
        head = relArray[1]
        hInd = relArray[2]
        dep = relArray[3]
        depInd = relArray[4]
        hPOS = relArray[5]
        dPOS = relArray[6]
        newDependency = [passRel, dep, depInd, head, hInd, dPOS, hPOS]
        adds.append(newDependency)
        for deps in sentArray:
            otherrel = deps[0]
            otherhead = deps[1]
            otherhInd = deps[2]
            otherdep = deps[3]
            otherdInd = deps[4]
            otherhPOS = deps[5]
            otherdPOS = deps[6]
            # Assuming rel(X, Y) which we just reved to rel(Y, X) -- given dep(A, B):
            # if A = X, B = Y, and rel != dep -- rev
            # WHY ARE WE REVERSING THESE?
            if otherdep == dep and \
               otherdInd == depInd and \
               head == otherhead and \
               hInd == otherhInd and \
               passRel != otherrel and \
               otherdep != otherhead and \
               otherdInd != otherhInd:
                if co.debug == True:
                    print("\tif A = X, B = Y, and rel != dep -- rev :", deps)
                add = [otherrel, otherdep, otherdInd, otherhead, otherhInd, otherdPOS, otherhPOS]
                if co.debug == True:
                    print("\t\t rev add", add)
                    print("\t\t rev del", deps)
                adds.append(add)
                dels.append(deps)
            # if A = Y, B = X, and rel != dep -- rev
            # this makes sense
            elif otherhead == dep and \
                 otherhInd == depInd and \
                 otherdep == head and \
                 otherdInd == hInd and \
                 passRel == otherrel and \
                 otherdep != otherhead and \
                 otherdInd != otherhInd:
                # if otherhead == dep and otherhInd == depInd and otherdep == head and otherdInd == hInd and passRel == otherrel and otherdep != otherhead and otherdInd != otherInd:
                if co.debug == True:
                    print("\tif A = Y, B = X, and rel != dep -- rev:", deps)
                add = [otherrel, otherdep, otherdInd, otherhead, otherhInd, otherdPOS, otherhPOS]
                if co.debug == True:
                    print("\t\t rev add", add)
                    print("\t\t rev del", deps)
                adds.append(add)
                dels.append(deps)
            # if only B = Y -- point to A
            # this stops gaps?
            elif otherdep == dep and \
                 otherdInd == depInd and \
                 head != otherhead and \
                 hInd != otherhInd and \
                 otherhead != head and \
                 otherhInd != hInd:
                # and passRel != otherrel:
                if co.debug == True:
                    print("\tif only B = Y -- point to A", deps)
                add = [otherrel, otherhead, otherhInd, head, hInd, otherhPOS, hPOS]
                if co.debug == True:
                    print("\t\t rev add", add)
                    print("\t\t rev del", deps)
                adds.append(add)
                dels.append(deps)
                # if only A = X -- points from B
                # let's try not changing heads
                # elif otherdep != dep and otherdInd != depInd and head == otherhead and hInd == otherhInd:
                # # and passRel != otherrel:
                # if co.debug == True:
                # print("\tif only A = X -- points from B", deps)
                # add = [otherrel, dep, depInd, otherdep, otherdInd, dPOS, otherdPOS]
                # if co.debug == True:
                # print("\t\t rev add", add)
                # print("\t\t rev del", deps)
                # adds.append(add)
                # dels.append(deps)
            # if only A = Y -- point to B
            elif otherdep == head and \
                 otherdInd == hInd and \
                 dep != otherhead and \
                 depInd != otherdInd and \
                 otherhead != dep and \
                 otherhInd != depInd:
                # and passRel != otherrel:
                if co.debug == True:
                    print("\tif only B = Y -- point to A", deps)
                add = [otherrel, otherhead, otherhInd, dep, depInd, otherhPOS, dPOS]
                # quick check that we're not making cycles
                if co.debug == True:
                    print("\t\t rev add", add)
                    print("\t\t rev del", deps)
                adds.append(add)
                dels.append(deps)
                # if only B = X -- points from A
                # elif otherdep != head and otherdInd != hInd and dep == otherhead and depInd == otherdInd:
                # # and passRel != otherrel:
                # if co.debug == True:
                # print("\tif only A = X -- points from B", deps)
                # add = [otherrel, head, hInd, otherdep, otherdInd, hPOS, otherdPOS]
                # if co.debug == True:
                # print("\t\t rev add", add)
                # print("\t\t rev del", deps)
                # adds.append(add)
                # dels.append(deps)
            else:
                if co.debug == True:
                    print("\t\t doing nothing with:", deps)
                # assert(otherdep != dep and otherdInd != depInd and head != otherhead and hInd != otherhInd and otherrel != passRel),[relArray, deps]
                add = [otherrel, otherhead, otherhInd, otherdep, otherdInd, otherhPOS, otherdPOS]
                adds.append(add)
        dels.append(relArray)
        return adds, dels

    def remapPreconj(co, sentArray, pcArray):
        """
        Again, which this script binarized conjunction, this function
        remapped 'ccpreconj' from pointing to the governor of the 'cc'
        relation to its dependent.
        :param sentArray: sentence array -- list of dependencies (also lists)
        :param pcArray: dependency with 'ccpreconj' -- list of strings
        :return:
        """
        newpc = []
        for deps6 in sentArray:
            if deps6[0] == 'conj1' and deps6[3] == pcArray[1] and deps6[4] == pcArray[2]:
                newpc = [pcArray[0], deps6[1], deps6[2], pcArray[3], pcArray[4], deps6[5], pcArray[6]]
        return newpc

    def makeCCConj2(co, sentArray, ccArray, newrel, delrel, conjheads):
        """
        When this script remapped conjunction, this function took extraneous 'cc'
        relation with only one dependent and made them 'conj2,' only in the event
        that there was no 'conj1' from this script, or 'conj' from the SDC output.
        This function was later abstracted to change lonely 'cc's or any other
        dependency into another (newrel), deleting the original (delrel), and en-
        suring the dependency structure suffered no gaps
        :param sentArray: sentence array
        :param ccArray: array with lonely 'cc' relation
        :param newrel: dependency to be created
        :param delrel: dependency to be deleted
        :param conjheads: list of conjunction heads
        :return:
        """
        delz = []
        addz = []
        newconj2 = [newrel, ccArray[3], ccArray[4], ccArray[1], ccArray[2], ccArray[6], ccArray[5]]
        addz.append(newconj2)
        for depz in sentArray:
            if depz[3] == ccArray[1] and \
                            depz[4] == ccArray[2] and \
                            depz[3] not in conjheads and \
                            depz[0] != delrel and \
                            depz[0] not in ['conj1', 'conj2']:
                toAdd = [depz[0], depz[1], depz[2], ccArray[3], ccArray[4], depz[5], ccArray[6]]
                toCheck = ['conj1', depz[1], depz[2], ccArray[3], ccArray[4], depz[5], ccArray[6]]
                # a quick check to stop overwriting conj1s with conj2s
                if toCheck not in sentArray and toAdd not in sentArray:
                    if co.debug == True:
                        print("\tmakeCCConj2 walking:\n\tdepz[0]", depz[0], "is conj2 or conj1?",
                              depz[0] in ['conj1', 'conj2'], '\n\tdeps[3]', depz[3], 'a conjhead?',
                              depz[3] in conjheads)
                    addz.append(toAdd)
                    delz.append(depz)
                    # get puncts realigned, too
            if depz[0] == 'punct' and \
                            depz[1] == ccArray[1] and \
                            depz[2] == ccArray[2]:
                add = [depz[0], ccArray[3], ccArray[4], depz[3], depz[4], ccArray[6], depz[6]]
                rem = depz
                if co.debug == True:
                    print("makeCCConj2 realigning punct:\n\tdepz", depz, "add", add)
                addz.append(add)
                delz.append(depz)
        if co.debug == True:
            print("results from makeCCConj2")
            for d in delz:
                print("\tdeleting", d)
            for a in addz:
                print("\tadding", a)
        return delz, addz

    def scanForDuplicateRel(co, sentArray, refArray):
        """
        This removes duplicate relations created by either supplementing
        basic SDC output with the enhanced or by overzealous maxent
        predictions. Currently only being used for 'ref' relations
        :param sentArray: sentence as array of dependencies
        :param refArray: dependency as array
        :return:
        """
        delThese = []
        checkThese = []
        # The cat that knows me...
        for deps5 in sentArray:
            # in "rel(cat, that), this is looking for all cats
            if deps5[3] == refArray[1] and deps5[4] == refArray[2] and deps5[0] != 'ref':
                checkThese.append(deps5)
            # in "rel(cat, that), this is looking for all thats
            elif deps5[3] == refArray[3] and deps5[4] == refArray[4] and deps5[0] != 'ref':
                delThese.append(deps5)
        # only delete them if they're more than 1 of the same rel
        # (in case 'that' has relations that 'cat' doesn't)
        for dT in delThese:
            count = 0
            for cT in checkThese:
                if dT[0] == cT[0] and dT[1] == cT[1] and dT[2] == cT[2]:
                    count += 1
            if count == 0:
                delThese.pop(delThese.index(dT))
        return delThese

    def scanMarkAdvcl(co, sentArray, markArray, rel, iD):
        """
        this function finds the head of one rel to see if it matches the dep of another,
        then remaps it to point to the head of the original (as in mark/advcl cases)
        consider renaming. Consider depreciating.
        :param sentArray: sentence as array of dependencies
        :param markArray: relation of interest
        :param rel: relation label
        :param iD: CCG like iD
        :return: list of deletable and addable dependencies
        """
        delArray = []
        addArray = []
        for deps4 in sentArray:
            if deps4[0] == rel and deps4[3] == markArray[1] and deps4[4] == markArray[2]:
                delArray.append(deps4)
                new = co.getLex([deps4[0], deps4[1], deps4[2], markArray[3], markArray[4]], co.auto[iD], iD)
                addArray.append(new)
                if co.debug == True:
                    print("\t\tadding", new)
                    print("\t\tdeleting", deps4)
        return delArray, addArray

    def canDeleteCC(co, sentArray, ccArray):
        """
        What this does is count the conj relations
        of any dependency that have the same head as the cc
        in question. If the count is greater than one,
        we can delete it
        :param sentArray: sentence as array
        :param ccArray: cc dependency
        :return: yes or no
        """
        conjcount = 0
        for rels in sentArray:
            if rels[0] == 'conj':
                if rels[1] == ccArray[1] and rels[2] == ccArray[2]:
                    conjcount += 1
                else:
                    assert (rels[1] != ccArray[1] or rels[2] != ccArray[2])
            else:
                assert (rels[0] != 'conj')
        if conjcount == 0:
            return True
        elif conjcount > 0:
            return False

    def getLex(co, depArray, lexDict3, sID1):
        """
        Get the POS tag from CCGBank's auto file
        :param depArray0: dependency graph
        :param lexDict3: dictionary of lexical items
        :param sID1: the sentence ID
        :return: an array changed from [rel word1, index1, word2, index2] to [rel word1, index1, word2, index2, pos1, pos2]
        """
        if len(depArray) == 7:
            depArray = depArray[0:-2]
            # we're erroring out on forward slashes '/':
            # 2/3, Fleet/Norstar, etc.
            # changing to '\/' and '\\/' don't work
            # if co.debug == True:
            # print("trying to find POS tag", )
        try:
            POS1 = lexDict3[sID1][depArray[1].replace('/', '\/')][0][1]
        except:
            POS1 = depArray[1]
            # if co.debug == True:
            # for words in lexDict3[sID1]:
            # print(depArray0[1], words, lexDict3[sID1][words])
        try:
            POS2 = lexDict3[sID1][depArray[3].replace('/', '\/')][0][1]
        except:
            POS2 = depArray[3]
            # if co.debug == True:
            # for words in lexDict3[sID1]:
            # print(depArray0[3], words, lexDict3[sID1][words])
        depArray.append(POS1)
        depArray.append(POS2)
        # print("after:", depArray0)
        assert (len(depArray) == 7), "depArray in getLex is not 7"
        return depArray

    def traverse(co, start, end, ccgarray):
        # TODO delete/depreciate this
        # Old depenendency traversal function that broke a lot
        canTrav = False
        mids = []
        for ccg in ccgarray:
            # basecase
            if len(ccg) > 4:
                if ccg[4] == start and ccg[5] == end:
                    canTrav = True
                elif ccg[5] == start and ccg[4] == end:
                    canTrav = True
                else:
                    if ccg[5] != start and ccg[5] != end and ccg[4] == start:
                        mids.append(ccg[5])
                    elif ccg[4] != start and ccg[4] != end and ccg[5] == start:
                        mids.append(ccg[4])
        if co.debug == True and canTrav == True:
            print('\t\trouting', start, 'to', end, canTrav)
        elif co.debug == True and canTrav == False:
            print('\t\t1-moving to', mids, 'towards', end)
        # this will need to happen as many as three times
        # non-recursive since we won't always find an end
        mid = mids
        mids = []
        if canTrav == False:
            for m in mid:
                for ccg in ccgarray:
                    if len(ccg) > 4:
                        if ccg[4] == m and ccg[5] == end:
                            canTrav = True
                        elif ccg[5] == m and ccg[4] == end:
                            canTrav = True
                        else:
                            if ccg[5] != m and ccg[5] != end and \
                                            ccg[4] == m and ccg[5] != start and \
                                            ccg[4] not in mid:
                                mids.append(ccg[5])
                            elif ccg[4] != m and ccg[4] != end and \
                                            ccg[5] == m and ccg[4] != start and \
                                            ccg[4] not in mid:
                                mids.append(ccg[4])
            if co.debug == True and canTrav == True:
                print('\t\trouting', m, 'to', end, canTrav)
            elif co.debug == True and canTrav == False:
                print('\t\t2-moving to', mids, 'towards', end)
        mid = mids
        mids = []
        if canTrav == False:
            for m in mid:
                for ccg in ccgarray:
                    if len(ccg) > 4:
                        if ccg[4] == m and ccg[5] == end:
                            canTrav = True
                        elif ccg[5] == m and ccg[4] == end:
                            canTrav = True
                        else:
                            if ccg[5] != m and ccg[5] != end and \
                                            ccg[4] == m and ccg[5] != start and \
                                            ccg[4] not in mid:
                                mids.append(ccg[5])
                            elif ccg[4] != m and ccg[4] != end and \
                                            ccg[5] == m and ccg[4] != start and \
                                            ccg[4] not in mid:
                                mids.append(ccg[4])
            if co.debug == True and canTrav == True:
                print('\t\trouting', m, 'to', end, canTrav)
            elif co.debug == True and canTrav == False:
                print('\t\t3-moving to', mids, 'towards', end)
        mid = mids
        if canTrav == False:
            for m in mid:
                for ccg in ccgarray:
                    if len(ccg) > 4:
                        if ccg[4] == m and ccg[5] == end:
                            canTrav = True
                        elif ccg[5] == m and ccg[4] == end:
                            canTrav = True
            if co.debug == True and canTrav == True:
                print('\t\trouting', m, 'to', end, canTrav)
            elif co.debug == True and canTrav == False:
                print('\t\tno way from', start, 'to', end)
        return canTrav

    def argpropcheck(co, sent, conjdep, iD, dep, headdep):
        # TODO delete/depreciate this
        # Old depenendency coordination propogations function that broke a lot
        # headdep should be 1 or 3, for head or dependent
        realign = True
        pair = []
        allmatches = []
        # most of these aren't actually used
        conjrel = conjdep[0]
        conj = conjdep[1]
        conjI = conjdep[2]
        depT = conjdep[3]
        depI = conjdep[4]
        for deps in sent:
            # print("conjdep", conjdep[0])
            # print('deps', deps[0])
            if len(deps) > 1:
                if deps[1] == depT and deps[2] == depI and deps[0] == 'conj':
                    allmatches.append(deps)
                    # else:
                    # print("conjrel == 'conj1' and deps[0] == 'conj2'")
                    # print(conjrel == 'conj1')
                    # print(deps[0] == 'conj2')
                    # print("conjrel == 'conj2' and deps[0] == 'conj1'")
                    # print(conjrel == 'conj2')
                    # print(deps[0] == 'conj1')
        if co.debug == True:
            print("\ttotal from ALLMATCHES\n\t", allmatches)
        pair.append(conjdep[3])
        for am in allmatches:
            if co.debug:
                print("\tSeeing if 1 and 2 from", am, "\n\tare the same as 3 and 4 in", conjdep)
            if am[1] == conjdep[3] and \
                            am[2] == conjdep[4]:
                # if am[3] not in pair:
                pair.append(am[3])
                # elif am[3] == conjdep[3] and \
                # am[4] == conjdep[4]:
                # if am[1] not in pair:
                # pair.append(am[1])
                # pair.append(conjdep[3])
        # print(pair)
        assert (len(pair) >= 1)
        if len(pair) > 1:
            if co.debug:
                print("\ttotal items in PAIR:\n\t", pair)
            for p in pair:
                if not co.traverse(p, dep[headdep], co.ccgs[iD]):
                    realign = False
                    if co.debug:
                        print("\ttrying", p, "against", dep, "for", conjdep)
                        print('\t', p, "to", dep[headdep], realign)
                else:
                    if co.debug:
                        print("\ttrying", p, "against", dep, "for", conjdep)
                        print('\t', p, "to", dep[headdep], realign)
        else:
            if co.debug:
                print("\ttoo few pairs -- no rewriting\n\t")
                print("\ttotal items in PAIR:\n\t", pair)
                print("dep", dep, "for", conjdep)
            realign = False
        # special compound case - Hollingsworth & Vose - 0003.28
        if len(pair) == 2:
            for ccg in co.ccgs[iD]:
                if len(ccg) > 1:
                    if ccg[4] == pair[0] and ccg[5] == pair[1]:
                        realign = True
                    elif ccg[5] == pair[0] and ccg[4] == pair[1]:
                        realign = True
            if realign == True and co.debug == True:
                print("overrode false for true since CCG coordinates these")
        return realign

    def remapdepargs(co, sent, conjdep, iD, conjheads, conjdeps):
        # TODO delete/depreciate this
        # This is the function where we remap the dependents and some heads
        # Currently -- all dependents of a conj are remapped to conj head ('and')
        # Current heads that are remapped to conj:
        #    puncts
        #    advmod
        #    appos
        # Originally this returned a full sentence, but I think just the
        # diffs are better.
        # Error here: 'The X and Y of W and Z think... 0044.113
        removes = []
        changed = []
        # print(sent, conjdep)
        conj = conjdep[1]
        conjI = conjdep[2]
        depT = conjdep[3]
        depI = conjdep[4]
        # count = 0
        for ds in sent:
            # print("\t\t\tds in remapdepargs", ds)
            if ds[0] != 'ignore':
                # check for post modification
                # All dependents get remapped
                if ds[3] == depT and \
                                ds[4] == depI and \
                                ds[0] != 'conj1' and \
                                ds[0] != 'conj2' and \
                                ds[1] != conj and \
                                ds[2] != conjI:
                    check = co.argpropcheck(sent, conjdep, iD, ds, 1)
                    # print("\tFound:", ds, conjdep)
                    # new dep = rel, head, head index, conj, conj index
                    if check == True or ds[0] == 'root':
                        newdep = [ds[0], ds[1], ds[2], conj, conjI]
                        removes.append(ds)
                        changed.append(newdep)
                        if co.debug == True:
                            print("\t\tChanged dep of", ds, "to", newdep, '\nand check is', check)
                        # find anything else that needs to be removed:
                        for d in sent:
                            if d[0] == ds[0] and \
                                            d[1] == ds[1] and \
                                            d[2] == ds[2] and \
                                            d[3] in conjdeps:
                                removes.append(d)
                                if co.debug == True:
                                    print("\t\tAlso removing", d)
                                    # count += 1
                                    # else:
                                    # if conjdep[0] == 'conj2':
                                    # if co.debug == True:
                                    # print("no change for conj1/2 dep", ds, "from", conjdep)
                                    # print("ds[3] == depT")
                                    # print(ds[3] == depT)
                                    # print("ds[4] == depI")
                                    # print(ds[4] == depI)
                                    # print("ds[0] != 'conj1'")
                                    # print(ds[0] != 'conj1')
                                    # print("ds[0] != 'conj2'")
                                    # print(ds[0] != 'conj2')
                                    # print("ds[1] != conj")
                                    # print(ds[1] != conj)
                                    # print("ds[2] != conjI")
                                    # print(ds[2] != conjI)
                # Also, now all puncts, appos, and modifiers with a conj head in common:
                if ds[0] != 'conj1' and \
                                ds[0] != 'conj2' and \
                                ds[0] in ['punct', 'advmod', 'appos', 'nmod', 'case', \
                                          'nmod:tpmod', 'nmod:poss', 'nmod:npmod', \
                                          'mark', 'neg', 'det'] and \
                                ds[1] == depT and \
                                ds[2] == depI and \
                                ds[3] != conj and \
                                ds[4] != conjI and \
                                conjdep[0] != 'conj2':
                    check = co.argpropcheck(sent, conjdep, iD, ds, 3)
                    # this section is doing something with punctiation?
                    # kill this section -- it was a first attempt at the 
                    # argprop check
                    # for d in sent:
                    # if d[0] == 'conj':
                    # if ds[1] == d[1] and ds[2] == d[2]:
                    # for dep in sent:
                    # if dep[0] == 'cc' and dep[1] == d[1] and dep[2] == d[2]:
                    # newdep = [ds[0], conj, conjI, ds[3], ds[4]]
                    # removes.append(ds)
                    # changed.append(newdep)
                    # if co.debug == True:
                    # print('weird cc section1 results\n\t', newdep, '\n\tand removing', ds)
                    # elif ds[1] == d[3] and ds[2] == d[4]:
                    # for dep in sent:
                    # if dep[0] == 'cc' and dep[1] == d[1] and dep[2] == d[2]:
                    # newdep = [ds[0], conj, conjI, ds[3], ds[4]]
                    # removes.append(ds)
                    # changed.append(newdep)
                    # if co.debug == True:
                    # print('weird cc section2 results\n\t', newdep, '\n\tand removing', ds)
                    # new dep = rel, conj, conj index, dep, dep index, conj POS, dep POS
                    if check == True:
                        newdep = [ds[0], conj, conjI, ds[3], ds[4]]
                        removes.append(ds)
                        changed.append(newdep)
                        if co.debug == True:
                            print("\t\tChanged head of", ds, "to", newdep)
                            # find anything else that needs to be removed:
                            # for d in sent:
                            # if d[0] == ds[0] and \
                            # d[1] == ds[1] and \
                            # d[2] == ds[2]:
                            # removes.append(d)
                            # if co.debug == True:
                            # print("\t\tAlso removing", d)

                            # else:
                            # if co.debug == True:
                            # print("no change for conj1/2 head", ds, "from", conjdep)
                            # print("ds[1] == depT")
                            # print(ds[1] == depT)
                            # print("ds[2] == depI")
                            # print(ds[2] == depI)
                            # print("ds[0] != 'conj1'")
                            # print(ds[0] != 'conj1')
                            # print("ds[0] != 'conj2'")
                            # print(ds[0] != 'conj2')
                            # print("ds[0] in ['punct', 'advmod', 'appos', 'nmod', 'case', 'nmod:tpmod', 'nmod:poss', 'nmod:npmod', 'mark', 'neg', 'det']")
                            # print(ds[0] in ['punct', 'advmod', 'appos', 'nmod', 'case', 'nmod:tpmod', 'nmod:poss', 'nmod:npmod', 'mark', 'neg', 'det'])
                            # print("ds[1] != conj")
                            # print(ds[1] != conj)
                            # print("ds[2] != conjI")
                            # print(ds[2] != conjI)
                            # else:
                            # if co.debug == True:
                            # print("Changed nothing. Should we have?\nds", ds,'\nconjdep', conjdep, '\n'\
                            # "ds[0] != 'conj1'", \
                            # ds[0] != 'conj1', '\n', \
                            # "ds[0] != 'conj2'", \
                            # ds[0] != 'conj2', '\n', \
                            # "ds[0] in list", \
                            # ds[0] in ['punct', 'advmod', 'appos', 'nmod', 'case' \
                            # 'nmod:tpmod', 'nmod:poss', 'nmod:npmod', \
                            # 'mark', 'neg', 'det'], '\n', \
                            # "ds[1] == depT", \
                            # ds[1] == depT, '\n', \
                            # "ds[2] == depI", \
                            # ds[2] == depI, '\n', \
                            # "ds[3] != conj", \
                            # ds[3] != conj, '\n', \
                            # "ds[4] != conjI", \
                            # ds[4] != conjI)
                            # print("\tNothing:", ds, conjdep)
                            # print("\tds[3] and depT", ds[3], depT)
                            # print("\tds[4] and depI", ds[4], depI)
                            # newsent.append(ds)
                            # special remap for conj2 modifiers since they're not all removed
                            # if count == 0:
                            # newsent.append(['sub', 'ROOT', 0, conj, conjI])
                            # print(count)
                            # for each in newsent:
                            # print(each)
        return removes, changed

    def getLemma(co, wordform):
        """
        This requires morpha to be working and for the noninteractive
        version to be called morphaNoI in the same directly as this
        script runs: https://github.com/knowitall/morpha
        :param wordform: any word string
        :return: lemma
        """
        # Array of things that will break Bash and Morpha:
        notthese = ['"', '`', '``']
        if wordform not in notthese:
            cmd = 'echo "'
            # print("wordform", wordform)
            cmd = cmd + wordform
            cmd = cmd + '" | ./morphaNoI -u'
            byteLemma = subprocess.check_output(cmd, shell=True)
            lemma = byteLemma.decode("utf-8").replace("\n", '')
            return lemma
        elif wordform in notthese:
            return wordform

    def ready4Tabs(co, depArray, normCon1):
        """
        make sure the right format was selected
        -d for SDC like output, -c for conll-like, and -n
        for what I call 'normal,' which is just one I found
        a little easier to read during debugging. Then call
        the right function for output.
        :param depArray: sentence as array
        :param normCon1: -c, -n, or -d
        :return: nothing
        """
        if normCon1 == '-c':
            co.conllTabs(depArray)
        elif normCon1 == '-n':
            co.normalTabs(depArray)
        elif normCon1 == '-d':
            co.depTabs(depArray)
        else:
            print(normCon1,
                  "isn't a valid option. Please select -c for CoNLL 2008 output, or -n for normal tab delimited output.")

    def conllTabs(co, newdeps):
        """
        Now we take the underlying SDC representation and output it as
        something like the CoNLL 2008 formatting that works with White's
        (2014) induction code (see induce branch of openCCG).
        :param newdeps: dependencies to be formatted
        :return: nothing
        """
        assert (len(newdeps) >= 7), "newdeps in ready4Tabs is less than 7" + str(newdeps)
        # ConLL line:
        if newdeps[0] == 'compound':
            lemma0 = newdeps[3]
        else:
            lemma0 = co.getLemma(newdeps[3])
        newArray = [newdeps[4].replace("'", ""), newdeps[3], lemma0, newdeps[6], newdeps[6], "_",
                    newdeps[2].replace("'", ""), newdeps[0]]
        if len(newdeps) > 7:
            # we have extra dependency to deal with
            assert (len(newdeps) == 8), "newdeps has more than 9"
            # for conll:
            conll = newdeps[7].split(';')
            extender = 8
            extra = ''
            for aD in conll:
                ready = aD.split(',')
                # 10/subj
                extra = extra + ready[1].replace("'", "") + '/' + ready[0] + ','
            # remove final comma
            extra = extra[0:-1]
            newArray.append(extra)
            for i in range(extender):
                newArray.append('_')
        elif len(newdeps) == 7:
            # conll with no extra deps
            newArray.extend(('_', '_', '_', '_', '_', '_', '_', '_', '_'))
        elif len(newdeps) < 7:
            print("Error, this shouldn't be possible, len(newdeps) < 7")
        assert (len(newArray) == 17), "Bad newArray in conllTabs function " + str(len(newArray)) + " " + str(newArray)
        print('\t'.join(newArray))

    def depTabs(co, newdeps):
        """
        For this particular output, we simply concatenate all but the
        last two POS tags to get normal SDC output -- good for comparing
        formalisms
        :param newdeps: sentences as array of dependencies
        :return: nothing
        """
        assert (len(newdeps) >= 7), "newdeps in ready4Tabs is less than 7 " + str(newdeps)
        # SD line
        newLine = newdeps[0] + "("
        newLine = newLine + newdeps[1] + "-" + newdeps[2] + ', '
        newLine = newLine + newdeps[3] + "-" + newdeps[4] + ')'
        print(newLine)

    def quickDict(co, newdepArray):
        """
        build a quick index keyed dictionary for dependency output
        Old utility
        :param newdepArray sentence as array of dependencies
        """
        # TODO delete/depreciate me
        qD = {}
        for newdeps in newdepArray:
            qD[newdeps[2]] = newdeps[1]
            qD[newdeps[4]] = newdeps[3]
        return qD

    def normalTabs(co, newdeps):
        """
        This outputs a simple output which more easily legible
        than the other two in my entirely subjective opinion
        :param newdeps: sentence as array of dependencies
        :return: nothing
        """
        # print(len(newdeps), newdeps)
        assert (len(newdeps) >= 7), "newdeps in ready4Tabs is less than 7 " + str(newdeps)
        if newdeps[0] == 'compound' or newdeps[6] == 'NNP':
            lemma1 = newdeps[3]
        else:
            lemma1 = co.getLemma(newdeps[3])
        # Normal human line:
        newArray = [newdeps[4], newdeps[3], lemma1, newdeps[6], newdeps[2], newdeps[0]]
        if len(newdeps) > 7:
            assert (len(newdeps) == 8), "newdeps has more than 8 " + newdeps
            # for normal:
            newArray.append(newdeps[7])
        elif len(newdeps) < 7:
            print("Error, this shouldn't be possible")
        print('\t'.join(newArray))

    def sortThem(co, readyArray):
        """
        Quick utility for keeping sentence order in output
        for legibility
        :param readyArray: sentence as array of dependencies
        :return: same array, but sorted
        """
        sortThese = {}
        for unruly in readyArray:
            checkForApost = unruly[4].strip("'")
            key = int(checkForApost)
            if key not in sortThese:
                sortThese[key] = []
                sortThese[key].append(unruly)
            elif key in sortThese:
                # make sure we don't have duplicates
                if unruly not in sortThese[key]:
                    sortThese[key].append(unruly)
            else:
                print("Python is incredibly broken")
        return sortThese

    def preRepair(co, sentArray, iD):
        # TODO delete/depreciate this
        # this was an attempt at fixing gaps
        missing = []
        sentorder = []
        possFixer = {}
        for deps in sentArray:
            sentorder.append(int(deps[4]))
        prev = 0
        for ind in sorted(set(sentorder)):
            if ind - prev != 1:
                missing.append(str(ind - 1))
            prev = ind
        if len(missing) > 0:
            for m in missing:
                for deps in co.sdfi[iD]:
                    if len(deps) > 4:
                        if deps[4] == str(m):
                            if m not in possFixer:
                                possFixer[m] = []
                            possFixer[m].append(deps)
        if co.debug == True:
            print("\tsent indexes:", sorted(set(sentorder)))
            print("\tmissing indexes:", missing)
            print("\tpossFixer:", possFixer)
        # if there are more than out, print it to debug so we can see later:
        for p in possFixer:
            if len(possFixer[p]) > 1:
                # and fix with the last one -- less likely to be something we wanted to delete
                fix = co.getLex(possFixer[p][-1], co.auto[iD], iD)
                sentArray.append(fix)
                if co.debug == True:
                    print("\tfixing gap with", possFixer[p][-1])
                    print("\tmore than one though", possFixer[p])
            elif len(possFixer[p]) == 1:
                fix = co.getLex(possFixer[p][0], co.auto[iD], iD)
                sentArray.append(fix)
                if co.debug == True:
                    print("\tfixing gap with only option", possFixer[p][0])
            elif len(possFixer[p]) == 0:
                if co.debug == True:
                    print("\tNo way to fix, possFixer has no entries")
        return sentArray

    def checkForGaps(co, sentDict, iD):
        """
        This is a very important function. In SDC output, a word can
        be accidentally skipped for a variety of reasons. This is functionally
        and additional ROOT. To mitegate this, we combine enhanced and basic
        SDC output, but we still want to know where and when words get skipped.
        This function finds them and outputs that information when the --debug
        is used
        :param sentDict: sentence as array of dependencies
        :param iD: CCG like ID
        :return: sentDict, as is, and whether there are gaps (skipped words) T/F
        """
        currentNum = 0
        addthese = {}
        gaps = False
        for depNum in sentDict:
            if (depNum - currentNum) == 1:
                currentNum = depNum
            elif (depNum - currentNum) != 1:
                gaps = True
                if co.debug == True:
                    print("There are gaps in this sentence!", iD)
                    print("depNum", depNum, "currentNum", currentNum)
                    for s in sentDict:
                        print("\t", s, sentDict[s])
                        # sys.exit()
                # fixer = [["ERROR", "ERROR", str(depNum), "ERROR", str(currentNum), "ERROR", "ERROR"]]
                currentNum += 1
                # assert(currentNum not in sentDict),"We're overgenerating tokens, currentNum in is sentDict in findGaps function"
                # addthese[currentNum] = fixer
                currentNum += 1
            else:
                sys.exit("depNum - currentNum is neither 1 nor not 1\nSee checkForGaps function")
        if not addthese == {}:
            for newindex in addthese:
                sentDict[newindex] = addthese[newindex]
        return sentDict, gaps


    def lexbuilder(co, autostring):
        """
        building a dictionary of lexical entries with their CCG cat and PTB POS
        tag -- This is mostly used for pulling argument categories. Each line is
        broken into an array, and only the first 5 entries after an entry matching
        '(<L' are used.
        :param autostring: entry forom a CCGbank auto file
        :return: dictionary keyed on token
        """
        broken = autostring.split()
        # Creating hash to associate category and pos tuple to lexical entry
        lex = {}
        i = 0
        while i <= (len(broken) - 1):
            if broken[i] == '(<L':
                try:
                    lex[broken[i + 4]].append((broken[i + 1], broken[i + 3]))
                    # assert(broken[i+2] == broken[i+3]),"POS doesn't match other POS"
                    # lex[broken[i+4]].append([broken[i+1],broken[i+2]])
                    # assert(broken[i+2] == broken[i+3])
                except:
                    lex[broken[i + 4]] = []
                    lex[broken[i + 4]].append((broken[i + 1], broken[i + 3]))
                    # print broken[i+4],broken[i+3]
                    # assert(broken[i+2] == broken[i+3]),"POS doesn't match other POS"
            i += 1
        neatlex = {}
        # erase the duplicates
        for lists in lex:
            neatlex[lists] = sorted(set(lex[lists]))
        # print neatlex
        return neatlex


# input = FORMAT, DEPS, MAX, CONJ, --DEBUG
if __name__ == '__main__':
    if len(sys.argv) < 5:
        runerror = "example:    python3 collate.py -n wsj_0111.mrg.dep.withid maxent.collated newconj.txt wsj_1111.auto\nAdditionally, megam and morpha should be located in the same directory as this program is invoked from."
        print(runerror)
    elif len(sys.argv) >= 6:
        c = collate()
        if len(sys.argv) == 7:
            c.actualstart(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], 'no')
            # c.actualstart(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], 'yes')
        elif len(sys.argv) == 6:
            fauxdebug = "no"
            c.actualstart(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], fauxdebug, 'no')
            # c.actualstart(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], fauxdebug, 'yes')
        else:
            sys.exit("The final argument must be nothing or '--debug'")
        c.iterate()
        # c.checkoutput()
