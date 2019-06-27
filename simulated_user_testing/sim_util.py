"""
Code used by multiple Simulated User Testing modules and scripts
"""
from datetime import datetime

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


def sort_project_datasets_by_creation_datetime(project, reverse=True):
    def _sort_key(item):
        ds_tuple = item[1]
        datetime_str = ds_tuple.creation_time
        if datetime_str.endswith("+00:00"):
            datetime_str = datetime_str[:-6]
        t = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%f")
        return (t, ds_tuple.name)

    return sorted(datasets_in_project(project), key=_sort_key, reverse=reverse)


def ds_is_good(ds):
    if isinstance(ds, pycrunch.shoji.Tuple):
        ds = ds.entity
    return ds.body.size.columns > 0 and ds.body.size.rows > 0


def find_latest_good_dataset_in_project(project, ds_name_prefix):
    """
    Return a dataset tuple for the most recent dataset entity in the given
    project that has a name matching ds_name_prefix and looks like it isn't
    hosed (has non-zero columns and rows), or None if there aren't any.
    """
    if isinstance(project, pycrunch.shoji.Tuple):
        project = project.entity
    for _, ds_tuple in sort_project_datasets_by_creation_datetime(project):
        if not ds_tuple.name.startswith(ds_name_prefix):
            continue
        if ds_is_good(ds_tuple):
            return ds_tuple
    return None


def get_entity_url(obj):
    if isinstance(obj, pycrunch.shoji.Tuple):
        return obj.entity_url
    else:
        return obj.self


def get_entity(obj):
    if isinstance(obj, pycrunch.shoji.Tuple):
        return obj.entity
    else:
        return obj
