#!/usr/bin/env python3
"""
Big Dataset metadata helper script

Usage:
    ds.meta list-datasets [options] [--projects] [--project=PROJECT]
    ds.meta get [options] <ds-id> <filename>
    ds.meta info [options] <filename>
    ds.meta anonymize [options] <filename> <output-filename>
    ds.meta post [options] <filename>
    ds.meta raw-request [options] <method> <uri-path> <filename>
    ds.meta addvar [options] <ds-id> <filename>
    ds.meta folderize [options] <ds-id> <filename>
    ds.meta loadsave [options] <filename> <output-filename>

Options:
    -c CONFIG_FILENAME      [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: local]
    -i                      Run interactive prompt after executing command
    -v                      Print verbose messages
    --name=NAME             Override name in JSON file (post, addvar)
    --alias=ALIAS           Override alias in JSON file (addvar)
    -u --unique-subvar-aliases
                            Generate unique subvariable aliases (addvar)

Commands:
    get
        Download dataset metadata and save in JSON file
    info
        Print stats about metadata in JSON file
    anonymize
        Convert names and aliases in metadata to anonymized unique strings of
        the same length.
    post
        Create an empty dataset with metadata from JSON file
    addvar
        Create a variable with metadata from JSON file
    folderize
        Organize the variables in dataset <ds-id> into folders according to
        the structure in the JSON metadata file.
    loadsave
        Just load the JSON file and save it again, for testing

Example config.yaml file:
    local:
        connection:
            username: 'captain@crunch.io'
            password: 'asdfasdf'
            api_url: 'https://local.crunch.io:8443/api'
            verify: false
"""
from __future__ import print_function
import codecs
from collections import defaultdict, OrderedDict
import io
import json
import re
import sys
import time
import uuid

import docopt
import yaml
import six
from six.moves.urllib import parse as urllib_parse

from crunch_util import connect_pycrunch, create_dataset_from_csv2

CRITICAL_KEYS = (
    "name",
    "description",
    "alias",
    "entity_name",
    "notes",
    "origin_entity",
    "origin_metric",
    "origin_source",
)
VALUES_TO_PRESERVE = ("No Data",)


def make_cats_key(categories_list, remove_ids=True):
    if remove_ids:
        categories_list = [d.copy() for d in categories_list]
        for d in categories_list:
            d.pop("id", None)
    return tuple(json.dumps(d, sort_keys=True) for d in categories_list)


def obfuscate_metadata(metadata):
    """
    metadata is a dict containing Crunch dataset metadata.
    Modify it in-place, replacing most string values with gibberish of the same length.
    """
    if isinstance(metadata, dict):
        for key, value in six.iteritems(metadata):
            if isinstance(value, (dict, list)):
                obfuscate_metadata(value)
            elif isinstance(value, six.string_types):
                if key not in CRITICAL_KEYS:
                    continue
                if value in VALUES_TO_PRESERVE:
                    continue
                metadata[key] = codecs.encode(value, "rot13")
    elif isinstance(metadata, list):
        for item in metadata:
            obfuscate_metadata(item)


