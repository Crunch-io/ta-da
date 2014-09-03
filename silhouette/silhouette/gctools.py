import gc
import inspect
import sys

from silhouette.dotfile import DotGraph


class ReferrerTree(object):
    """An object which gathers all referrers of an object to a given depth."""

    peek_length = 40

    def __init__(self, ignore=None, maxdepth=2, maxparents=10):
        self.ignore = ignore or []
        self.ignore.append(inspect.currentframe().f_back)
        self.maxdepth = maxdepth
        self.maxparents = maxparents

    def ascend(self, obj, depth=1):
        """Return a nested list containing referrers of the given object."""
        depth += 1

        # Gather all referrers in one step to minimize
        # cascading references due to repr() logic.
        refs = gc.get_referrers(obj)
        self.ignore.append(refs)
        if len(refs) > self.maxparents:
            return [("[%s referrers]" % len(refs), [])]

        parents = []
        self.ignore.append(parents)

        try:
            ascendcode = self.ascend.__code__
        except AttributeError:
            ascendcode = self.ascend.im_func.func_code
        for parent in refs:
            if inspect.isframe(parent) and parent.f_code is ascendcode:
                continue
            if parent in self.ignore:
                continue
            if depth <= self.maxdepth:
                node = (parent, self.ascend(parent, depth))
            else:
                node = (parent, [("(%s others)" % len(gc.get_referrers(parent)), [])])
            self.ignore.append(node)
            parents.append(node)

        return parents

    def peek(self, s):
        """Return s, restricted to a sane length."""
        if len(s) > (self.peek_length + 3):
            half = self.peek_length // 2
            return s[:half] + '...' + s[-half:]
        else:
            return s

    format_separator = " "

    def _format(self, obj, descend=True):
        """Return a string representation of a single object."""
        if inspect.isframe(obj):
            filename, lineno, func, context, index = inspect.getframeinfo(obj)
            return "<frame of function '%s'>%s(%s:%s)" % (
                func, self.format_separator, filename, lineno
            )
        if obj is vars(sys):
            return "vars(sys)"

        if not descend:
            return self.peek(repr(obj))

        SEP = "," + self.format_separator
        if isinstance(obj, dict):
            return "{" + SEP.join(["%s: %s" % (self._format(k, descend=False),
                                               self._format(v, descend=False))
                                   for k, v in obj.items()]) + "}"
        elif isinstance(obj, list):
            return "[" + SEP.join([self._format(item, descend=False)
                                   for item in obj]) + "]"
        elif isinstance(obj, tuple):
            return "(" + SEP.join([self._format(item, descend=False)
                                   for item in obj]) + ")"

        r = self.peek(repr(obj))
        if isinstance(obj, (str, int, float)):
            return r
        return "%s: %s" % (type(obj), r)

    def format(self, tree):
        """Return a list of string reprs from a nested list of referrers."""
        output = []

        def ascend(branch, depth=1):
            for parent, grandparents in branch:
                output.append(("    " * depth) + self._format(parent))
                if grandparents:
                    ascend(grandparents, depth + 1)
        ascend(tree)
        return output

    def write_dot(self, title, outfile, tree):
        refdot = ReferrerDot(title)
        refdot.tree = self
        self.format_separator = "\\n"
        refdot.write_dot(outfile, tree)


class ReferrerDot(DotGraph):
    """A .dot graph for a ReferrerTree."""

    def node_params(self, node):
        """Return a dict of .dot params for the given node."""
        parent, grandparents = node
        return {
            "label": self.tree._format(parent)
        }

    def node_children(self, node):
        """Return an iterable of child nodes for the given node."""
        parent, grandparents = node
        return grandparents


def get_instances(cls):
    return [x for x in gc.get_objects() if isinstance(x, cls)]


def type_counts():
    objs = {}
    for obj in gc.get_objects():
        t = type(obj)
        if t not in objs:
            objs[t] = 0
        objs[t] += 1
    return objs
