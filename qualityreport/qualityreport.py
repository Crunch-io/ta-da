# Results from api.Metric.query are of the form: {
#     'status': 'ok',
#     'res_type': 'time_series',
#     'resp_version': 1,
#     'series': [
#         {
#             'start': 1566942720000,
#             'end': 1566946299000,
#             'display_name': 'cr.server.request.time.ms.count',
#             'metric': 'cr.server.request.time.ms.count',
#             'interval': 20,
#             'length': 179,
#             'query_index': 0,
#             'aggr': 'sum',
#             'attributes': {},
#             'expression': 'sum:cr.server.request.time.ms.count{controller:deckcatalogcontroller,method:get,slow:yes,system:eu}.as_count().rollup(sum)',
#             'scope': 'controller:deckcatalogcontroller,method:get,slow:yes,system:eu',
#             'unit': None,
#             'pointlist': [
#                 [1566942720000.0, None],
#                 [1566942740000.0, None],
#                 ...
#                 [1566945380000.0, 1.0],
#                 [1566946260000.0, None],
#                 [1566946280000.0, None]
#             ]
#         }, {
#             ...
#         }
#     ],
#     'from_date': 1566942705000,
#     'group_by': ['controller', 'method'],
#     'to_date': 1566946305000,
#     'query': 'sum:cr.server.request.time.ms.count{system:eu,slow:yes} by {controller,method}.as_count().rollup(sum)',
#     'message': u''
# }

from collections import defaultdict
import contextlib
import datetime
import json
import time
import traceback

import requests

from datadog import api, initialize

initialize(
    api_key="bdbf2191a6a706ef474615b6a3d01ba0",
    app_key="7a0ef450a46d698982aa376a4003423101e15549",
)
api._timeout = 3
api._backoff_period = 3

NOW = time.time()
ONE_WEEK_AGO = NOW - (86400 * 7)
ONE_MINUTE_OF_MS = 60 * 1000
ONE_HOUR_OF_MS = ONE_MINUTE_OF_MS * 60
K = 1000
M = 1000 * K
G = 1000 * M


def get_weekly_series(q):
    return api.Metric.query(start=int(ONE_WEEK_AGO), end=int(NOW), query=q)["series"]


def friendly_count(num):
    if num >= G:
        return "%dG" % (num / G)
    if num >= M:
        return "%dM" % (num / M)
    if num >= K:
        return "%dK" % (num / K)
    return "%d" % num


def friendly_pct(pct):
    if pct == 0:
        return ""
    if pct < 1:
        return "%.2f%%" % pct
    return "%d%%" % pct


def friendly_duration(ms):
    if ms > ONE_HOUR_OF_MS:
        return "%d h" % (ms / ONE_HOUR_OF_MS)
    if ms > ONE_MINUTE_OF_MS:
        return "%d m" % (ms / ONE_MINUTE_OF_MS)
    if ms > 1000:
        return "%d s" % (ms / 1000)
    return "%d ms" % ms


class Slack(object):

    url = (
        "https://hooks.slack.com/services/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"
    )

    def __init__(self, channel="#api", username="crunchbot"):
        if not (channel.startswith("#") or channel.startswith("@")):
            channel = "#" + channel
        self.channel = channel
        self.username = username

    def send(self, text=None, attachments=None):
        kwargs = {"channel": self.channel, "username": self.username, "parse": "none"}
        if text is not None:
            kwargs["text"] = text
        if attachments is not None:
            kwargs["attachments"] = attachments
        r = requests.post(self.url, data={"payload": json.dumps(kwargs)})
        # print(r)
        return r

    def attach(self, headline, text, color="good"):
        body = {
            "pretext": "*%s*" % headline,
            "fields": [
                # e.g. {"title": "Dataset", "value": dataset, "short": True},
            ],
            "text": text,
            "color": color,
            "mrkdwn_in": ["text", "pretext"],
        }
        self.send(attachments=[body])

    @contextlib.contextmanager
    def errors(self, text=None):
        """Catch any errors that happen and send them to slack"""
        try:
            yield
        except Exception as e:
            if text:
                text += ' "%s"' % e.message
            else:
                text = e.message

            try:
                self.send(text=text)
            except:
                traceback.print_exc()

    @staticmethod
    def linkify(href, text):
        return "<%s|%s>" % (href, text)


