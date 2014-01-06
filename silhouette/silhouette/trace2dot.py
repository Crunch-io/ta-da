#!/usr/bin/env python
import sys
import os
import time
import platform
import re
import argparse
import cPickle
from math import sqrt


class Converter(object):

    def __init__(self, title='trace2dot', cutoff=0.1, collapse=False):
        self.title = title
        self.cutoff = cutoff
        self.collapse = collapse

        self.color_min = 1

        self.timestamp = None
        self.data = None

    def read_trace_file(self, infile):
        self.timestamp = os.fstat(infile.fileno()).st_ctime
        self.data = cPickle.load(infile)
        #infile.close()

    @property
    def total(self):
        return sum([c.get("__time__", 0.0) for c in self.data] + [0.0])

    def write_dot(self, outfile):
        self.node_id = 0

        self.write_header(outfile)
        self.recurse(outfile, {
            "__call__": self.title,
            "__time__": self.total,
            "{calls}": self.data,
        })
        self.write_footer(outfile)

    def write_svg(self, path):
        outfile = os.popen('dot -Tsvg -o%s' % path, 'w')
        self.write_dot(outfile)
        exitcode = outfile.close()
        if exitcode:
            raise IOError("dot did not succeed. Got exitcode %s" % exitcode)

    def colorcode(self, pct):
        if pct < self.color_min:
            return "0 0 1"
        f = min((pct - self.color_min) / (100.0 - self.color_min), 1.0)
        f = sqrt(f)
        h = f * 0 + (1 - f) * 0.15  # Yellow-orange
        s = max(f, 0.1)
        v = 1
        return "%.3f %.3f %.3f" % (h, s, v)

    fixup_pattern = re.compile("'[0-9a-f]{32}'")

    def fixup_expr(self, expr):
        """Return the given expr with unique IDs replaced by a common <ID>."""
        if isinstance(expr, dict):
            expr = str(expr)
        return re.sub(self.fixup_pattern, '<ID>', expr)

    def update_accum(self, a, b):
        """Accumulate members of dict b into the same members of a."""
        for k in b.keys():
            if k == "__call__":
                continue
            if k == "expr":
                if self.fixup_expr(a.get(k, '')) != self.fixup_expr(b.get(k, '')):
                    raise ValueError("Cannot combine %s and %s" % (a.get(k), b.get(k)))
                else:
                    continue
            if k == 'types':
                a_types = [x['class'] for x in a['types']]
                b_types = [x['class'] for x in b['types']]
                if a_types != b_types:
                    raise ValueError("Cannot combine %s and %s" % (a_types, b_types))
                else:
                    continue

            if k not in a:
                a[k] = b[k]
            else:
                if isinstance(a[k], (int, float, list)):
                    a[k] += b[k]
                elif isinstance(a[k], basestring):
                    a[k] = '%s, %s' % (a[k], b[k])
                elif isinstance(a[k], tuple):
                    a[k] = tuple(a[k] + b[k])
                elif isinstance(a[k], dict):
                    self.update_accum(a[k], b[k])
                elif a[k] is None:
                    if b[k] is not None:
                        raise TypeError("trying to update %s None with %s" % (k, b[k]))
                else:
                    #pass
                    raise TypeError("key=%s, type=%s" % (k, type(a[k])))

    def collapse_children(self, children):
        """Collapse repeated children into a single child per set."""
        result = []
        for c in children:
            c['__ncalls__'] = 1
            c_expr = self.fixup_expr(c.get('expr', ''))

            found = False
            for r in result:
                r_expr = self.fixup_expr(r.get('expr', ''))
                if (r['__call__'] == c['__call__'] and
                    c_expr == r_expr and
                    c.get('types') == r.get('types')):
                    found = True
                    break

            if not found:
                result.append(c)
            else:
                try:
                    self.update_accum(r, c)
                except ValueError: # Cannot merge
                    result.append(c)

        return result

    def recurse(self, outfile, d, parent=None):
        self.node_id += 1
        me = self.node_id

        call = d['__call__']
        ncalls = d.get('__ncalls__', 1)
        cumtime = d.get('__time__', None)
        if cumtime is None or not isinstance(cumtime, float):
            return
        if self.total:
            cumtime_pct = (cumtime / self.total) * 100
            if cumtime_pct < self.cutoff:
                return
        else:
            cumtime_pct = 0

        # Calculate individual time by subtracting child times
        selftime = cumtime
        for child in d['{calls}']:
            childtime = child.get('__time__', None)
            if childtime and isinstance(childtime, float):
                selftime -= childtime
        if self.total:
            selftime_pct = (selftime / self.total) * 100
        else:
            selftime_pct = 0

        outfile.write('N%d\n' % me)
        self_color = self.colorcode(selftime_pct)
        cum_color = self.colorcode(cumtime_pct)

        if ncalls != 1:  # Use stacked polygons?
            call = '%s [%d X]' % (call, ncalls)

        def fmt_time(t):
            return ('%.2fs' % t) if t > 1 else '%.2fms' % (t*1000)

        outfile.write(r'[label="%s\n' % call)

        # Extra annotation
        expr = d.get('expr')
        # Additional escaping of expr?  backslashes?
        if expr:
            outfile.write(self.fixup_expr(expr))
            outfile.write(r'\n')

        types = d.get('types')
        if types:
            outfile.write(r'%s\n' % str(tuple(t['class'] for t in types)))

        outfile.write(
            r'%s (%.2f%%) self\n%s (%.2f%%) cumulative"' %  # ends " started in label=
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
        if self.collapse:
            children = self.collapse_children(children)
            d['{calls}'] = children

        for child in children:
            self.recurse(outfile, child, me)

    def write_header(self, outfile):
        try:
            meminfo = open('/proc/meminfo').readline().split()
            if meminfo[0] == 'MemTotal:' and meminfo[2] == 'kB':
                meminfo = int(meminfo[1]) / (1048576.)  # Convert kB to GB
            else:
                meminfo = None
        except:
            meminfo = None

        # Header data will be wrong if trace2dot runs on a different host than
        # the data was captured on.  Perhaps we should include this info in trace
        outfile.write('digraph "%s" {\n' % self.title)
        outfile.write('label="%s\\n%s\\nPython %s\\n%s: %s' %  # Open quote
              (self.title,
               time.ctime(self.timestamp),
               platform.python_version(),
               platform.node(),
               platform.processor()))
        if meminfo:
            outfile.write(r'\n%.1fGB' % meminfo)

        outfile.write('"\nlabelloc=top\n')  # Close quotes in label

    def write_footer(self, outfile):
        outfile.write('}')


if __name__ == '__main__':
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

    c = Converter(title, cutoff, collapse)
    c.read_trace_file(infile)
    c.write_svg(outfile)
