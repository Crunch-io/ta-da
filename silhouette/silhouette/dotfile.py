#!/usr/bin/env python
import os
import platform
from math import sqrt


class DotGraph(object):
    """A helper for writing a tree of things to a .dot file (and then .svg)."""

    header = "%(title)s\\nPython %(pyversion)s\\n%(node)s: %(processor)s"

    def __init__(self, title='trace2dot', header=None):
        self.title = title
        self.color_min = 1

        if header is None:
            header = self.__class__.header
        self.header = header

    def write_dot(self, outfile, tree):
        self.node_id = 0
        self.seen_nodes = []
        self.write_dot_header(outfile)
        self.recurse(outfile, tree)
        self.write_dot_footer(outfile)

    def write_dot_header(self, outfile):
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
        header = self.header % {
            "title": self.title,
            "pyversion": platform.python_version(),
            "node": platform.node(),
            "processor": platform.processor(),
            "mem": ('%.1fGB' % meminfo if meminfo else "?")
        }
        outfile.write('label="%s"\nlabelloc=top\n' % header)

    def write_dot_footer(self, outfile):
        outfile.write('}')

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

    def dotparams(self, params):
        """Return the given params dict in a string of .dot syntax."""
        return ",".join([
            '%s=%s' % (k, '"%s"' % v.replace('"', '\\"') if isinstance(v, basestring) else v)
            for k, v in params.iteritems()
        ])

    detect_repeats = True

    def recurse(self, outfile, node, parent_id=None):
        self.node_id += 1
        curnode = self.node_id

        params = self.node_params(node)
        if params is None:
            return
        params.setdefault("style", "filled")
        params.setdefault("gradientangle", 90)
        params.setdefault("fillcolor", "0 0 1;0.5;0 0 1")

        if self.detect_repeats:
            for node_id, p in self.seen_nodes:
                if p == params:
                    # Don't draw a new node. Instead, if the node has a parent,
                    # draw the connector line to the existing node.
                    if parent_id:
                        outfile.write('N%d -> N%d;\n' % (parent_id, node_id))
                    return

            self.seen_nodes.append((curnode, params))

        outfile.write('N%d [%s]\n' % (curnode, self.dotparams(params)))

        if parent_id:
            outfile.write('N%d -> N%d;\n' % (parent_id, curnode))

        for child in self.node_children(node):
            self.recurse(outfile, child, curnode)

    def node_params(self, node):
        """Return a dict of .dot params for the given node.

        You almost certainly want to override this. You should return
        at least a "label" member containing the text to put in the node.
        """
        return {"label": repr(node)}

    def node_children(self, node):
        """Return an iterable of child nodes for the given node.

        You almost certainly want to override this.
        """
        if isinstance(node, (tuple, list)):
            return node
        return []