class MetadataModel(object):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self._meta = None
        # {alias: {"var_id": var_id, "subvar_id": subar_id_or_none}
        self._alias_map = None

    @property
    def alias_map(self):
        if self._alias_map is not None:
            return self._alias_map
        if self._meta is None:
            raise RuntimeError("Call get() or load() first")
        table = self._meta["table"]
        alias_map = self._alias_map = {}
        for var_id, var_def in six.iteritems(table):
            alias = var_def["alias"]
            if alias in alias_map:
                raise ValueError(
                    "Variable '{}' has duplicate alias '{}'".format(var_id, alias)
                )
            alias_map[alias] = {"var_id": var_id, "subvar_id": None}
            if "subreferences" not in var_def:
                continue
            for subvar_id, subvar_def in six.iteritems(var_def["subreferences"]):
                subvar_alias = subvar_def["alias"]
                if subvar_alias in alias_map:
                    raise ValueError(
                        "Subvariable '{}.{}' () has duplicate alias '{}'".format(
                            var_id, subvar_id, alias, subvar_alias
                        )
                    )
                alias_map[subvar_alias] = {"var_id": var_id, "subvar_id": subvar_id}
        return alias_map

    @staticmethod
    def _var_has_non_default_missing_reasons(var_def):
        """
        Return true iff the variable definition has one or more missing reasons
        other than the default system one.
        """
        missing_reasons = var_def.get("missing_reasons")
        if not missing_reasons:
            return False
        if len(missing_reasons) == 1 and missing_reasons == {"No Data": -1}:
            return False
        return True

    def get(self, site, ds_id):
        """
        Download dataset metadata into an internal data structure
        site: Crunch API object returned by connect_pycrunch
        ds_id: Dataset ID
        """
        if self.verbose:
            print("Downloading metadata for dataset", ds_id)
        self._meta.clear()
        self._meta["id"] = ds_id
        ds_url = "{}{}/".format(site.datasets["self"], ds_id)
        response = site.session.get(ds_url)
        ds = response.payload
        self._meta["name"] = ds["body"]["name"]
        self._meta["description"] = ds["body"]["description"]
        self._meta["size"] = ds["body"]["size"]
        self._meta["variables"] = {}
        self._get_variables(site, ds_url)
        self._get_weights(site, ds_url)
        self._get_settings(site, ds_url)
        # Get preferences
        if self.verbose:
            print("Fetching preferences")
        self._meta["preferences"] = ds.preferences["body"]
        # Get "table" of variable definitions
        if self.verbose:
            print("Fetching metadata table")
        table_url = "{}table/".format(ds_url)
        response = site.session.get(table_url)
        table_info = response.payload
        self._meta["table"] = table_info["metadata"]
        # Get missing_rules for variables with non-default missing_reason
        # codes.
        var_ids_needing_missing_rules = []
        for var_id, var_def in six.iteritems(self._meta["table"]):
            if self._var_has_non_default_missing_reasons(var_def):
                var_ids_needing_missing_rules.append(var_id)
        if self.verbose:
            print(
                "Fetching missing_rules for {} variables".format(
                    len(var_ids_needing_missing_rules)
                )
            )
        for var_id in var_ids_needing_missing_rules:
            missing_rules_url = "{}variables/{}/missing_rules/".format(ds_url, var_id)
            response = site.session.get(missing_rules_url)
            missing_rules = response.payload["body"]["rules"]
            self._meta["table"][var_id]["missing_rules"] = missing_rules
        # Get hierarchical order
        if self.verbose:
            print("Getting hierarchical order")
        hier = ds.variables.hier["graph"]
        self._meta["variables"]["hier"] = hier
        # That's all
        if self.verbose:
            print("Done.")

    def _get_variables(self, site, ds_url):
        if self.verbose:
            print("Fetching variables")
        variables_url = "{}variables/".format(ds_url)
        response = site.session.get(variables_url)
        variables_info = response.payload
        self._meta["variables"]["index"] = variables_info["index"]

    def _get_weights(self, site, ds_url):
        if self.verbose:
            print("Fetching weights")
        weights_url = "{}variables/weights/".format(ds_url)
        response = site.session.get(weights_url)
        weights_info = response.payload
        self._meta["variables"]["weights"] = weights_info["graph"]

    def _get_settings(self, site, ds_url):
        if self.verbose:
            print("Fetching settings")
        settings_url = "{}settings/".format(ds_url)
        response = site.session.get(settings_url)
        settings_info = response.payload
        self._meta["settings"] = settings_info["body"]

    @staticmethod
    def convert_var_def(var_def):
        """
        Convert a variable definition from the format returned by GET into the
        format expected by POST.

        For variables of type multiple_response:

            The GET format includes a 'subreferences' key containing a map of
            subvariable ID to subvariable definition, and a 'subvariables' key
            containing a list of subvariable IDs.

            The POST format instead just has a key named 'subvariables'
            containing a list of subvariable definitions.
        """
        new_var_def = var_def.copy()
        if "subreferences" in new_var_def and "subvariables" in new_var_def:
            del new_var_def["subreferences"]
            new_var_def["subvariables"] = subvariables = []
            for subvar_id in var_def["subvariables"]:
                subvariables.append(var_def["subreferences"][subvar_id].copy())
        return new_var_def

    def _translate_var_id(self, variables_by_alias, orig_var_id):
        """
        variables_by_alias: ds.variables.by('alias')
        orig_var_id: ID from metadata file used to create dataset
        Return variable ID from live dataset, or None if not found.
        """
        var_def = self._meta["table"].get(orig_var_id)
        if not var_def:
            return None
        var_alias = var_def["alias"]
        var_info = variables_by_alias.get(var_alias)
        if not var_info:
            return None
        return var_info["id"]

    def _translate_var_url(self, ds, orig_var_url, variables_by_alias=None):
        if variables_by_alias is None:
            variables_by_alias = ds.variables.by("alias")
        if orig_var_url is None:
            return None
        m = re.match(r"^(.*)/([^/]+)/$", orig_var_url)
        if not m:
            # Doesn't look like a URL
            return None
        prefix = m.group(1)
        orig_var_id = m.group(2)
        var_id = self._translate_var_id(variables_by_alias, orig_var_id)
        if var_id is None:
            return None
        if orig_var_url.startswith((".", "/")):
            # Handle relative URL like "../<var-id>/" or URI like "/..."
            return "{}/{}/".format(prefix, var_id)
        else:
            # Handle absolute URL
            return "{}{}/".format(ds.variables.self, var_id)

    def post(self, site, name=None):
        if not self._meta:
            raise RuntimeError("Must load metadata before POSTing dataset")
        if not name:
            name = self._meta["name"]
        new_meta = {
            "element": "shoji:entity",
            "body": {
                "name": name,
                "description": self._meta["description"],
                "table": {
                    "element": "crunch:table",
                    "metadata": OrderedDict(),
                    "order": [],
                },
                "weight_variables": [],
            },
        }
        table = self._meta["table"]
        new_table = new_meta["body"]["table"]["metadata"]
        var_ids_to_create = set(table)

        # First pass: Create all the variables with IDs like "000000"
        # in the same request used to create the dataset.
        for i in six.moves.range(100000):
            var_id = str(i).zfill(6)
            if var_id in var_ids_to_create:
                var_ids_to_create.remove(var_id)
            else:
                continue
            var_def = table[var_id]
            new_table[var_def["alias"]] = self.convert_var_def(var_def)
        if self.verbose:
            print(
                "Creating dataset with its {} original variables".format(len(new_table))
            )
        ds = create_dataset_from_csv2(
            site, new_meta, None, verbose=self.verbose, gzip_metadata=True
        )
        print("New dataset ID:", ds.body.id)

        # Second pass: Create all the variables with longer IDs
        if self.verbose:
            print("Adding {} more variables to dataset".format(len(var_ids_to_create)))
        for i, var_id in enumerate(sorted(var_ids_to_create), 1):
            if self.verbose:
                print(
                    "\rCreating variable {:04d} of {:04d}".format(
                        i, len(var_ids_to_create)
                    ),
                    end="",
                )
            var_def = self.convert_var_def(self._meta["table"][var_id])
            ds.variables.create({"body": var_def})
            if self.verbose:
                print()

        # Set the list of weight variables
        weight_urls = []
        ds.variables.refresh()
        variables_by_alias = ds.variables.by("alias")
        for orig_weight_url in self._meta["variables"]["weights"]:
            weight_url = self._translate_var_url(
                ds, orig_weight_url, variables_by_alias=variables_by_alias
            )
            if weight_url:
                weight_urls.append(weight_url)
        if self.verbose:
            print("Setting {} weight variable(s)".format(len(weight_urls)))
        ds.variables.weights.patch({"graph": weight_urls})

        # Set settings
        if self.verbose:
            print("Setting settings")
        settings = self._meta["settings"].copy()
        settings["weight"] = self._translate_var_url(
            ds, settings["weight"], variables_by_alias=variables_by_alias
        )
        if settings["dashboard_deck"]:
            print(
                "WARNING: dashboard_deck is set to '{}'"
                " which is probably not valid for this dataset.".format(
                    settings["dashboard_deck"]
                ),
                file=sys.stderr,
            )
        ds.settings.patch(settings)

        # Set preferences
        if self.verbose:
            print("Setting preferences")
        preferences = self._meta["preferences"].copy()
        preferences["weight"] = self._translate_var_url(
            ds, preferences["weight"], variables_by_alias=variables_by_alias
        )
        ds.preferences.patch(preferences)

        # Set hierarchical order
        self.folderize(ds)

    def _translate_hier(self, ds, hier_list, variables_by_alias=None):
        # ds: Dataset object
        # hier_list: List of folders dicts and variable URLs
        # variables_by_alias: ds.variables.by('alias')
        # Return the new hierarchy with all variable URLs translated
        if variables_by_alias is None:
            variables_by_alias = ds.variables.by("alias")
        new_hier_list = []
        for node in hier_list:
            if isinstance(node, six.string_types):
                var_url = self._translate_var_url(
                    ds, node, variables_by_alias=variables_by_alias
                )
                if var_url:
                    new_hier_list.append(var_url)
            elif isinstance(node, dict):
                new_node = {}
                for folder_name, sub_list in six.iteritems(node):
                    new_node[folder_name] = self._translate_hier(
                        ds, sub_list, variables_by_alias=variables_by_alias
                    )
                new_hier_list.append(new_node)
        return new_hier_list

    def folderize(self, ds):
        if self.verbose:
            print("Setting hierarchical order")
        hier = self._translate_hier(ds, self._meta["variables"]["hier"])
        ds.variables.hier.put({"graph": hier})

    @staticmethod
    def _open_json(filename, mode):
        if six.PY2:
            return open(filename, mode + "b")
        else:
            return io.open(filename, mode, encoding="UTF-8")

    def save(self, filename):
        """Save downloaded metadata to JSON file"""
        if self.verbose:
            print("Saving metadata to:", filename)
        with self._open_json(filename, "w") as f:
            json.dump(self._meta, f, indent=2, sort_keys=True)
            f.write("\n")

    def load(self, filename):
        """Load downloaded metadata from JSON file"""
        if self.verbose:
            print("Loading metadata from:", filename)
        with self._open_json(filename, "r") as f:
            self._meta = json.load(f)

    def report(self):
        # general info
        meta = self._meta
        print("Dataset ID:", meta["id"])
        print("name:", meta["name"])
        print("description:", meta["description"])
        print("size:")
        print("  columns:", meta["size"]["columns"])
        print("  rows:", meta["size"]["rows"])
        print("  unfiltered_rows:", meta["size"]["rows"])
        # variable info
        table = meta["table"]
        var_type_count_map = defaultdict(int)
        num_vars_with_categories = 0
        unique_cats_lists_without_ids = set()
        unique_cats_lists_with_ids = set()
        tot_categories = 0
        min_categories = None
        max_categories = None
        max_categories_var_alias = None
        num_vars_with_subvars = 0
        tot_subvars = 0
        min_subvars = None
        max_subvars = None
        for var_def in six.itervalues(table):
            var_type = var_def["type"]
            var_type_count_map[var_type] += 1
            if "categories" in var_def:
                num_vars_with_categories += 1
                categories_list = var_def["categories"]
                unique_cats_lists_without_ids.add(
                    make_cats_key(categories_list, remove_ids=True)
                )
                unique_cats_lists_with_ids.add(
                    make_cats_key(categories_list, remove_ids=False)
                )
                num_categories = len(categories_list)
                tot_categories += num_categories
                if min_categories is None or num_categories < min_categories:
                    min_categories = num_categories
                if max_categories is None or num_categories > max_categories:
                    max_categories = num_categories
                    max_categories_var_alias = var_def["alias"]
            if "subreferences" in var_def:
                num_vars_with_subvars += 1
                num_subvars = len(var_def["subreferences"])
                tot_subvars += num_subvars
                if min_subvars is None or num_subvars < min_subvars:
                    min_subvars = num_subvars
                if max_subvars is None or num_subvars > max_subvars:
                    max_subvars = num_subvars
        print("variables:")
        print("  num. variables:", len(table))
        print("  variables by type:")
        for var_type in sorted(var_type_count_map):
            print("    {}: {}".format(var_type, var_type_count_map[var_type]))
        print("  num. variables with categories:", num_vars_with_categories)
        print("  total categories:", tot_categories)
        print("  min. categories per variable:", min_categories)
        if num_vars_with_categories > 0:
            print(
                "  ave. categories per variable:",
                float(tot_categories) / num_vars_with_categories,
            )
        print("  max. categories per variable:", max_categories)
        print("  alias of variable with most categories:", max_categories_var_alias)
        print("  num. unique category lists:")
        print("    with ids:", len(unique_cats_lists_with_ids))
        print("    without ids:", len(unique_cats_lists_without_ids))
        print("  subvariables:")
        print(
            "    num. variables with subvariables (multiple response):",
            num_vars_with_subvars,
        )
        print("    tot. subvariables:", tot_subvars)
        print("    min. subvariables per variable:", min_subvars)
        if num_vars_with_subvars > 0:
            print(
                "    ave. subvariables per variable:",
                float(tot_subvars) / num_vars_with_subvars,
            )
        print("    max. subvariables per variable:", max_subvars)

    def anonymize(self):
        obfuscate_metadata(self._meta)


