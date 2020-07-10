#!/var/lib/crunch.io/venv/bin/python
# Created by david 2020-03-05
"""
Create test derived variables "quick and dirty"

Usage:
    make_derived_vars.py [options] <ds-id>

Options:
    --cr-lib-config=FILENAME    [default: /var/lib/crunch.io/cr.server-0.conf]
    --alias-template=TEMPLATE   Template for new var aliases [default: derived_{:04}]
    --user-email=EMAIL          Email address of user that will own new variables,
                                default is the database maintainer.
    --start-n=N                 Starting var sequence num [default: 1]
    -n N                        Number of derived variables to create [default: 1]
"""
from __future__ import print_function
import itertools
import os
import sys
import traceback

import docopt
from magicbus import bus
from magicbus.plugins import loggers

from cr.lib.commands.common import load_settings, startup
from cr.lib.entities.datasets.dataset import Dataset
from cr.lib.entities.users import User
from cr.lib.entities.variables import VariableDefinition
from cr.lib import exceptions
from cr.lib.loglib import log_to_stdout
from cr.lib.settings import settings


def _cr_lib_init(args):
    """
    Run this before doing anything with cr.lib
    """
    settings_yaml = args["--cr-lib-config"]
    settings.update(load_settings(settings_yaml))
    startup()


def _sample_code_fetch_derivations(ds):
    personal_var_ids = sorted(ds.folders.personal_variable_ids())
    print('Dataset {} has {} "personal variables"'.format(ds.id, len(personal_var_ids)))

    # Fetch all variable derivations
    # all_derivations is a list of tuples
    all_derivations = [
        (var_id, info)
        for var_id, info in ds.primary.describe("derivation")
        if info.get("derivation")
    ]
    print("Found", len(all_derivations), "derivations")


def find_base_vars(ds, num_vars):
    # Look for categorical non-derived variables to use as base variables
    base_vars = []
    ndv = ds.primary.non_derived_variables
    for v in ndv.values():
        if v.type not in ("categorical", "multiple_response"):
            continue
        if not len(v.categories):
            continue
        if max([cat.id for cat in v.categories]) <= 0:
            continue
        base_vars.append(v)
        if len(base_vars) >= num_vars:
            break
    return base_vars


def create_derived_vars(ds, alias_template, user_id, start_n=1, num_vars=1):
    # Create new derived variables from the available base variables
    base_vars = find_base_vars(ds, num_vars)
    if not base_vars:
        raise RuntimeError("No base categorical or multiple_response variables")
    base_vars = itertools.cycle(base_vars)
    new_var_ids = []
    for i in range(start_n, num_vars + start_n):
        var_alias = alias_template.format(i)
        var_name = "Derived Variable {}".format(var_alias)
        base_var = next(base_vars)
        selected_cat_id = max([cat.id for cat in base_var.categories])
        new_var = VariableDefinition(
            name=var_name,
            alias=var_alias,
            type=base_var.type,
            derived=True,
            derivation={
                "function": "select_categories",
                "args": [{"variable": base_var.id}, {"value": [selected_cat_id]}],
            },
        )
        print("Creating variable", var_alias, new_var.id)
        ds.add_variable(new_var)
        ds.folders.make_personal(user_id, new_var.id)
        new_var_ids.append(new_var.id)

    return new_var_ids


def main():
    args = docopt.docopt(__doc__)
    level = int(os.environ.get("CR_LOGLEVEL", "30"))
    loggers.StdoutLogger(bus, format="%(message)s\n", level=level).subscribe()
    log_to_stdout(level=30)
    _cr_lib_init(args)
    ds_id = args["<ds-id>"]
    try:
        ds = Dataset.find_by_id(id=ds_id, version="master__tip")
    except exceptions.NotFound:
        print("Source dataset not found:", ds_id, file=sys.stderr)
        return 1
    user_email = args["--user-email"]
    if user_email:
        try:
            user = User.get_by_email(user_email)
        except exceptions.NotFound:
            print(
                'User with email addr "{}" not found'.format(user_email),
                file=sys.stderr,
            )
            return 1
        user_id = user.id
    else:
        user_id = ds.maintainer_id
    if False:
        _sample_code_fetch_derivations(ds)
    new_var_ids = create_derived_vars(
        ds,
        args["--alias-template"],
        user_id,
        start_n=int(args["--start-n"]),
        num_vars=int(args["-n"]),
    )
    print("Created", len(new_var_ids), "new derived variables")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
