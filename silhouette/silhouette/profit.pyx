from collections import defaultdict
from threading import local as _threadlocal
import time


cdef class Call


cpdef Call Call_from_dict(d):
    c = Call()
    c.min = d.get('min', 0.0)
    c.max = d.get('max', 0.0)
    c.total = d.get('total', 0.0)
    c.count = d.get('count', 0)
    c.recur = d.get('recur', 0)
    return c


cdef record_exit(Call self, double elapsed):
    if self.count == 0:
        self.min = elapsed
        self.max = elapsed
    else:
        if elapsed < self.min:
            self.min = elapsed
        if elapsed > self.max:
            self.max = elapsed
    self.total += elapsed
    self.count += 1


cdef dict Call_as_dict(Call self):
    if self.count == 0:
        return {}
    return {
        "min": self.min, "max": self.max,
        "total": self.total, "count": self.count,
        "recur": self.recur
    }


cdef class Call:

    cdef public double min
    cdef public double max
    cdef public double total
    cdef public int count
    cdef public int recur

    cdef double _start
    cdef int _depth

    as_dict = Call_as_dict

    def __enter__(self):
        if self._depth == 0:
            self._start = time.time()
        self._depth += 1

    def __exit__(self, type, value, traceback):
        cdef double elapsed
        self._depth -= 1
        if self._depth == 0:
            # Only record times for non-recursive calls.
            # If you want to dig into recursiveness, use cProfile.
            elapsed = time.time() - self._start
            record_exit(self, elapsed)
        else:
            self.recur += 1

    record = record_exit


class Profit(_threadlocal):
    """A thread-local object for selectively recording call times.

    This is not for detailed profiling (use the cprofile decorator for that)
    but instead allows multiple functions to be treated as a single component,
    delivering a higher-level view of where time is being spent. This allows
    the recorded times to be more lightweight and easier to pass upward
    to higher applications.
    """

    def __init__(self):
        self.clear()

    def clear(self):
        """Remove all attributes of self."""
        self.calls = defaultdict(Call)

    def as_dicts(self):
        """Return a dict of {tag: call.__dict__} pairs."""
        cdef Call call
        return dict(
            (tag, call.as_dict())
            for tag, call in self.calls.iteritems()
        )

    def merge(self, updates):
        """Merge the given dict of {tag: call or call.__dict__} pairs into self."""
        cdef Call call, selfcall
        for tag, call_info in updates.iteritems():
            t = type(call_info)
            if t is dict:
                call = Call_from_dict(call_info)
            elif t is Call:
                call = call_info
            else:
                raise TypeError("silhouette cannot merge calls of type '%s'." % (t,))

            if call.count:
                selfcall = self.calls[tag]
                if selfcall.count:
                    if call.min < selfcall.min:
                        selfcall.min = call.min
                    if call.max > selfcall.max:
                        selfcall.max = call.max
                    selfcall.total += call.total
                    selfcall.count += call.count
                    selfcall.recur += call.recur
                else:
                    selfcall.min = call.min
                    selfcall.max = call.max
                    selfcall.total = call.total
                    selfcall.count = call.count
                    selfcall.recur = call.recur

    def pretty(self, total_time=None, calls=None):
        """Return a list of lines of pretty output."""
        fmt = "  ".join([
            "%(pct)6.2f", "%(total)8.6f", "%(count)6d",
            "%(min)8.6f", "%(avg)8.6f", "%(max)8.6f",
            "%(tag)s"])

        if calls is None:
            calls = self.calls
        else:
            # Convert to Call objects as needed.
            calls = dict((tag, Call_from_dict(c) if type(c) is dict else c)
                         for tag, c in calls.iteritems())

        cdef Call call
        dsu = []
        for tag, call in calls.iteritems():
            if call._depth > 0:
                # The call is still under way, probably in a separate thread.
                # Record its partial time.
                dsu.append((call.total + (time.time() - call._start), tag,
                           call.count + 1, call.min, call.max, True))
            else:
                dsu.append((call.total, tag, call.count, call.min, call.max, False))
        dsu.sort(reverse=True)

        if total_time is None:
            total_time = max([entry[0] for entry in dsu] + [0.0])

        lines = ["   Pct  Total      Count  Min       Avg       Max       Tag"]
        for total, tag, count, mn, mx, partial in dsu:
            lines.append(fmt % {
                "pct": ((total / total_time) * 100) if total_time else 0.0,
                "total": total,
                "count": count,
                "min": mn,
                "avg": total / count if count else total,
                "max": mx,
                "tag": (tag + "...") if partial else tag
            })

        return lines