def do_get(args):
    ds_id = args["<ds-id>"]
    filename = args["<filename>"]
    with io.open(args["-c"], "r", encoding="UTF-8") as f:
        config = yaml.safe_load(f)[args["-p"]]
    site = connect_pycrunch(config["connection"], verbose=args["-v"])
    meta = MetadataModel(verbose=args["-v"])
    meta.get(site, ds_id)
    meta.save(filename)
    if args["-i"]:
        import IPython

        IPython.embed()


def do_info(args):
    filename = args["<filename>"]
    meta = MetadataModel(verbose=args["-v"])
    meta.load(filename)
    meta.report()


def do_anonymize(args):
    filename = args["<filename>"]
    meta = MetadataModel(verbose=args["-v"])
    meta.load(filename)
    meta.anonymize()
    meta.save(args["<output-filename>"])


def do_loadsave(args):
    filename = args["<filename>"]
    meta = MetadataModel(verbose=args["-v"])
    meta.load(filename)
    meta.save(args["<output-filename>"])


def do_post(args):
    filename = args["<filename>"]
    with io.open(args["-c"], "r", encoding="UTF-8") as f:
        config = yaml.safe_load(f)[args["-p"]]
    site = connect_pycrunch(config["connection"], verbose=args["-v"])
    meta = MetadataModel(verbose=args["-v"])
    meta.load(filename)
    meta.post(site, name=args["--name"])