slack = Slack()


def api_times():
    output = []

    total_requests = sum(
        sum(int(value) for ts, value in s["pointlist"] if value is not None)
        for s in get_weekly_series(
            "sum:cr.server.request.time.ms.count{system:eu}.as_count().rollup(sum)"
        )
    )

    slow_requests = {}
    for s in get_weekly_series(
        "sum:cr.server.request.time.ms.count{system:eu,slow:yes} by {controller,method}.as_count().rollup(sum)"
    ):
        scope = dict(atom.split(":") for atom in s["scope"].split(","))
        values = [int(value) for ts, value in s["pointlist"] if value is not None]
        slow_requests[(scope["controller"], scope["method"])] = sum(values)
    slow_total = float(sum(slow_requests.itervalues()))
    worst = set([k for k, v in slow_requests.iteritems() if v / slow_total > 0.05])

    lost_hours = {}
    for s in get_weekly_series(
        "avg:cr.server.request.time.ms.avg{system:eu,slow:yes} by {controller,method}.rollup(avg) * "
        "sum:cr.server.request.time.ms.count{system:eu,slow:yes} by {controller,method}.as_count().rollup(sum)"
    ):
        scope = dict(atom.split(":") for atom in s["scope"].split(","))
        values = [
            value / ONE_HOUR_OF_MS for ts, value in s["pointlist"] if value is not None
        ]
        lost_hours[(scope["controller"], scope["method"])] = sum(values)
    lost_total = float(sum(lost_hours.itervalues()))
    worst.update(set([k for k, v in lost_hours.iteritems() if v / lost_total > 0.05]))

    worst = [
        (
            int((slow_requests.get(k, 0) * 100 / slow_total)),
            int((lost_hours.get(k, 0) * 100 / lost_total)),
            int(lost_hours.get(k, 0)),
            k,
        )
        for k in worst
    ]

    href = (
        "https://app.datadoghq.com/dashboard/f52-a52-7hv/slo-violators"
        "?from_ts=%d&to_ts=%d&fullscreen_widget=408300294"
        % (ONE_WEEK_AGO * 1000, NOW * 1000)
    )

    fast_percent = (total_requests - slow_total) * 100 / total_requests
    output.append(
        "%.2f%% of queries completed in time. Target is 99.99%%." % (fast_percent,)
    )
    output.append(
        "%d %s to slow queries" % (int(lost_total), slack.linkify(href, "hours lost"))
    )
    output.append("```")
    output.append("SLO      % count   Lost hours   % hours   Controller")
    tmpl = "{}      {:3}%         {:4}      {}   {} {}"
    for sp, lp, lh, k in reversed(sorted(worst)):
        controller, method = k
        SLO = " 200ms" if method in ("get", "head", "options") else "2000ms"
        output.append(
            tmpl.format(
                SLO,
                sp,
                lh or "",
                "{:3}%".format(lp) if lp else "    ",
                method.upper(),
                controller,
            )
        )
    output.append("```")

    return (
        output,
        "good"
        if fast_percent >= 99.99
        else "warning"
        if fast_percent >= 99.9
        else "danger",
    )


