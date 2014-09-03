#!/usr/bin/env python
import sys
import os
import time
import re
import argparse
import cPickle

from . import dotfile


class Converter(dotfile.DotGraph):

    def __init__(self, title='trace2dot', cutoff=0.1, collapse=False):
        self.cutoff = cutoff
        self.collapse = collapse
        self.data = None

        dotfile.DotGraph.__init__(self, title)

    def read_trace_file(self, infile):
        timestamp = time.ctime(os.fstat(infile.fileno()).st_ctime)
        self.header = "%(title)s\\n" + timestamp + "\\nPython %(pyversion)s\\n%(node)s: %(processor)s"
        self.data = cPickle.load(infile)
        self.total = self.get_total()
        #infile.close()

    def get_total(self):
        return sum([float(c.get("__time__", 0.0)) for c in self.data] + [0.0])

    def write_dot(self, outfile):
        head_node = {
            "__call__": self.title,
            "__time__": self.total,
            "{calls}": self.data,
        }
        dotfile.DotGraph.write_dot(self, outfile, head_node)

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

            if k == '__time__':  # Hack b/c serialize times can be reported as string type
                if isinstance(b[k], basestring):
                    b[k] = float(b[k])
                if k in a and isinstance(a[k], basestring):
                    a[k] = float(a[k])

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
                if (
                    r['__call__'] == c['__call__'] and
                    c_expr == r_expr and
                    c.get('types') == r.get('types')
                ):
                    found = True
                    break

            if not found:
                result.append(c)
            else:
                try:
                    self.update_accum(r, c)
                except ValueError:  # Cannot merge
                    result.append(c)

        return result

    def node_params(self, node):
        """Return a dictionary of .dot params for the given node."""
        params = {}

        # ---------------------------- Fillcolor ---------------------------- #

        cumtime = node.get('__time__', None)
        if cumtime is None:
            return
        if not isinstance(cumtime, float):
            cumtime = float(cumtime)

        total = self.total
        if total:
            cumtime_pct = (cumtime / total) * 100
            if cumtime_pct < self.cutoff:
                return
        else:
            cumtime_pct = 0

        # Calculate individual time by subtracting child times
        selftime = cumtime
        for child in node['{calls}']:
            childtime = child.get('__time__', None)
            if childtime:
                selftime -= float(childtime)
        if total:
            selftime_pct = (selftime / total) * 100
        else:
            selftime_pct = 0

        self_color = self.colorcode(selftime_pct)
        cum_color = self.colorcode(cumtime_pct)

        if self_color or cum_color:
            params["fillcolor"] = "%s;0.5:%s" % (cum_color, self_color)

        # --------------------------- Node Label --------------------------- #

        call = node['__call__']
        ncalls = node.get('__ncalls__', 1)
        if ncalls != 1:  # Use stacked polygons?
            call = '%s [%d X]' % (call, ncalls)
        label = '"%s\n' % call

        # Extra annotation
        expr = node.get('expr')
        # Additional escaping of expr?  backslashes?
        if expr:
            label += self.fixup_expr(expr) + r'\n'

        types = node.get('types')
        if types:
            label += r'%s\n' % str(tuple(t['class'] for t in types))

        def fmt_time(t):
            return ('%.2fs' % t) if t > 1 else '%.2fms' % (t*1000)

        label += (
            r'%s (%.2f%%) self\n%s (%.2f%%) cumulative"' %  # ends " started in label=
            (
                fmt_time(selftime), selftime_pct,
                fmt_time(cumtime), cumtime_pct,
            )
        )

        params["label"] = label

        return params

    def node_children(self, node):
        """Return an iterable of child nodes for the given node."""
        children = node['{calls}']
        if self.collapse:
            children = self.collapse_children(children)
            node['{calls}'] = children
        return children


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
    args = parser.parse_args()
    cutoff = float(args.cutoff)
    title = args.title
    collapse = not args.no_collapse
    infile = args.infile
    outfile = args.outfile

    c = Converter(title, cutoff, collapse)
    c.read_trace_file(infile)
    c.write_dot(outfile)
