import re
import sys
import os
from collate import collate

# import mrgs
# counts starts at 1
# grap basename
# if regexp S (S matches, 
#    count increments
# if TMP= matches
#    load basename + "_" + str(count) to array
# when done, for each in array
#    print each

c = collate()

mrg = open(sys.argv[1], 'r')
# auto file for lexical entries
a = open(sys.argv[2], 'r')
auto = c.other2dict(a, 'a')
# actual mrg.dep.withid file, not the conll output
d = open(sys.argv[3], 'r')
deps = c.other2dict(d, 'd')


# for getLex
#~ try:
    #~ POS1 = lexDict3[sID1][depArray0[1]][0][1]
#~ except:
    #~ POS1 = depArray0[1]

count = 0
tmps = []
prebase = os.path.splitext(sys.argv[1])[0]
base = re.sub('.*/','',prebase)
baseperiod = base.rsplit('.')[0] + "."
#'<s id="' + base.rsplit('.')[0] + "."
for line in mrg:
    #~ print("Does", line, "match?")
    if re.match('^\( \(', line) != None:
        #~ print("previous count", count)
        count += 1
        #~ print("new senetnce")
    elif re.match('.*=.*', line) != None:
        tmps.append(baseperiod + str(count))
        #~ print("yes!")
    #~ else:
        #~ print("No")
    elif re.match('.*RNR.*', line) != None:
        remove = False
        iD = baseperiod + str(count)
        #~ print("\tfound an RNR", iD)
        for dep in deps[iD]:
            #~ depArray = c.dep2split(dep)
            #~ print("dep", dep)
            if dep[0] == 'conj':
                try:
                    POS1 = auto[iD][dep[1]][0][1]
                except:
                    POS1 = 'okay'
                try:
                    POS2 = auto[iD][dep[3]][0][1]
                except:
                    POS2 = 'okay'
                # stupidly simple, if their first letters don't match,
                # they're in separate classes
                if POS1[0] in ['J', 'V'] and POS2[0] in ['J', 'V']:
                    pass
                    #~ print("\tcannot remove", dep, POS1, POS2)
                elif POS1[0] != POS2[0]:
                    remove = True
                    #~ print("\table to remove", dep, POS1, POS2)
                else:
                    #~ print("\tcannot remove", dep, POS1, POS2)
                    pass
        if remove == True:
            tmps.append(baseperiod + str(count))
for temps in sorted(set(tmps)):
    print(temps)
