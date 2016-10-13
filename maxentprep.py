import cdc
import sys
import pickle

ccgs = sys.argv[1]
deps = sys.argv[2]
auto = sys.argv[3]
ofile = sys.argv[4]
cndict = 'fake'

c = cdc.counter(cndict,ccgs,deps)
res = c.maxentprep(ccgs,deps,auto, 'no')
c.presults(res, ofile)

# print "cndict",cndict
# print "c.counts",c.counts