def task_times():
    output = []

    total_tasks = sum(
        sum(int(value) for ts, value in s["pointlist"] if value is not None)
        for s in get_weekly_series(
            "sum:task.run.ms.count{system:eu}.as_count().rollup(sum)"
        )
    )

    slow_tasks = {}
    for s in get_weekly_series(
        "sum:task.run.ms.count{system:eu,slow:yes} by {task}.as_count().rollup(sum)"
    ):
        scope = dict(atom.split(":") for atom in s["scope"].split(","))
        values = [int(value) for ts, value in s["pointlist"] if value is not None]
        slow_tasks[scope["task"]] = sum(values)
    slow_total = float(sum(slow_tasks.itervalues()))
    worst = set([k for k, v in slow_tasks.iteritems() if v / slow_total > 0.05])

    max_tasks = {}
    for s in get_weekly_series(
        "max:task.run.ms.max{system:eu,slow:yes} by {task}.rollup(max)"
    ):
        scope = dict(atom.split(":") for atom in s["scope"].split(","))
        values = [int(value) for ts, value in s["pointlist"] if value is not None]
        max_tasks[scope["task"]] = max(values)
    worst_max_tasks = list(reversed(sorted((v, k) for k, v in max_tasks.iteritems())))
    worst.update(set([k for v, k in worst_max_tasks[: int(len(worst_max_tasks) / 10)]]))

    lost_hours = {}
    for s in get_weekly_series(
        "avg:task.run.ms.avg{system:eu,slow:yes} by {task}.rollup(avg) * "
        "sum:task.run.ms.count{system:eu,slow:yes} by {task}.as_count().rollup(sum)"
    ):
        scope = dict(atom.split(":") for atom in s["scope"].split(","))
        values = [
            value / ONE_HOUR_OF_MS for ts, value in s["pointlist"] if value is not None
        ]
        lost_hours[scope["task"]] = sum(values)
    lost_total = float(sum(lost_hours.itervalues()))
    worst.update(set([k for k, v in lost_hours.iteritems() if v / lost_total > 0.05]))

    worst = [
        (
            int((slow_tasks.get(k, 0) * 100 / slow_total)),
            int((lost_hours.get(k, 0) * 100 / lost_total)),
            int(lost_hours.get(k, 0)),
            int(max_tasks.get(k, 0)),
            k,
        )
        for k in worst
    ]

    href = (
        "https://app.datadoghq.com/dashboard/d4f-fqa-x8u/slo-tasks"
        "?from_ts=%d&to_ts=%d&fullscreen_widget=354299717"
        % (ONE_WEEK_AGO * 1000, NOW * 1000)
    )
    fast_percent = (total_tasks - slow_total) * 100 / total_tasks
    output.append(
        "%.2f%% of tasks completed in time. Target is 99%%." % (fast_percent,)
    )
    output.append(
        "%d %s to slow tasks" % (int(lost_total), slack.linkify(href, "hours lost"))
    )
    output.append("```")
    output.append("% count   Lost hours   % hours   Max      Task")
    tmpl = "   {:3}%         {:4}      {}   {:>6}   {}"
    for sp, lp, lh, maxt, k in reversed(sorted(worst)):
        output.append(
            tmpl.format(
                sp,
                lh or "",
                "{:3}%".format(lp) if lp else "    ",
                friendly_duration(maxt),
                k,
            )
        )
    output.append("```")

    return (
        output,
        "good" if fast_percent >= 99 else "warning" if fast_percent >= 95 else "danger",
    )


