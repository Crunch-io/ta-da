"""
Code used by multiple Simulated User Testing modules and scripts
"""
from contextlib import contextmanager
from datetime import datetime
import json
import logging
import re
import requests

import pycrunch
import pycrunch.shoji
import six

from crunch_util import connect_pycrunch


def connect_api(config, args):
    """
    config: dict with contents of config.yaml
    args: dict with docopt options:
        -p: profile name
        -u: user alias
        -v: verbose flag
    """
    profile_name = args["-p"]
    user_alias = args["-u"]
    profile = config["profiles"][profile_name]
    connect_params = {"api_url": profile["api_url"]}
    for field_name in ("progress_timeout", "progress_interval"):
        if field_name in profile:
            connect_params[field_name] = profile[field_name]
    connect_params.update(profile["users"][user_alias])
    return connect_pycrunch(connect_params, verbose=args["-v"])


def get_command_name(args):
    """Return the command name out of docopt-generated args, or None"""
    for key, value in six.iteritems(args):
        if key[:1] in ("-", "<"):
            continue
        if value:
            return key
    else:
        return None


def get_project_by_name(site, project_name):
    projects = [
        p for p in six.itervalues(site.projects.index) if p.name == project_name
    ]
    if not projects:
        raise IndexError(
            'No project named "{}" visible to this user'.format(project_name)
        )
    if len(projects) > 1:
        raise ValueError(
            'Multiple projects named "{}" visible to this user'.format(project_name)
        )
    return projects[0]


def get_subproject_by_name(project, subproject_name):
    if isinstance(project, pycrunch.shoji.Tuple):
        project = project.entity
    subprojects = [
        p for _, p in subprojects_in_project(project) if p.name == subproject_name
    ]
    if not subprojects:
        raise IndexError('No sub-project named "{}"'.format(subproject_name))
    if len(subprojects) > 1:
        raise ValueError('Multiple sub-projects named "{}"'.format(subproject_name))
    return subprojects[0]


def datasets_in_project(project):
    """Yield (ds_url, ds_tuple) for each dataset in a project (skipping sub-projects)"""
    for ds_url, ds_tuple in six.iteritems(project.datasets.index):
        if ds_tuple.type != "dataset":
            continue
        yield (ds_url, ds_tuple)


def subprojects_in_project(project):
    """Yield (proj_url, proj_tuple) for each sub-project in a project (skipping
    datasets)"""
    for proj_url, proj_tuple in six.iteritems(project.index):
        if proj_tuple.type == "dataset":
            continue
        yield (proj_url, proj_tuple)


def yield_project_datasets_matching_name(project, ds_name_pattern):
    """
    ds_name_pattern: A regular expression to be matched against dataset names
    """
    compiled_ds_name_pattern = re.compile(ds_name_pattern)
    project = get_entity(project).refresh()
    for ds_tuple in six.itervalues(project.datasets.index):
        if ds_tuple.type != "dataset":
            continue
        if compiled_ds_name_pattern.search(ds_tuple.name):
            yield ds_tuple


def sort_ds_tuples_by_creation_datetime(ds_tuples, reverse=True):
    """
    ds_tuples: Sequence of dataset Tuples (pycrunch.shoji.Tuple)
    reverse: If true, sort newest dataset first (default: True)
    Return the Tuples in a list sorted by creation_time.
    """

    def _sort_key(ds_tuple):
        datetime_str = ds_tuple.creation_time
        if datetime_str.endswith("+00:00"):
            datetime_str = datetime_str[:-6]
        if len(datetime_str) > 19:
            t = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            t = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
        return (t, ds_tuple.name)

    return sorted(ds_tuples, key=_sort_key, reverse=reverse)


def ds_is_good(ds):
    """
    Return true iff `ds` is a datset with non-zero columns and rows.
    Warning: This will load the full dataset details if it they aren't loaded already.
    """
    if isinstance(ds, pycrunch.shoji.Tuple):
        ds = ds.entity
    return ds.body.size.columns > 0 and ds.body.size.rows > 0


