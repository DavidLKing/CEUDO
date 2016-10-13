import sys
import re
from remap import remap

"""
there has to be a better way to do arguments in python
import argparse
p = parser = argparse.ArgumentParser(description='A script for combining collapses and enhanced SDC output.')
p.add_argument('--debug', dest='debug', default=False, type=str, help='an integer for the accumulator')
args = parser.parse_args()
"""
r = remap()

"""
read in two sentences
if new deps have a colon -- ignore
if no colon and no in old deps --add
write to std out
"""

def makeHash(depFile, keepall):
    """
    Read in a series of dependencies, read their IDs and make a hash with those IDs as a key
    Should be SDC output neutral (enhanced, basic, makeCopulaHead, etc.)
    keepall is a parameter for deciding how much we trust a given schema.
    If set to True, we just make a hash and filter nothing.
    If set to False, we remove 'dep' relations
    This is also currently hardwired to convert 'nmod:of' type relations to 'nmod', since these
    are eventually going into a machine learning system we don't want to confuse with data sparsity.
    :param depFile: SDC output with CCGbank names from rename.py
    :param keepall: True or False
    :return: a very neat hash keyed on CCGbank IDs, also a list of IDs for a sanity check later
    """
    depHash = {}
    iDs = []
    iD = ''
    isId = re.compile('<s id=')
    ignore = re.compile('.*:.*')
    for line in open(depFile, 'r'):
        """
        if we find an ID, we're at a new sentence:
        We add lines as we go, so the previous sentence is done.
        Make a new entry for the iD, then start appending some more
        """
        if isId.match(line) != None:
            iD = line.replace('<s id="wsj_', '').replace('">', '').split('.')[1].strip()
            iDs.append(iD)
            #~ print("iD", iD)
            depHash[iD] = []
            depHash[iD].append(line)
        elif len(line.split('(')[0].split(':')) > 1 and line.split('(')[0].split(':')[0] == 'nmod':
            """remove the nmod:of types and make them nmod types"""
            newline = line.split(":")
            # grab the nmod relation
            newdep = [newline[0]]
            # we don't want the 'of' in 'nmod:of'
            removeSparcity = ':'.join(newline[1:])
            removeSparcity = removeSparcity.split('(')
            # make sure nothing crazy is happening
            assert(len(removeSparcity) == 2)
            newdep.append(removeSparcity[1])
            #~ print('('.join(newdep), "original", line)
            assert(len(newdep) == 2)
            depHash[iD].append('('.join(newdep))
        elif ignore.match(line) != None and keepall == False:
            """ignore all others with : """
            pass
        elif line.split('(')[0] == 'dep' and keepall == False:
            """ we don't want enhanced underspecified 'dep' relations """
            pass
        else:
            """otherwise append, making sure we're not on the first iD"""
            assert(iD != None)
            depHash[iD].append(line)
    return depHash, iDs
    
def goAhead(noncollapsed, enhanced):
    """
    General function for not overwriting good nonnoncollapsed deps
    with weird enhanced ones (weird being different root or
    other issues
    :param noncollapsed: noncollapsed sentence hash, key = ID
    :param enhanced: enhanced sentence hash, key = ID
    :return: progress = True or False
    """
    progress = True
    """for checking different roots"""
    unColRoot = ''
    enhRoot = ''
    """for checking different deps of interest, OI = of interest -- expendable"""
    depOI = set()
    for rel in ['cc']:
        depOI.add(rel)
    unColOI = set()
    for c in noncollapsed:
        if r.dep2split(c).split()[0] == 'root':
            unColRoot = c
        """do the same for 'cc' -- possibly more deps"""
        if r.dep2split(c).split()[0] in depOI:
            unColOI.add(c)
    """Now we have a list of noncollapsed dependencies of interest -- now let's look at the enhanced group"""
    for e in enhanced:
        if r.dep2split(e).split()[0] == 'root':
            enhRoot = e
        if r.dep2split(e).split()[0] in depOI:
            if e not in unColOI:
                """if we find different sets of dependencies we care about, we probably have different structures
                and combining them would dbe a bad choice"""
                progress = False
                if debug:
                    print("progress switched to false. e absent from unColOI:", e, unColOI, e not in unColOI)
            # only needed in extreme debugging cases
            else:
                if debug:
                    print("progress left alone. e absent from unColOI:", e, unColOI, e not in unColOI)
    """if the roots don't match, do not continue"""
    if unColRoot != enhRoot:
        if debug:
            print("progress switched to true. unColRoot != enhRoot:", unColRoot != enhRoot)
        progress = False
    else:
        if debug:
            print("progress left alone. unColRoot != enhRoot:", unColRoot != enhRoot)
    return progress

"""way simpler than argparse"""
if len(sys.argv) > 3:
    if sys.argv[3] == '--debug':
        debug = True
        print("Debugging is turned on!")
    else:
        sys.exit("Third argument must be '--debug' or nothing")
else:
    debug = False

"""actual beginning, get the hashes"""
oldDep, iDs = makeHash(sys.argv[1], True)
enhancedDep, moreiDs = makeHash(sys.argv[2], False)

"""quick sanity check"""
assert(iDs == moreiDs)

for i in iDs:
    """
    Check to see if we can go ahead
    """
    forward = goAhead(oldDep[i], enhancedDep[i])
    if debug:
        print("goAhead(oldDep[i], enhancedDep[i]) = ", forward)
    if forward:
        endOfSent = oldDep[i].pop(-1)
        """ remove </s> """
        enhancedDep[i].pop(-1)
        for deps in enhancedDep[i]:
            if deps not in oldDep[i]:
                oldDep[i].append(deps)
                # print("adding", deps)
        oldDep[i].append(endOfSent)
        """
        For removing extraneous nsubj(..., that)
        Enhanced deps have explicit argument relations to content words.
        Giving relatives the same relation duplicates our argument relations.
        Let's fix that -- this occurs after we've already appended the
        enhanced deps.
        """
        for dep in oldDep[i]:
            d = r.dep2split(dep).split()
            # print("d", d, "d[0]", d[0])
            """
            target construction: ... symptoms that show ...
            ['nsubj', 'show', '25', 'that', '24']
            ['ref', 'symptoms', '23', 'that', '24']
            ['nsubj', 'show', '25', 'symptoms', '23']
            """
            if d[0] in ['nsubj', 'dobj', 'iobj']:
                for dep2 in oldDep[i]:
                    d2 = r.dep2split(dep2).split()
                    if d2[0] == 'ref' and \
                       d2[3] == d[3] and \
                       d2[4] == d[4]:
                        """ make sure there's a replacement """
                        # print("check\n", d, '\n', d2)
                        for dep3 in oldDep[i]:
                            d3 = r.dep2split(dep3).split()
                            if d3[0] in ['nsubj', 'dobj', 'iobj'] and \
                               d3[1] == d[1] and \
                               d3[2] == d[2] and \
                               d3[3] == d2[1] and \
                               d3[4] == d2[2] and \
                               d3[3] != d[3] and \
                               d3[4] != d[4]:
                                # print('removing arg', dep, "replacement", dep3, "ref", dep2)
                                # for depdep in oldDep[i]:
                                #     print(depdep)
                                if dep in oldDep[i]:
                                    oldDep[i].pop(oldDep[i].index(dep))
    for dep in oldDep[i]:
        #~ pass
        """
        The replace portion here fixes a very infuriating bug where
        the SDC outputs apostrophes after indices in some cases
        """
        print(dep.strip().replace("',", ",").replace("')", ")"))

# print("Debug is", debug)