"""A library for selectively tracing execution.

Traditional profiling in Python is performed by hooking into the function
call machinery so that every call is timed; occasionally, a tool will
allow certain functions or modules to be ignored. The forest is often
lost for the trees. Silhouette operates selectively instead, allowing
you to focus on the important concepts in your domain. You can:

 * Add function decorators or context managers to your code to get a
   context-rich call graph, complete with timings.
 * Annotate any call node with arbitrary metadata, to help explain
   why you received the results you did.
 * Print calls as they execute and/or collect them for later analysis.
 * Return silhouette call graphs from other services and integrate
   them into your local graph. Distributed tracing ftw!

Due to overhead, silhouette is disabled by default.
To enable, the environment variable SILHOUETTE_ENABLE must be set.

See the script 'trace2dot.py' in the tools repo for a post-processor
which creates a graphical representation.
"""

from copy import deepcopy
import os
import sys
from threading import local as _threadlocal
import time

try:
    import simplejson as json
except ImportError:
    import json

enable = (os.environ.get("SILHOUETTE_ENABLE") is not None)


class Context(object):
    """A call context for tracing execution.

    You may use this as a context manager to record the execution of any
    arbitrary block of code:

        from silhouette import trace

        with trace.context("big operation"):
            do_stuff()
            do_other_stuff()

        trace.report()
    """

    def __init__(self, call):
        self.callpoint = {
            "__call__": call,
            "__time__": None,
            "{calls}": [],
        }

    def __enter__(self):
        if trace.logger:
            trace.logger.debug("tracing %s" % self.callpoint["__call__"])

        self.old_execution = trace.execution
        self.old_callpoint = trace.callpoint
        trace.execution = self.callpoint["{calls}"]
        trace.callpoint = self.callpoint
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time

        self.callpoint["__time__"] = elapsed
        self.old_execution.append(self.callpoint)
        trace.execution = self.old_execution
        trace.callpoint = self.old_callpoint

        if trace.logger:
            # Log any extension attributes first
            for k, v in self.callpoint.iteritems():
                if k in ("__time__", "__call__", "{calls}"):
                    continue
                v = repr(v)[:80]
                trace.logger.debug("tracing %s: %s=%s" %
                                   (self.callpoint["__call__"], k, v))
            # Then log the elapsed time
            trace.logger.debug("tracing %s: done in %0.3f" %
                               (self.callpoint["__call__"], elapsed))

class Noop:
    def __setitem__(self, key, val):
        pass

class Trace(_threadlocal):
    """A thread-local stack for tracing execution."""

    context = Context
    # You may replace this with a class-level attribute for a combined log,
    # or one for each thread for separate logs, as you desire.
    logger = None

    def __init__(self):
        self.execution = []
        self.callpoint = None if enable else Noop()

    def __nonzero__(self):
        # Allows clients to test 'if trace'
        return enable

    def clear(self):
        """Remove all attributes of self."""
        self.__dict__.clear()
        self.execution = []
        self.callpoint = None if enable else Noop()

    def execute(self, call=None):
        """Return a function decorator with timing/execution recording.

        You may use this as a decorator to record the execution of any
        arbitrary function or method:

            from silhouette import trace

            @trace.execute()
            def do_stuff():
                do_other_stuff()

        If the 'call' argument is omitted or None, the name of
        the decorated function will be used as the name of the call.
        """
        def decorator(func):
            if not enable:
                return func

            def execute_wrapper(*args, **kwargs):
                icall = call
                if icall is None:
                    # Assume the func is an instancemethod
                    # and the first arg is therefore 'self'
                    # (or a classmethod and therefore 'cls')
                    if args:
                        firstarg = args[0]
                        clsname = getattr(firstarg, "__name__",
                                          firstarg.__class__.__name__)
                        icall = "%s.%s" % (clsname, func.__name__)
                    else:
                        icall = "%s.%s" % (func.__module__, func.__name__)

                with Context(icall):
                    return func(*args, **kwargs)

            return execute_wrapper
        return decorator

    def click(self, call):
        """Add a callpoint with the time since the last callpoint (or 0)."""
        if not enable:
            return
        c = time.time()
        try:
            t = c - self.execution[-1]["click"]
        except (KeyError, IndexError):
            t = 0
        self.execution.append({
            "__call__": call,
            "click": c,
            "__time__": t,
            "{calls}": [],
            })

    def prune(self, threshold=1.0):
        """Remove any calls from self less than the given time (in seconds)."""
        if not enable:
            return
        self.execution = prune_calls(self.execution, threshold)

    def format(self, indent='  ', pct=False):
        """Return self.execution in a pretty format."""
        if not enable:
            return
        return format_calls(self.execution, indent=indent, pct=pct)

    def report(self, indent='  ', pct=False, stream=sys.stdout):
        """Write the trace as JSON to the given stream."""
        if not enable:
            return
        stream.write("\nExecution trace ===================================\n")
        stream.flush()
        stream.write(self.format(indent, pct))
        stream.flush()
        stream.write("\n===================================================\n")
        stream.flush()

    def save(self, file):
        """Write trace (as python pickle) for post-processing by other programs (e.g. trace2dot)"""
        if not enable:
            return
        import cPickle
        cPickle.dump(self.execution, file, protocol=2)

    def write_svg(self, title, path):
        from silhouette import trace2dot

        c = trace2dot.Converter(title)
        c.data = self.execution
        c.write_svg(path)


def prune_calls(calls, threshold=1.0):
    """Remove any calls less than the given time (in seconds)."""
    if not enable:
        return
    calls = [c for c in calls if c.get("__time__", 0) >= threshold]
    for c in calls:
        if "{calls}" in c:
            c["{calls}"] = prune_calls(c["{calls}"], threshold)
    return calls


def format_calls(calls, indent='  ', pct=False):
    """Return the given calls as a JSON-formatted string.

    The 'indent' argument will be passed through to json.dumps.
    If the 'pct' argument is True, all "__time__" members (which are
    floating-point seconds) will be replaced with percent strings.
    """
    if not enable:
        return
    if pct:
        total = sum([c.get("__time__", 0.0) for c in calls] + [0.0])
        if total:
            def munge(calls):
                for c in calls:
                    t = c.get("__time__", None)
                    if t is not None:
                        c["__time__"] = str(int((t / total) * 10000) / 100.0) + "%"
                        inner = c.get("{calls}", None)
                        if inner:
                            munge(inner)
            calls = deepcopy(calls)
            munge(calls)
            return json.dumps(calls, sort_keys=True, indent=indent)

    return json.dumps(calls, sort_keys=True, indent=indent)


trace = Trace()