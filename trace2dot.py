#!/usr/bin/env python
import sys
import os
import time
import platform
import re
import argparse
import cPickle
from math import sqrt

# TODO: make these command-line args

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--cutoff', default=0.1,
                    help='omit nodes with less than this percent of total time')
parser.add_argument('-nc', '--no-collapse', action='store_true',
                    help='do not combine repeated calls (graph will be huge!)')
parser.add_argument('-t', '--title', default='trace2dot',
                    help='title for graph')
parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                    default=sys.stdin)
parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                    default=sys.stdout)

# Add flag for 2-color operation (requires graphviz 2.34)

args = parser.parse_args()
cutoff = args.cutoff
title = args.title
collapse = not args.no_collapse
infile = args.infile
outfile = args.outfile

timestamp = os.fstat(infile.fileno()).st_ctime
data = cPickle.load(infile)
#infile.close()

total = sum([c.get("__time__", 0.0) for c in data] + [0.0])

try:
    meminfo = open('/proc/meminfo').readline().split()
    if meminfo[0] == 'MemTotal:' and meminfo[2] == 'kB':
        meminfo = int(meminfo[1]) / (1048576.) # Convert kB to GB
    else:
        meminfo = None
except:
    meminfo = None

color_min=1

def colorcode(pct):
    if pct < color_min:
        return "white"
    f = min((pct - color_min) / (100.0 - color_min), 1.0)
    f = sqrt(f)
    h = f * 0 + (1 - f) * 0.15  # Yellow-orange
    s = max(f, 0.1)
    v = 1
    return "%.3f %.3f %.3f" % (h, s, v)

node_id = 0

pat = re.compile("'[0-9a-f]{32}'")

def fixup_expr(expr):
    if isinstance(expr, dict):
        expr = str(expr)
    return re.sub(pat, '<ID>', expr)

def update_accum(a,b):
    for k in b.keys():
        if k == "__call__":
            continue
        if k == "expr":
            if fixup_expr(a.get(k,'')) != fixup_expr(b.get(k, '')):
                raise ValueError, "cannot combine %s and %s" % (a.get(k), b.get(k))
            else:
                continue
        if k == 'types':
            a_types = [x['class'] for x in a['types']]
            b_types = [x['class'] for x in b['types']]
            if a_types != b_types:
                raise ValueError, "cannot combine %s and %s" % (a_types, b_types)
            else:
                continue

        if not a.has_key(k):
            a[k] = b[k]
        else:
            if isinstance(a[k], (int, float, list)):
                a[k] += b[k]
            elif isinstance(a[k], basestring):
                a[k] = '%s, %s' % (a[k], b[k])
            elif isinstance(a[k], tuple):
                a[k] = tuple(a[k]+n[k])
            elif isinstance(a[k], dict):
                update_accum(a[k], b[k])
            elif a[k] is None:
                if b[k] is not None:
                    raise TypeError, "trying to update %s None with %s" % (k, b[k])
            else:
                #pass
                raise TypeError, "key=%s, type=%s" % (k, type(a[k]))

def collapse_children(children):
    result = []
    for c in children:
        c['__ncalls__'] = 1
        expr = c.get('expr')
        found = False
        for r in result:
            exp = fixup_expr(r.get('expr', ''))
            if (r['__call__'] == c['__call__'] and
                fixup_expr(c.get('expr', '')) == exp):
                found = True
                break
        if not found:
            result.append(c)
        else:
            try:
                update_accum(r, c)
            except ValueError: # Cannot merge
                result.append(c)
    return result


def recurse(d, parent=None):
    global node_id
    node_id += 1
    me = node_id

    call = d['__call__']
    ncalls = d.get('__ncalls__', 1)
    cumtime = d.get('__time__', None)
    if cumtime is None:
        return
    if total:
        cumtime_pct = (cumtime / total) * 100
        if cumtime_pct < cutoff:
            return
    else:
        cumtime_pct = 0

    # Calculate individual time by subtracting child times
    selftime = cumtime
    for child in d['{calls}']:
        childtime = child.get('__time__', None)
        if childtime:
            selftime -= childtime
    if total:
        selftime_pct = (selftime / total) * 100
    else:
        selftime_pct = 0

    outfile.write('N%d\n' % me)
    self_color = colorcode(selftime_pct)
    cum_color = colorcode(cumtime_pct)

    if ncalls != 1: # Use stacked polygons?
        call = '%s [%d X]' % (call, ncalls)

    def fmt_time(t):
        return ('%.2fs' % t) if t > 1 else '%.2fms' % (t*1000)

    outfile.write(r'[label="%s\n' % call)

    # Extra annotation
    expr = d.get('expr')
    # Additional escaping of expr?  backslashes?
    if expr:
        outfile.write(fixup_expr(expr))
        outfile.write(r'\n')

    types = d.get('types')
    if types:
        outfile.write(r'%s\n' % str(tuple(t['class'] for t in types)))

    outfile.write(
        r'%s (%.2f%%) self\n%s (%.2f%%) cumulative"' % # ends " started in label=
        (
            fmt_time(selftime), selftime_pct,
            fmt_time(cumtime), cumtime_pct,
        )
    )

    if self_color or cum_color:
        outfile.write(',style=filled,gradientangle=90,fillcolor="%s;0.5:%s"' % (cum_color, self_color))
        # NB - gradient is bottom-to-top
    outfile.write('];\n')
    if parent:
        outfile.write('N%d -> N%d;\n' % (parent, me))

    children = d['{calls}']
    if collapse:
        children = collapse_children(children)
        d['{calls}'] = children

    for child in children:
        recurse(child, me)

def header():
    # Header data will be wrong if trace2dot runs on a different host than
    # the data was captured on.  Perhaps we should include this info in trace
    outfile.write('digraph "%s" {\n' % title)
    outfile.write('label="%s\\n%s\\nPython %s\\n%s: %s' % # Open quote
          (title,
           time.ctime(timestamp),
           platform.python_version(),
           platform.node(),
           platform.processor()))
    if meminfo:
        outfile.write(r'\n%.1fGB' % meminfo)

    outfile.write('"\nlabelloc=top\n') # Close quotes in label

def footer():
    outfile.write('}')


def main():
    header()
    recurse({
        "__call__": title,
        "__time__": total,
        "{calls}": data,
    })
    footer()


if __name__ == '__main__':
    main()