def find_newest_dataset_in_project(project, ds_name_pattern):
    """
    Return a dataset tuple for the most recent dataset entity in the given
    project that has a name matching regular expression `ds_name_pattern` or
    None if there aren't any.
    """
    ds_tuples = yield_project_datasets_matching_name(project, ds_name_pattern)
    sorted_ds_tuples = sort_ds_tuples_by_creation_datetime(ds_tuples)
    return sorted_ds_tuples[0] if sorted_ds_tuples else None


def find_newest_good_dataset_in_project(project, ds_name_pattern):
    """
    Return a dataset tuple for the most recent dataset entity in the given
    project that has a name matching regular expression `ds_name_pattern` and
    looks like it isn't hosed (has non-zero columns and rows), or None if
    there aren't any.
    This can go slow because it loads each dataset to check for "goodness".
    """
    ds_tuples = yield_project_datasets_matching_name(project, ds_name_pattern)
    for ds_tuple in sort_ds_tuples_by_creation_datetime(ds_tuples):
        if ds_is_good(ds_tuple):
            return ds_tuple
    return None


def find_oldest_dataset_in_project(project, ds_name_pattern):
    """
    Return a dataset tuple for oldest dataset in the given project that has a
    name matching regular expression `ds_name_pattern` or None if there
    aren't any.
    """
    ds_tuples = yield_project_datasets_matching_name(project, ds_name_pattern)
    sorted_ds_tuples = sort_ds_tuples_by_creation_datetime(ds_tuples)
    return sorted_ds_tuples[0] if sorted_ds_tuples else None


def find_oldest_good_dataset_in_project(project, ds_name_pattern):
    """
    Return a dataset tuple for oldest dataset in the given project that has a
    name matching regular expression `ds_name_prefix` and looks like it isn't
    hosed (has non-zero columns and rows), or None if there aren't any.
    This can go slow because it loads each dataset to check for "goodness".
    """
    result = None
    ds_tuples = yield_project_datasets_matching_name(project, ds_name_pattern)
    for ds_tuple in sort_ds_tuples_by_creation_datetime(ds_tuples):
        if ds_is_good(ds_tuple):
            result = ds_tuple
    return result


def get_entity_url(obj):
    if isinstance(obj, pycrunch.shoji.Tuple):
        return obj.entity_url
    else:
        return obj.self


def get_entity_name(obj):
    if isinstance(obj, pycrunch.shoji.Tuple):
        return obj.name
    else:
        return obj.body.name


def get_entity(obj):
    if isinstance(obj, pycrunch.shoji.Tuple):
        return obj.entity
    else:
        return obj


# Copied from pow/clang/apis/slack.py
def message(**kwargs):
    """ Send a message to our Slack team

        kwargs:
        * `text` message
        * `channel` to post in
        * `username` to post as
        * `icon_emoji` to use for username
        * `parse` to control what Slack does with it ('full' is default; use
            None to do things like sending formatted links)
    """
    u = "https://hooks.slack.com/services/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"
    if kwargs["channel"][0] not in ["#", "@"]:
        kwargs["channel"] = "#" + kwargs["channel"]
    if "parse" not in kwargs:
        kwargs["parse"] = "full"
    payload = {"payload": json.dumps(kwargs)}
    r = requests.post(u, data=payload)
    return r


def get_ds_name_prefix(template_id):
    return "Sim {}".format(template_id)


class ErrorDuringActivity(Exception):
    def __init__(self, activity, err):
        self.activity = activity
        self.err = err

    def __str__(self):
        return "Error while {}: {}".format(self.activity, self.err)

    def __repr__(self):
        return "ErrorDuringActivity({!r}, {!r})".format(self.activity, self.err)


@contextmanager
def track_activity(logger_name, activity):
    log = logging.getLogger(logger_name)
    log.info(activity)
    try:
        yield
    except Exception as err:
        log.exception("Error during activity: %s", activity)
        raise ErrorDuringActivity(activity, err)
