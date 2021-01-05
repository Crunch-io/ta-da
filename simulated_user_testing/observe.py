# Originally copied from zz9/zz9lib/src/zz9lib/observe.py
"""Tracing subsystem for Crunch projects.

The `Tracer` class is the primary interface for this functionality,
and typically requires calls at three different levels of your code.

First, when you start your service, you need to initialize the tracer with
some configuration details. Instantiate a Tracer and import that instance
everywhere you need it.

    tracer = Tracer(collect_times=True, profit=True)

Passing `profit=False` will disable the legacy "silhouette" tracing subsystem
(that subsystem and this option will be removed in a future release).

Next, initialize Honeycomb and/or Datadog APM with either or both
of the following commands:

    tracer._init_honeycomb(
        writekey="<Honeycomb API Key>",  # see pow
        dataset="API",
        service_name="worker" if is_worker else "API",
        sample_rate=250,
        system=conf.get("SYSTEM", "unknown"),
    )

    tracer._init_datadog(
        service_name="worker" if is_worker else "API",
        system=hconf.get("SYSTEM", "unknown"),
    )

Second, wrap each request (task, script execution, or whatever the "top level"
of your service is) with a call to `start_trace` and, in a finally: block or
some other guaranteed way, a call to `finish_trace`:

    tracer.start_trace(
        "api.request",  # name of the top-level span
        trace_id=request_id,
        hc_parent_id=hc_parent_id,
        dd_parent_id=dd_parent_id,
        emit=emit,
    )
    try:
        handle_request()
    finally:
        tracer.finish_trace()

The name of the top-level span is required. You then have some options:
  * If the request is truly the top level, generate a trace_id via uuid
    or some other means and pass it.
  * If the request is potentially being called by some other service,
    pass the trace_id of the caller and the "parent ids" of the span
    in the caller which is calling this nested service. These fields
    may be passed in a variety of ways.

Next, you may control which traces are emitted. Both Honeycomb and Datadog APM
provide random sampling, but this is per span, not per trace. To unequivocally
emit a certain trace pass `emit=True`, or `emit=False` to not emit any spans
for this request. For example, you might pass `emit=True` for any request which
is being called from another service, on the agreement that the calling service
only passes span ids when has decided to emit spans for the entire trace.
If `emit` is None (the default), then the trace is emitted by random sample
according to the tracer's sample_rate.

Finally, for each region in your code where you want a separate nested span,
use the `tracer` contextmanager. In general, you only need to pass a span name.

    with tracer.tracer(span_name):
        value = do_stuff()
        tracer.add_context({"param": value})

You can add fields to the span via `add_context`.
"""
from contextlib import contextmanager
import datetime
from functools import wraps
import inspect
import random
import threading
import time
import uuid

import beeline
from libhoney import transmission
import ddtrace
from ddtrace import context as ddcontext
from ddtrace.ext import SpanTypes
from resource import getrusage, RUSAGE_SELF
import six

# from silhouette.profit import Profit


class FakeStatsD:
    def StatsClient(self, *args, **kwargs):
        return self

    def gauge(self, *args, **kwargs):
        pass

    incr = gauge


transmission.statsd = FakeStatsD()


omitted = object()


def call_repr(frame):
    try:
        co = frame.f_code
        return "%s (%s:%s)" % (
            co.co_name,
            co.co_filename.split("/")[-1],
            frame.f_lineno,
        )
    except AttributeError:
        return "<unknown>"


class Calls:
    def __init__(self, tracer):
        # Yes, this is a circular reference, but should be only one per app.
        self.tracer = tracer

    def __getitem__(self, key):
        return self.tracer.tracer(key)


class TracingThreadContext(threading.local):
    """A thread-local context for managing the behavior of tracing."""

    # When False, the current thread will not be traced.
    emit = False

    # When True, the current span will be discarded by honeycomb or datadog
    discard = False

    # Any spans shorter than this number of seconds will be consolidated.
    consolidate_time = 0
    # While consolidating, this will be a dict of {span name: [info, ...]} pairs.
    consolidations = None

    # Inside a trace, a dict with info about the root span.
    root = None