def _generate_unique_subvar_aliases(var_meta):
    """
    Modify variable metadata in-place, replacing the alias of each subvarible
    (if any) with a guaranteed unique identifier.
    """
    if "subreferences" not in var_meta:
        return
    for subref in six.itervalues(var_meta["subreferences"]):
        subref["alias"] = uuid.uuid4().hex


def do_addvar(args):
    ds_id = args["<ds-id>"]
    filename = args["<filename>"]
    verbose = args["-v"]
    with io.open(args["-c"], "r", encoding="UTF-8") as f:
        config = yaml.safe_load(f)[args["-p"]]
    site = connect_pycrunch(config["connection"], verbose=verbose)
    ds_url = "{}{}/".format(site.datasets["self"], ds_id)
    response = site.session.get(ds_url)
    ds = response.payload
    with open(filename) as f:
        var_meta = json.load(f)
    if args["--name"]:
        var_meta["name"] = args["--name"]
    if args["--alias"]:
        var_meta["alias"] = args["--alias"]
    if args["--unique-subvar-aliases"]:
        _generate_unique_subvar_aliases(var_meta)
    meta = MetadataModel(verbose=verbose)
    var_def = meta.convert_var_def(var_meta)
    if verbose:
        print(
            "Creating variable '{}' with alias {}".format(
                var_def["name"], var_def["alias"]
            )
        )
    t0 = time.time()
    variables = ds.variables
    t1 = time.time()
    print("GET /variables duration:", t1 - t0)
    try:
        variables.create({"body": var_def})
    finally:
        print("POST /variables duration:", time.time() - t1)