def api_errors():
    output = []

    req_errors = defaultdict(dict)
    for s in get_weekly_series(
        "sum:cr.server.request.time.ms.count{system:eu,api_status_class:5xx} by {controller,method,api_status_code}.as_count().rollup(sum)"
    ):
        scope = dict(atom.split(":") for atom in s["scope"].split(","))
        values = [int(value) for ts, value in s["pointlist"] if value is not None]
        code = scope["api_status_code"]
        req_errors[code][(scope["controller"], scope["method"])] = sum(values)
    req_errors_total = float(sum(sum(v.itervalues()) for v in req_errors.itervalues()))

    href = (
        "https://app.datadoghq.com/dashboard/f52-a52-7hv/slo-violators"
        "?from_ts=%d&to_ts=%d&fullscreen_widget=3015013201169822"
        % (ONE_WEEK_AGO * 1000, NOW * 1000)
    )
    output.append(
        "%d %s that the API itself knew about (clients probably saw more)."
        % (req_errors_total, slack.linkify(href, "5xx errors"))
    )

    total_503s = float(sum(req_errors["503"].itervalues()))
    total_500s = float(sum(req_errors["500"].itervalues()))
    total_5xx = total_503s + total_500s
    req_503s = [
        (int((v * 100) / total_5xx), v, "503", k[1].upper(), k[0])
        for k, v in req_errors["503"].iteritems()
    ]
    req_500s = [
        (int((v * 100) / total_5xx), v, "500", k[1].upper(), k[0])
        for k, v in req_errors["500"].iteritems()
    ]
    output.append(
        """500s=%d 503s=%d (when Mongo/ZZ9/Elasticsearch don't work)."""
        % (total_500s, total_503s)
    )
    output.append("```")
    output.append("  %  Errors  Code   Endpoint")
    tmpl = "{:3}  {:6}   {}   {} {}"
    for item in reversed(sorted(req_503s + req_500s)):
        output.append(tmpl.format(*item))
    output.append("```")

    return (
        output,
        "danger" if total_5xx > 20 else "warning" if total_5xx > 10 else "good",
    )


def task_errors():
    output = []

    tasks = defaultdict(dict)
    for s in get_weekly_series(
        "sum:task.run.ms.count{system:eu} by {task,task_status}.as_count().rollup(sum)"
    ):
        scope = dict(atom.split(":") for atom in s["scope"].split(","))
        values = [int(value) for ts, value in s["pointlist"] if value is not None]
        code = scope["task_status"]
        tasks[code][scope["task"]] = sum(values)
    tasks_total = float(sum(sum(v.itervalues()) for v in tasks.itervalues()))

    href = (
        "https://app.datadoghq.com/dashboard/d4f-fqa-x8u/slo-tasks"
        "?from_ts=%d&to_ts=%d&fullscreen_widget=8945077376219396"
        % (ONE_WEEK_AGO * 1000, NOW * 1000)
    )
    output.append(
        "%s %s in the last week"
        % (friendly_count(tasks_total), slack.linkify(href, "tasks run"))
    )

    titles = {
        "retry": "retry (not broken, but indicates contention)",
        "suicided": "suicided (the developer thinks there is no need anymore to run the task, most often because the dataset has been deleted)",
        "invalid": "invalid (the inputs provided by the user weren't valid)",
    }

    def task_status_table(status):
        t = tasks[status]
        total = sum(t.itervalues())

        output = []
        output.append(
            "%s (%s) had status: %s"
            % (
                friendly_count(total),
                friendly_pct((total * 100) / tasks_total),
                titles.get(status, status),
            )
        )

        if status != "success":
            items = [(v, friendly_count(v), status, k) for k, v in t.iteritems()]
            tmpl = "{:>4}  {:8}      task:{}"
            for item in reversed(sorted(items)):
                output.append(tmpl.format(*item[1:]))

        return output

    for total, status in reversed(
        sorted(
            [(sum(counts.itervalues()), status) for status, counts in tasks.iteritems()]
        )
    ):
        output.append("```")
        output.extend(task_status_table(status))
        output.append("```")

    success_pct = (sum(tasks["success"].itervalues()) * 100) / tasks_total
    return (
        output,
        "danger" if success_pct < 95 else "warning" if success_pct < 99 else "good",
    )


def main():
    with slack.errors(text="Error running qualityreport on ahsoka:"):
        slack.send(
            "Weekly Quality Report for: %s UTC"
            % datetime.datetime.utcnow().strftime("%c")
        )
        output, color = api_times()
        slack.attach("API Completion Time", "\n".join(output), color=color)
        output, color = task_times()
        slack.attach("Task Completion Time", "\n".join(output), color=color)
        output, color = api_errors()
        slack.attach("API Errors", "\n".join(output), color=color)
        output, color = task_errors()
        slack.attach("Task Errors", "\n".join(output), color=color)


if __name__ == "__main__":
    main()