import yaml

from observe import Tracer
import statslib

tracer = Tracer(profit=False)


def init_tracing(
    service_name, sample_rate=1, config_filename="/var/lib/crunch.io/cr.server.conf"
):
    """
    Initialize Datadog and/or Honeycomb stats and tracing.
    Only call this once, at application startup time.
    """
    # See: cr/server/startup/__init__.py:startup()
    with open(config_filename) as f:
        settings = yaml.safe_load(f)
    statslib.statsd.configure(settings["APP_SETTINGS"])
    hconf = settings["APP_SETTINGS"].get("HONEYCOMB", {})
    hkey = hconf.get("API_KEY", "")
    if hkey:
        tracer._init_honeycomb(
            writekey=hkey,
            dataset="API",
            service_name=service_name,
            sample_rate=sample_rate,
            system=hconf.get("SYSTEM", "unknown"),
        )

        tracer._init_datadog(
            service_name=service_name, system=hconf.get("SYSTEM", "unknown")
        )


class PycrunchTracer(object):
    """
    Use an instance of this to add performance tracing to a span of pycrunch
    requests.

    >>> import uuid
    >>> import crunch_util
    >>> trace_id = uuid.uuid4().hex
    >>> crunch_util.patch_pre_http_request(site.session, PycrunchTracer(trace_id))
    """

    def __init__(self, trace_id):
        self.trace_id = trace_id

    def __call__(self, session, method, url, **kwparams):
        header_value = "{}, {}, {}".format(
            self.trace_id, tracer.active_hc_span_id, tracer.active_dd_span_id
        )
        # Uncomment to trace HTTP requests
        # print("{} {} X-Crunch-Tracing: {}".format(method, url, header_value))
        session.headers["X-Crunch-Tracing"] = header_value
