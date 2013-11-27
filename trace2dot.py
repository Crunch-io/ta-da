#!/usr/bin/env python
import sys, os, time, platform, re
import cPickle
from math import sqrt

# TODO: make these command-line args
cutoff = 0.5
color_min=2
collapse=True
out = sys.stdout

def colorcode(pct):
    if pct < color_min:
        return None
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

    out.write('N%d\n' % me)
    color = colorcode(selftime_pct)
    if ncalls != 1:
        call = '%s [%d X]' % (call, ncalls)


    def fmt_time(t):
        return ('%.2fs' % t) if t > 1 else '%.2fms' % (t*1000)

    out.write(r'[label="%s\n' % call)

    # Extra annotation
    expr = d.get('expr')
    # Additional escaping of expr?  backslashes?
    if expr:
        out.write(fixup_expr(expr))
        out.write(r'\n')

    types = d.get('types')
    if types:
        out.write(r'%s\n' % str(tuple(t['class'] for t in types)))

    out.write(
        r'%s (%.2f%%) self\n%s (%.2f%%) cumulative"' % # ends " started in label=
        (
            fmt_time(selftime), selftime_pct,
            fmt_time(cumtime), cumtime_pct,
        )
    )

    if color:
        out.write('style=filled,fillcolor="%s"' % color)
    out.write('];\n')
    if parent:
        out.write('N%d -> N%d;\n' % (parent, me))

    children = d['{calls}']
    if collapse:
        children = collapse_children(children)
        d['{calls}'] = children

    for child in children:
        recurse(child, me)

def header(testname):
    # This will be wrong if trace2dot runs on a different host than the
    # data was captured on.  Perhaps we should include this info in trace
    out.write('digraph "%s" {\n' % testname)
    out.write('label="%s\\n%s\\nPython %s\\n%s: %s"\nlabelloc=top\n' %
          (testname,
           time.ctime(),
           platform.python_version(),
           platform.node(),
           platform.processor()))

def footer():
    out.write('}')

filename = 'trace.pickle'
testname = 'Silhouette'

args = sys.argv[1:]
while args:
    a = args.pop(0)
    if a.startswith('-t'):
        testname = args.pop(0)
    elif a.startswith('-'):
        sys.stderr.write("Unknown flag %s\n" % a)
        sys.exit(-1)
    else:
        filename = a

infile = open(filename, 'r')
data = cPickle.load(infile)
infile.close()

total = sum([c.get("__time__", 0.0) for c in data] + [0.0])

header(testname)
recurse({
    "__call__": testname,
    "__time__": total,
    "{calls}": data,
})
footer()