def do_folderize(args):
    ds_id = args["<ds-id>"]
    filename = args["<filename>"]
    with io.open(args["-c"], "r", encoding="UTF-8") as f:
        config = yaml.safe_load(f)[args["-p"]]
    site = connect_pycrunch(config["connection"], verbose=args["-v"])
    ds_url = "{}{}/".format(site.datasets["self"], ds_id)
    response = site.session.get(ds_url)
    ds = response.payload
    meta = MetadataModel(verbose=args["-v"])
    meta.load(filename)
    meta.folderize(ds)


def do_list_datasets(args):
    with open(args["-c"]) as f:
        config = yaml.safe_load(f)[args["-p"]]
    verbose = args["-v"]
    site = connect_pycrunch(config["connection"], verbose=verbose)
    if args["-i"]:
        import IPython

        IPython.embed()
    if args["--projects"]:
        for proj in six.itervalues(site.projects.index):
            print(u"{proj.id} {proj.name}".format(proj=proj))
        return 0
    if args["--project"]:
        proj_name_or_id = args["--project"]
        try:
            proj = site.projects.by("id")[proj_name_or_id]
        except KeyError:
            proj = site.projects.by("name")[proj_name_or_id]
        url = urllib_parse.urljoin(proj.entity_url, "datasets/")
        response = site.session.get(url)
        datasets_index = response.json()["index"]
        for ds_info in six.itervalues(datasets_index):
            print(u"{ds[id]} {ds[name]}".format(ds=ds_info))
        return 0
    for ds in six.itervalues(site.datasets.index):
        print(u"{ds.id} {ds.name}".format(ds=ds))
    return 0


