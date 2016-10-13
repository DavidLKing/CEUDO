from cdc import counter
import sys

# Sample command:
# pypy rename.py wsj_0005.mrg.dep output.txt

assert(len(sys.argv) == 3),"There should be two arguments.\nExample:pypy rename.py wsj_0005.mrg.dep output.txt"
df = sys.argv[1]
of = sys.argv[2]
# Adding fake ccgfile
cf = "fake"
fakedict = {}
ct = counter(fakedict,df,cf)
ct.addDepSeqNumbers(df,of)
