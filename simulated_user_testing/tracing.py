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
