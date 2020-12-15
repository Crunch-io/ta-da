# Copied from zz9lib/statslib.py
"""Utilities to gather metrics about the system in Datadog."""
import math
import os
import inspect

import datadog
from datadog.dogstatsd.base import DogStatsd
import diagnose

from functools import wraps
import six


def is_enabled(func):
    @wraps(func)
    def wrapped_enabled(self, *a, **kw):
        if self.is_enabled:
            return func(self, *a, **kw)
        else:
            return None

    return wrapped_enabled


def wrap_methods_with_enabled_check(cls):
    WRAP = set(["_report", "event", "service_check", "_send", "get_socket"])

    for name, member in inspect.getmembers(cls, inspect.isroutine):
        if name in WRAP:
            setattr(cls, name, is_enabled(member))
    return cls


@wrap_methods_with_enabled_check
class CrunchStatsD(DogStatsd):
    is_enabled = None

    """
    A value between 0 (disabled) and 1.0 (no sampling) indicating the sampling ratio
    """
    sample_rate = 0
    default_host = "localhost"
    default_port = 8125
    buffer = None
    socket = None

    def __init__(self, host="localhost", port=8125, max_buffer_size=50):
        enabled = os.environ.get("CR_SEND_TO_DATADOG", "false")

        if enabled and not enabled.lower() in ["f", "false", "0", "no", "off", "none"]:
            self.is_enabled = True
        else:
            self.is_enabled = False

        super(CrunchStatsD, self).__init__(host, port, max_buffer_size)

    def enable(self):
        if not self.is_enabled:
            # Set this first, or the connect request below will be bypassed
            self.is_enabled = True
            self.get_socket()

    def disable(self):
        if self.is_enabled:
            if self.buffer:
                self.close_buffer()
            self._send = self._send_to_server

            self.close_socket()
        self.is_enabled = False

    def configure(self, config):
        """
        Given a zz9config object or a cr.lib.settings.settings.APP_SETTINGS object, set
        up statsd appropriately.
        """
        enable = config.get("dogstatsd", False)

        if enable or [
            v.get("dogstatsd", False)
            for k, v in six.iteritems(config)
            if k.startswith("zone_")
        ]:
            self.enable()
        else:
            self.disable()

        sample_rate = config.get("dogstatsd_sample_rate", 1.0)
        self.default_sample_rate = min(
            sample_rate,
            min(
                [
                    v.get("dogstatsd_sample_rate", 1.0)
                    for k, v in six.iteritems(config)
                    if k.startswith("zone_")
                ]
                or [1.0]
            ),
        )


statsd = CrunchStatsD()
# We also have to replace dstatsd.statsd becase it's imported by sillhouette at least,
# and maybe more
datadog.statsd = statsd
datadog.dogstatsd.statsd = statsd
datadog.dogstatsd.base.statsd = statsd
diagnose.instruments.statsd = statsd

__all__ = ["statsd", "log_tag", "meta"]

meta = {"zz9num": "unknown-zz9", "zz9zone": "unknown-zone"}


def log_tag(name, n):
    """Prepare a tag with log10 value for a metric reported to Datadog.

    The value is reported as a rounded base10 logarithm to bucket the reported
    values in a set of relatively smaller group of buckets. Otherwise we would
    report so many different minor tags that they would be useless as nothing
    would fit into the same group.
    """
    return "{}:{}".format(name, int(math.ceil(math.log10(n))) if n > 0 else 0)