class Tracer:

    _thread_ctx = TracingThreadContext()

    _profit = None

    _beeline = None
    _sample_rate = 1
    _minimum_span_time = 0.001
    _stack_height = 3

    _ddtracer = None
    _ddservice = None
    _ddspantype = None
    _ddspantypes = {
        # More would need to be done here if we adopted DDAPM
        "API": SpanTypes.WEB,
        "zz9": "db",
        "mongodb": "db",
        "worker": SpanTypes.WORKER,
    }

    def __init__(self, collect_times=True, profit=True):
        self.calls = Calls(self)
        if profit:
            # self._profit = Profit(collect_times=collect_times)
            raise NotImplementedError("silhouette.Profit not supported")

    def _init_honeycomb(
        self,
        writekey,
        dataset,
        service_name,
        sample_rate=1,
        transmission_impl=None,
        **fields
    ):
        self._sample_rate = sample_rate
        self._beeline = beeline.Beeline(
            writekey=writekey,
            dataset=dataset,
            service_name=service_name,
            sampler_hook=self._honeycomb_sampler_hook,
            debug=False,
            transmission_impl=transmission_impl,
        )
        self._beeline.client.add(fields)

    def _honeycomb_sampler_hook(self, fields):
        keep = self.emit_honeycomb and not self._thread_ctx.discard
        new_rate = self._sample_rate
        return keep, new_rate

    @property
    def emit_honeycomb(self):
        if self._beeline is None:
            return False
        return self._thread_ctx.emit

    def _init_datadog(self, service_name, **fields):
        self._ddtracer = ddtrace.tracer
        self._ddtracer.configure(hostname="localhost")
        self._ddservice = service_name
        self._ddspantype = self._ddspantypes.get(service_name, None)
        self._ddtracer.set_tags(fields)

    @property
    def emit_datadog(self):
        if self._ddtracer is None:
            return False
        return self._thread_ctx.emit

    @contextmanager
    def tracer(
        self, name, trace_id=None, parent_id=None, consolidate_time=None, rss_diff=False
    ):
        """Yield, wrapped in a new span.

        If `consolidate_time` is not None, then all spans inside this span
        which do not take at least the given amount of seconds will be
        consolidated into a single span at the end of this span. This helps
        traces that make the same call many times in a loop (such as locks)
        avoid being overwhelmed with hundreds or thousands of nearly-identical
        spans.
        """
        # Two f_back's because the first is just our @contextmanager
        caller = inspect.currentframe().f_back.f_back
        stack = [call_repr(caller)]
        for i in range(self._stack_height - 1):
            caller = getattr(caller, "f_back")
            if caller is None:
                break
            stack.append(call_repr(caller))

        with self._maybe_trace_profit(name, trace_id, parent_id):
            with self._maybe_trace_datadog(name):
                with self._maybe_trace_honeycomb(name, trace_id, parent_id):
                    self.add_context({"stack": ", ".join(reversed(stack))})
                    with self._maybe_consolidate(name, consolidate_time):
                        if rss_diff:
                            prev = getrusage(RUSAGE_SELF).ru_maxrss
                            try:
                                yield
                            finally:
                                diff = getrusage(RUSAGE_SELF).ru_maxrss - prev
                                self.add_context({"RSS_diff": diff * 1000})
                        else:
                            yield

    @contextmanager
    def _maybe_consolidate(self, name, new_consolidate_time=None):
        ctx = self._thread_ctx
        old_consolidations = None
        old_consolidation_time = None
        if new_consolidate_time is not None:
            # New consolidation context requested.
            # Stash any ongoing consolidations.
            old_consolidations = ctx.consolidations
            old_consolidation_time = ctx.consolidate_time
            ctx.consolidations = {}
            ctx.consolidate_time = new_consolidate_time

        start = time.time()
        try:
            yield
        finally:
            ctx.discard = False
            if new_consolidate_time is not None:
                # This span requested consolidation;
                # don't consolidate it, and don't discard it
                # (or its children will have no parent).
                # Do, however, record everything consolidated under it.
                for name, info in six.iteritems(ctx.consolidations):
                    info["data"].pop("name", None)
                    self.record_call(
                        name,
                        # Record the sum of elapsed. This means
                        # the "finish time" will be inaccurate,
                        # but engineers will care more about total
                        # time taken for all calls than start/end.
                        elapsed=info["elapsed"],
                        start_time=info["start"],
                        calls=info["count"],
                        **info["data"]
                    )
                ctx.consolidations = old_consolidations
                ctx.consolidate_time = old_consolidation_time
            else:
                elapsed = time.time() - start
                if elapsed < self._minimum_span_time:
                    # Discard, but don't consolidate.
                    ctx.discard = True
                elif elapsed < ctx.consolidate_time:
                    # Consolidate this span with others like it.
                    ctx.discard = True
                    bucket = ctx.consolidations.get(name)
                    if bucket is None:
                        ctx.consolidations[name] = bucket = {
                            "start": start,
                            "elapsed": elapsed,
                            "count": 1,
                            "data": {},
                        }
                        if self.emit_honeycomb:
                            span = self._beeline.tracer_impl.get_active_span()
                            if span is not None:
                                bucket["data"] = span.event._fields._data.copy()
                    else:
                        bucket["elapsed"] += elapsed
                        bucket["count"] += 1
                        if self.emit_honeycomb:
                            # Drop any fields from our bucket if this
                            # span has different values for them.
                            # In this way, we only keep values
                            # common to all consolidated spans.
                            span = self._beeline.tracer_impl.get_active_span()
                            if span is not None:
                                new_data = span.event._fields._data
                                for k, v in list(six.iteritems(bucket["data"])):
                                    if new_data.get(k, omitted) != v:
                                        del bucket["data"][k]

    @contextmanager
    def _maybe_trace_profit(self, name, trace_id=None, parent_id=None):
        if self._profit is None:
            yield
        else:
            with self._profit.calls[name]:
                yield

    @contextmanager
    def _maybe_trace_datadog(self, name, trace_id=None, parent_id=None):
        if self.emit_datadog:
            with self._ddtracer.trace(name) as current_span:
                yield
                if self._thread_ctx.discard:
                    current_span.sampled = False
        else:
            yield

    @contextmanager
    def _maybe_trace_honeycomb(self, name, trace_id=None, parent_id=None):
        if self.emit_honeycomb:
            with self._beeline.tracer(
                name=name, trace_id=trace_id, parent_id=parent_id
            ):
                yield
        else:
            yield

    def start_trace(
        self, name, trace_id=None, hc_parent_id=None, dd_parent_id=None, emit=None
    ):
        """Start a trace."""
        self._thread_ctx.root = root = {"name": name, "start_time": time.time()}
        if self._sample_rate == 1 or emit is True:
            self._thread_ctx.emit = True
        elif self._sample_rate == 0 or emit is False:
            self._thread_ctx.emit = False
        else:
            self._thread_ctx.emit = random.randrange(self._sample_rate) == 0

        if self.emit_honeycomb:
            root["hc_span"] = self._beeline.tracer_impl.start_trace(
                {"name": name}, trace_id=trace_id, parent_span_id=hc_parent_id
            )
            root["hc_span"].event.sample_rate = self._sample_rate

        if self.emit_datadog:
            # Datadog APM requires 64-bit long trace_id's,
            # and chokes if we pass it our UUID string.
            # For now, coerce our hex UUID to int.
            # As long as cr.server and zz9 do it the same way, they should nest.
            if isinstance(trace_id, six.string_types):
                trace_id = int(trace_id[:16], 16)

            ctx = ddcontext.Context(trace_id=trace_id, span_id=dd_parent_id)
            self._ddtracer.context_provider.activate(ctx)
            root["dd_span"] = self._ddtracer.start_span(
                name, child_of=ctx, service=self._ddservice, span_type=self._ddspantype
            )

    def finish_trace(self):
        root = self._thread_ctx.root
        self._thread_ctx.root = None

        if self._profit is not None:
            total_time = time.time() - root["start_time"]
            self._profit.calls[root["name"]].record(total_time)

        if self.emit_honeycomb:
            root_span = root.get("hc_span")
            if root_span is not None:
                self._thread_ctx.discard = False
                self._beeline.tracer_impl.finish_trace(root_span)

        if self.emit_datadog:
            root_span = root.get("dd_span")
            if root_span is not None:
                root_span.finish()

    def add_trace_field(self, name, value):
        """Add name:value to current and all future spans in the current trace."""
        if self.emit_honeycomb:
            self._beeline.tracer_impl.add_trace_field(name, value)
        if self.emit_datadog:
            # There doesn't seem to be a way to make these propagate.
            curspan = self._ddtracer.current_span()
            if curspan is not None:
                curspan.set_tag(name, value)

    def add_context(self, data):
        """Add the given name:value pairs to the current span."""
        if self.emit_honeycomb:
            self._beeline.add(data)

        if self.emit_datadog:
            curspan = self._ddtracer.current_span()
            if curspan is not None:
                # Hacky way to force our fields into Datadog's fixed schema.
                if "command" in data:
                    curspan.resource = data["command"]
                if "controller" in data:
                    curspan.resource = data["controller"]

                # Datadog-specific tag names
                data = data.copy()
                for ourname, ddname in [
                    ("path_info", "http.url"),
                    ("method", "http.method"),
                    ("api_status_code", "http.status_code"),
                    ("query_string", "http.query.string"),
                    ("service_name", "service.name"),
                ]:
                    if ourname in data:
                        data[ddname] = data.pop(ourname)

                curspan.set_tags(data)

    @property
    def active_hc_span_id(self):
        if self._beeline is not None:
            span = self._beeline.tracer_impl.get_active_span()
            if span is not None:
                return span.id

    @property
    def active_dd_span_id(self):
        if self._ddtracer is not None:
            span = self._ddtracer.current_span()
            if span is not None:
                return span.span_id

    def _record_honeycomb(self, created_at=None, **data):
        tracer_impl = self._beeline.tracer_impl
        trace = tracer_impl._trace
        if trace.stack:
            current_span = trace.stack[-1]
            ev = tracer_impl._client.new_event(data=trace.fields)
            if created_at is not None:
                ev.created_at = created_at
            ev.add(
                {
                    "trace.trace_id": trace.id,
                    "trace.parent_id": current_span.id,
                    "trace.span_id": str(uuid.uuid4()),
                }
            )
            if data:
                ev.add(data)
            ev.send_presampled()

    def clear(self):
        if self._profit is not None:
            self._profit.clear()

    def as_dicts(self, calls=None, skip_times=False):
        """Return a dict of {tag: call.__dict__} pairs."""
        if self._profit is not None:
            if isinstance(calls, Calls):
                calls = calls.tracer._profit.calls
            return self._profit.as_dicts(calls=calls, skip_times=skip_times)
        else:
            return {}

    def record_call(self, name, elapsed=None, start_time=None, calls=1, **data):
        """Manually add a span to the current trace.

        Either `start_time` (a time.time) or `elapsed` (a float number of seconds)
        must be provided.
        """
        if start_time is None:
            start_dt = datetime.datetime.now() - datetime.timedelta(seconds=elapsed)
            start_time = time.time() - elapsed
        else:
            start_dt = datetime.datetime.fromtimestamp(start_time)
        if elapsed is None:
            elapsed = (datetime.datetime.now() - start_dt).total_seconds()

        if elapsed > self._minimum_span_time:
            caller = inspect.currentframe().f_back.f_back
            stack = [call_repr(caller)]
            for i in range(self._stack_height - 1):
                caller = getattr(caller, "f_back")
                if caller is None:
                    break
                stack.append(call_repr(caller))
            data["stack"] = ", ".join(reversed(stack))
            if calls != 1:
                data["calls"] = calls

            if self.emit_honeycomb:
                # We would just call trace.start/finish_span here, but honeycomb
                # doesn't provide a way to override the duration_ms that way.
                hc_data = data.copy()
                hc_data.setdefault("created_at", start_dt)
                hc_data.setdefault("name", name)
                hc_data.setdefault("duration_ms", elapsed * 1000.0)
                self._record_honeycomb(**hc_data)

            if self.emit_datadog:
                ctx = self._ddtracer.get_call_context()
                span = self._ddtracer.start_span(
                    name,
                    child_of=ctx,
                    service=self._ddservice,
                    span_type=self._ddspantype,
                )
                span.set_tags(data)
                span.start = start_time
                span.finish(start_time + elapsed)

        if self._profit is not None:
            return self._profit.calls[name].record(elapsed)

    def merge(self, updates):
        """Merge the given dict of {tag: call or call.__dict__} pairs into self."""
        if self._profit is not None:
            return self._profit.merge(updates)

    def pretty(self, total_time=None, calls=None):
        """Return a list of lines of pretty output."""
        if self._profit is not None:
            if isinstance(calls, Calls):
                calls = calls.tracer._profit.calls
            return self._profit.pretty(total_time=total_time, calls=calls)
        else:
            return []

    def decorate(self, tag):
        def _trace_func(f):
            @wraps(f)
            def inner(*args, **kwargs):
                with self.calls[tag]:
                    return f(*args, **kwargs)

            inner.__immediate_wrapped__ = f
            # Update wrapped function, this is only done by functools.wraps on Python3.2+
            while hasattr(f, "__wrapped__"):
                f = f.__wrapped__
            inner.__wrapped__ = f
            return inner

        return _trace_func
