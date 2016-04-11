from collections import defaultdict
from contextlib import contextmanager
import os
thisdir = os.path.abspath(os.path.dirname(__file__))
from threading import local as _threadlocal
import time

enabled = os.environ.get("SILHOUETTE_ENABLE") is not None


class Tagger(_threadlocal):
    """A thread-local object for selectively recording times in groups.

    This is not for detailed profiling (use the cprofile decorator for that)
    but instead allows multiple functions to be treated as a single component,
    delivering a higher-level view of where time is being spent. This allows
    the recorded times to be more lightweight and easier to pass upward
    to higher applications.
    """

    tags = set()

    def __init__(self):
        self.clear()

    def clear(self):
        """Remove all attributes of self."""
        self.__dict__.clear()
        self.tag_times = defaultdict(list)
        self.seen_tags = set()

    def execute(self, *tags):
        """Return a function decorator which records times by tag.

        You may use this as a decorator to record the timing of any
        arbitrary function or method:

            tagger = Tagger()

            @tagger.execute("database", "debug")
            def do_stuff():
                do_other_stuff()

        The tags determine which functions will be timed and which will not.
        If any submitted tag is present in self.tags at the time the function
        is called, the function will be timed and added to the call stack.
        Using multiple tags allows applications to turn on all "database"
        functions or all "debug" functions and have their times aggregated.

        Nested calls with the same tag are ignored, on the assumption that
        the outermost time includes any inner times.
        """

        if not enabled:
            def noop(func):
                return func
            return noop

        tags = set(tags)

        def decorator(func):

            def execute_wrapper(*args, **kwargs):
                if self.tags.isdisjoint(tags):
                    # No tag matches. Do not time.
                    return func(*args, **kwargs)

                new_tags = tags - self.seen_tags
                self.seen_tags |= new_tags

                start = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed = time.time() - start

                    self.seen_tags -= new_tags

                    # Note that we emit all tags even if not in self.tags
                    for tag in tags - self.seen_tags:
                        self.tag_times[tag].append(elapsed)

            execute_wrapper.__name__ = func.__name__
            return execute_wrapper
        return decorator

    @contextmanager
    def tag(self, *tags):
        tags = set(tags)
        if enabled and not self.tags.isdisjoint(tags):
            new_tags = tags - self.seen_tags
            self.seen_tags |= new_tags

            start = time.time()
            try:
                yield
            finally:
                elapsed = time.time() - start

                self.seen_tags -= new_tags

                # Note that we emit all tags even if not in self.tags
                for tag in tags - self.seen_tags:
                    self.tag_times[tag].append(elapsed)
        else:
            yield

    def pretty(self, total_time=None):
        """Return a list of lines of pretty output."""
        fmt = "  ".join([
            "%(pct)6.2f", "%(total)8.6f", "%(count)6d",
            "%(min)8.6f", "%(avg)8.6f", "%(max)8.6f",
            "%(tag)s"])

        dsu = [(sum(ts), ts, tag) for tag, ts in self.tag_times.iteritems()]
        if total_time is None:
            total_time = max([ttl for ttl, times, atag in dsu] + [0.0])

        lines = []
        for ttl, times, atag in sorted(dsu):
            lines.append(fmt % {
                "tag": atag, "total": ttl, "count": len(times),
                "min": min(times), "max": max(times),
                "avg": (ttl / len(times)),
                "pct": ((ttl / total_time) * 100) if total_time else 0.0
            })

        lines.append("   Pct  Total      Count  Min       Avg       Max       Tag")
        lines.reverse()

        return lines
