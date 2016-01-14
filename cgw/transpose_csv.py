#!/usr/bin/env python

import sys

out = {}

def csvsplit(line):
    out = []
    open_quotes = False
    for t in line.split(','):
        if open_quotes:
            out[-1] += ','+t
            open_quotes = not t.endswith('"')
        else:
            out.append(t)
            open_quotes = t.startswith('"') and not t.endswith('"')
    return out

for line in sys.stdin:
    for i, x in enumerate(csvsplit(line.strip())):
        if i not in out:
            out[i] = open("%06d.dat" % i, 'w')
        out[i].write(x+'\n')

for f in out.values():
    f.close()
