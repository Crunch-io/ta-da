#!/usr/bin/env python
import sys, os, time, platform
from math import sqrt

CUTOFF = 0.5 # Drop nodes with less than this percent time
COLOR_MIN = 2  # Coloring starts at this level

_last = 0
def new_id():
    global _last
    _last += 1
    return _last

def colorcode(t):
    if t < COLOR_MIN:
        return None
    f = min((t-COLOR_MIN)/(100.-COLOR_MIN), 1.0)
    f = sqrt(f) # non-linear emphasis
    h = f*0 + (1-f)*0.15 # Yellow-orange
    s = max(f, 0.1)
    v = 1
    return "%.3f %.3f %.3f" % (h,s,v)

def recurse(d, out, parent=None):
    call = d['__call__']
    time = d['__time__']
    t = float(time[:-1]) # Remove % sign
    me = new_id()
    if t < CUTOFF:
        return
    out.write('N%d\n' % me)
    color = colorcode(t)
    out.write('[label="%s\\n%s"' % (call, time))
    if color:
        out.write('style=filled,fillcolor="%s"' % color)
    out.write('];\n')
    if parent:
        out.write('N%d -> N%d;\n' % (parent, me))
    for child in d['{calls}']:
        recurse(child, out, me)

null = None
in_block = False
testname = '???'
timings={}
for line in sys.stdin:
    if line.startswith('FAIL:'):
        testname = line.split()[1]

        # Do something with the class name?
    if 'begin captured stdout' in line:
        lines = []
        in_block = True
        continue
    if 'end captured stdout' in line:
        in_block = False
        timings[testname] = eval(''.join(lines))
    if in_block:
        lines.append(line)


for testname in timings.keys():
    assert len(timings[testname]) == 1
    suffix = ''
    while os.path.exists('%s%s.svg' % (testname, suffix)):
        suffix = suffix+1 if suffix else 1
    outfile = '%s%s.svg' % (testname, suffix)
    p = os.popen('dot -Tsvg -o%s' % outfile, 'w')
    p.write('digraph %s {\n' % testname)
    p.write('label="%s\\n%s\\nPython %s\\n%s: %s\nlabelloc=top\n' %
            (testname,
             time.ctime(),
             platform.python_version(),
             platform.node(),
             platform.processor()))
    recurse(timings[testname][0], p)
    p.write('}\n')
    status = p.close()
    if status:
        print status
        print "dot command failed"
        

    