def do_raw_request(args):
    with open(args["-c"]) as f:
        config = yaml.safe_load(f)[args["-p"]]
    verbose = args["-v"]
    method = args["<method>"]
    uri_path = args["<uri-path>"]
    filename = args["<filename>"]
    site = connect_pycrunch(config["connection"], verbose=verbose)
    request_url = "{}{}".format(site.self, uri_path)
    query = None  # TODO
    headers = None
    data = None
    if method in ("PATCH", "POST", "PUT"):
        # Request has a body
        headers = {"Content-Type": "application/json"}
        if filename == "-":
            data = sys.stdin.read().encode("utf-8")
        else:
            data = open(filename, "rb")
            if filename.endswith(".gz"):
                headers["Content-Encoding"] = "gzip"
    t0 = time.time()
    response = site.session.request(
        method, request_url, params=query, headers=headers, data=data
    )
    duration_sec = time.time() - t0
    print(duration_sec, "seconds", file=sys.stderr)
    location = response.headers.get("location")
    print("HTTP/1.1 {} {}".format(response.status_code, response.reason))
    if location is not None:
        print("Location:", location)
    print()
    json.dump(response.payload, sys.stdout, indent=4)
    sys.stdout.write("\n")
    sys.stdout.flush()
    if args["-i"]:
        import IPython

        IPython.embed()


def main():
    args = docopt.docopt(__doc__)
    t0 = time.time()
    try:
        if args["get"]:
            return do_get(args)
        elif args["info"]:
            return do_info(args)
        elif args["anonymize"]:
            return do_anonymize(args)
        elif args["post"]:
            return do_post(args)
        elif args["addvar"]:
            return do_addvar(args)
        elif args["folderize"]:
            return do_folderize(args)
        elif args["loadsave"]:
            return do_loadsave(args)
        elif args["list-datasets"]:
            return do_list_datasets(args)
        elif args["raw-request"]:
            return do_raw_request(args)
        else:
            raise NotImplementedError("Sorry, that command is not yet implemented.")
    finally:
        print("Elapsed time:", time.time() - t0, "seconds", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
