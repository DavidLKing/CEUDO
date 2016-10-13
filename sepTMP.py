#!/usr/bin/python3

"""
This program will read in both conll file and the temps.txt file
If iD is in temps.txt, moves the whole sentence to a different file
    (sdtout >> [concat] to file
All iDs will be removed in general and rewritten to the same
e.g. python3 sepTMP.py temps.txt
"""

import re
import sys


class RemoveTemps:
    def __init__(self):
        self.debug = None
        if len(sys.argv) > 3:
            if sys.argv[3] == '--debug':
                self.debug = True
        else:
            self.debug = False
        if self.debug:
            print("Debugging on:")
        conl = open(sys.argv[1], 'r')
        self.conl = self.loadHash(conl, {})
        tmps = open(sys.argv[2], 'r')
        self.temps = self.loadArray(tmps, [])
        conl.close()
        tmps.close()
        
    def loadArray(self, fileLines, array):
        for fl in fileLines:
            array.append(fl.rstrip('\n'))
            # if self.debug == True:
                # print("\tloadArray fl:", fl.rstrip('\n'))
        return array
        
    def loadHash(self, fileLines, dictionary):
        iD = ''
        for fl in fileLines:
            # if we find an iD
            if re.match('wsj_', fl):
                iD = fl.rstrip('\n')
                dictionary[iD] = []
                # if self.debug == True:
                    # print("\tloadHash fl -- is iD:", fl)
            # if it's not an iD and iD is not blank
            elif iD != '':
                dictionary[iD].append(fl.rstrip('\n'))
                # if self.debug == True:
                    # print("\tloadHash fl -- is dep:", fl.rstrip('\n'))
        # print(dictionary)
        return dictionary
    
    def makeoutput(self):
        """
        remember: the TMP= stuff is going to stdout.
        Ergo, each call will look like:
        python3 sepTMP.py file.conll temps.txt > file.conll.tempequals
        """
        outfile = open(sys.argv[1], 'w')
        # we need to order the output -- original code from collate.py
        order = {}
        keys = []
        for iD in self.conl:
            # print("ID =", iD)
            # print("split =", iD.split('.'))
            afterDot = int(iD.split('.')[1])
            assert (afterDot not in order)
            assert (afterDot not in keys)
            order[afterDot] = iD
            keys.append(afterDot)
        for k in sorted(set(keys)):
            iDs = order[k]
            isTMP = None
            if iDs in self.temps:
                isTMP = True
            else:
                isTMP = False
            if self.debug == True and isTMP == True:
                print(iDs)
            elif self.debug == True and isTMP == False:
                outfile.write(iDs + '\n')
            for deps in self.conl[iDs]:
                if isTMP == True:
                    print(deps)
                elif isTMP == False:
                    deps = deps + '\n'
                    outfile.write(deps)
            # if isTMP == True:
                # print("\n")
            # else:
                # outfile.write("\n")

if __name__ == '__main__':
    rt = RemoveTemps()
    rt.makeoutput()
