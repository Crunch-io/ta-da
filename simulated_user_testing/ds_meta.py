#!/usr/bin/env python3
"""
Big Dataset metadata helper script

Usage:
    ds_meta.py list-datasets [options] [--projects] [--project=PROJECT]
    ds_meta.py get [options] <ds-id> <dirname>
    ds_meta.py info [options] <dirname>
    ds_meta.py create-payload [options] <dirname>
    ds_meta.py anonymize-payload [options] <dirname>
    ds_meta.py create [options] <dirname-or-filename>
    ds_meta.py addvar [options] <ds-id> <filename>
    ds_meta.py folderize [options] <ds-id> <filename>
    ds_meta.py raw-request [options] <method> <uri-path> <filename>
    ds_meta.py sample-config

Options:
    -c CONFIG_FILENAME      [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: alpha]
    -u USER_ALIAS           Key to section inside profile [default: default]
    -i                      Run interactive prompt after executing command
    -v                      Log verbose messages
    --name=NAME             Override name in JSON file (create-payload, create, addvar)
    --alias=ALIAS           Override alias in JSON file (addvar)
    --unique-subvar-aliases
                            Generate unique subvariable aliases (addvar)

Commands:
    get
        Download dataset metadata and save in JSON files
    info
        Print stats about metadata in JSON files
    anonymize-payload
        Convert names and aliases in metadata payload to anonymized unique strings of
        the same length.
    create
        Create an empty dataset with metadata from -payload.json file
    addvar
        Create a variable with metadata from JSON file
    folderize
        Organize the variables in dataset <ds-id> into folders according to
        the structure in the JSON metadata file.
    sample-config
        Print sample config.yaml file contents to stdout
"""
from __future__ import print_function
import codecs
from collections import defaultdict, OrderedDict
import io
import json
import logging
import os
import re
import sys
import textwrap
import time
import uuid

import docopt
import yaml
import six

# from six.moves.urllib import parse as urllib_parse
import urllib.parse as urllib_parse

from crunch_util import create_dataset_from_csv2, maybe_uncompress_and_load_json
from sim_util import connect_api, get_command_name

this_module = sys.modules[__name__]

log = logging.getLogger("ds_meta")


CRITICAL_KEYS = (
    "name",
    "description",
    "alias",
    "entity_name",
    "notes",
    "origin_entity",
    "origin_metric",
    "origin_source",
    "variable",  # args that refer to variable aliases
)
VALUES_TO_PRESERVE = [("name", "No Data"), ("group", "__hidden__")]


def main():
    args = docopt.docopt(__doc__)
    logging.basicConfig(level=logging.INFO)
    with io.open(args["-c"], "r", encoding="UTF-8") as f:
        config = yaml.safe_load(f)
    command_name = get_command_name(args)
    method_name = "do_" + command_name.replace("-", "_")
    method = getattr(this_module, method_name, None)
    if method is None:
        raise NotImplementedError(
            "Sorry, {!r} is not yet implemented".format(command_name)
        )
    verbose = args["-v"]
    t0 = time.time()
    try:
        return method(config, args)
    finally:
        if verbose:
            log.info("Elapsed time: %s seconds", time.time() - t0)


def obfuscate_string(value, path):
    parent = path[-1] if path else None
    for k, v in VALUES_TO_PRESERVE:
        if k == parent and v == value:
            return value
    if parent in CRITICAL_KEYS:
        return codecs.encode(value, "rot13")
    if path[:3] == ["body", "table", "order"]:
        return codecs.encode(value, "rot13")
    if path == ["body", "settings", "weight"]:
        return codecs.encode(value, "rot13")
    if len(path) == 3 and path[:2] == ["body", "weight_variables"]:
        return codecs.encode(value, "rot13")
    return value


def obfuscate_metadata(metadata, path=None):
    """
    metadata is a dict containing Crunch dataset metadata.
    Modify it in-place, replacing most string values with gibberish of the same length.
    This is tuned for the create dataset payload JSON.
    """
    if path is None:
        path = []
    if isinstance(metadata, dict):
        if path == ["body", "table", "metadata"]:
            # The keys are variable aliases that must be obfuscated
            new_metadata = {}
            for key, value in six.iteritems(metadata):
                new_key = codecs.encode(key, "rot13")
                path.append(new_key)
                new_metadata[new_key] = obfuscate_metadata(value, path)
                path.pop()
            metadata = new_metadata
        else:
            for key, value in six.iteritems(metadata):
                path.append(key)
                metadata[key] = obfuscate_metadata(value, path)
                path.pop()
    elif isinstance(metadata, list):
        for i, item in enumerate(metadata):
            path.append(i)
            metadata[i] = obfuscate_metadata(item, path)
            path.pop()
    elif isinstance(metadata, six.string_types):
        metadata = obfuscate_string(metadata, path)
    return metadata


def make_cats_key(categories_list, remove_ids=True):
    if remove_ids:
        categories_list = [d.copy() for d in categories_list]
        for d in categories_list:
            d.pop("id", None)
    return tuple(json.dumps(d, sort_keys=True) for d in categories_list)


def get_id_from_url(url):
    """
    For a URL in the form https://hostname/blah/<id>/ or
    in the form ../<id>/, return id. Otherwise, return None
    """
    if url is None:
        return None
    p = urllib_parse.urlparse(url)
    parts = p.path.split("/")
    if len(parts) >= 3 and not parts[-1]:
        return parts[-2]
    return None


class MetadataModel(object):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self._meta = None
        # {alias: {"var_id": var_id, "subvar_id": subar_id_or_none}
        self._alias_map = None

    def _trace(self, msg, *args, **kwargs):
        if self.verbose:
            log.info(msg, *args, **kwargs)

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

    def get(self, site, ds_id, dirname):
        """
        Download dataset metadata to local files
        site: Crunch API object returned by connect_pycrunch
        ds_id: Dataset ID
        dirname: Directory into which the files will be saved
        """
        if self.verbose:
            log.info("Downloading metadata for dataset: %s", ds_id)
        # Download the main dataset metadata
        ds_url = "{}{}/".format(site.datasets["self"], ds_id)
        response = site.session.get(ds_url)
        ds = response.payload
        self._dump(ds, dirname, "dataset-main.json")
        # Download various additional types of dataset metadata
        self._get_variables(site, ds_url, dirname)
        self._get_weights(site, ds_url, dirname)
        self._get_settings(site, ds_url, dirname)
        self._get_preferences(site, ds, dirname)
        self._get_table(site, ds_url, dirname)
        self._get_variable_hierarchy(site, ds, dirname)
        # That's all
        self._trace("Done.")

    def _dump(self, obj, dirname, base_filename):
        with open(os.path.join(dirname, base_filename), "w") as f:
            json.dump(obj, f, indent=2, sort_keys=True)
            f.write("\n")

    def _get_variables(self, site, ds_url, dirname):
        self._trace("Fetching variables")
        variables_url = "{}variables/".format(ds_url)
        response = site.session.get(variables_url)
        dataset_vars = response.payload
        self._dump(dataset_vars, dirname, "dataset-variables.json")
        # Fetch details for derived variables
        for var_url, var_info in six.iteritems(dataset_vars["index"]):
            if not var_info["derived"]:
                continue
            var_id = get_id_from_url(var_url)
            response = site.session.get(var_url)
            self._dump(response.payload, dirname, "var-{}-detail.json".format(var_id))

    def _get_weights(self, site, ds_url, dirname):
        self._trace("Fetching weights")
        weights_url = "{}variables/weights/".format(ds_url)
        response = site.session.get(weights_url)
        self._dump(response.payload, dirname, "dataset-weights.json")

    def _get_settings(self, site, ds_url, dirname):
        self._trace("Fetching settings")
        settings_url = "{}settings/".format(ds_url)
        response = site.session.get(settings_url)
        self._dump(response.payload, dirname, "dataset-settings.json")

    def _get_preferences(self, site, ds, dirname):
        self._trace("Fetching preferences")
        self._dump(ds.preferences, dirname, "dataset-preferences.json")

    def _get_table(self, site, ds_url, dirname):
        # Get "table" of variable definitions
        self._trace("Fetching metadata table")
        table_url = "{}table/".format(ds_url)
        response = site.session.get(table_url)
        # We need to temporarily keep the table payload in memory
        # in order to figure out what to load next.
        response_payload = response.payload
        self._dump(response_payload, dirname, "dataset-table.json")

        # Get missing_rules for variables with non-default missing_reason
        # codes.
        var_ids_needing_missing_rules = []
        for var_id, var_def in six.iteritems(response_payload["metadata"]):
            if self._var_has_non_default_missing_reasons(var_def):
                var_ids_needing_missing_rules.append(var_id)
        self._trace(
            "Fetching missing_rules for {} variables".format(
                len(var_ids_needing_missing_rules)
            )
        )
        for var_id in var_ids_needing_missing_rules:
            missing_rules_url = "{}variables/{}/missing_rules/".format(ds_url, var_id)
            response = site.session.get(missing_rules_url)
            self._dump(
                response.payload, dirname, "var-{}-missing-rules.json".format(var_id)
            )

    def _get_variable_hierarchy(self, site, ds, dirname):
        self._trace("Getting variable folder hierarchy")
        self._dump(ds.variables.hier, dirname, "variables-hier.json")

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

    def create_payload(self, dirname, name=None):
        self.remove_variables_with_duplicate_names()

        if not name:
            name = self._meta["main"]["name"]
        new_meta = {
            "element": "shoji:entity",
            "body": {
                "name": name,
                "table": {
                    "element": "crunch:table",
                    "metadata": OrderedDict(),
                    "order": [],
                },
                "weight_variables": [],
            },
        }
        for k in (
            "end_date",
            "notes",
            "start_date",
            "streaming",
            "is_published",
            "description",
        ):
            if k in self._meta["main"]:
                new_meta["body"][k] = self._meta["main"][k]

        table = self._meta["table"]
        new_table = new_meta["body"]["table"]["metadata"]

        # Convert the variable definitions from GET format to POST format and
        # add them to the payload in alias order.
        alias_varid_map = {}
        for var_id, var_def in six.iteritems(table):
            alias_varid_map[var_def["alias"]] = var_id
        for var_alias in sorted(alias_varid_map):
            var_id = alias_varid_map[var_alias]
            var_def = table[var_id]
            new_table[var_alias] = self.convert_var_def(var_def)
            if "alias" in new_table[var_alias]:
                # Delete redundant alias, the key is the alias
                del new_table[var_alias]["alias"]

        # Add variable derivations to the payload
        for var_url, var_info in six.iteritems(self._meta["variables"]["index"]):
            if not var_info["derived"]:
                continue
            var_id = get_id_from_url(var_url)
            var_detail = self._meta["variables"]["detail"][var_id]
            var_alias = var_info["alias"]
            derived_var = {
                "name": var_info["name"],
                "description": var_info.get("description", ""),
                "derivation": self._convert_var_derivation(var_detail["derivation"]),
            }
            new_table[var_alias] = derived_var

        # Set aliases of starting weight variables
        for orig_weight_url in self._meta["variables"]["weights"]:
            var_id = get_id_from_url(orig_weight_url)
            if not var_id:
                raise ValueError("Weight URL missing ID: {}".format(orig_weight_url))
            var_def = self._meta["table"][var_id]
            new_meta["body"]["weight_variables"].append(var_def["alias"])

        # Set settings
        settings = self._convert_settings(self._meta["settings"])
        if settings:
            new_meta["body"]["settings"] = settings

        # Set up order
        order = self._translate_hier_to_order()
        new_meta["body"]["table"]["order"] = order

        # Save the payload
        self._dump(new_meta, dirname, "dataset-payload.json")

    def _convert_var_derivation(self, derivation_expr):
        """Return a copy of derivation_expr converted from GET to POST format"""
        new_expr = {"function": derivation_expr["function"], "args": []}
        for arg in derivation_expr["args"]:
            if "variable" in arg:
                var_id = get_id_from_url(arg["variable"])
                var_alias = self._meta["table"][var_id]["alias"]
                arg = arg.copy()
                arg["variable"] = var_alias
            new_expr["args"].append(arg)
        return new_expr

    def _convert_settings(self, settings):
        """Return a copy of dataset settings converted from GET to POST format"""
        settings = settings.copy()
        var_id = get_id_from_url(settings.get("weight"))
        if var_id:
            var_def = self._meta["table"][var_id]
            settings["weight"] = var_def["alias"]
        if "dashboard_deck" in settings:
            dashboard_deck = settings["dashboard_deck"]
            if dashboard_deck:
                # Any dashboard_deck setting is probably not valid for the new dataset.
                del settings["dashboard_deck"]
        return settings

    def create(self, site, dirname_or_filename, name=None, project=None):
        """Create dataset given a metadata file. Return the dataset entity."""
        if os.path.isdir(dirname_or_filename):
            filename = os.path.join(dirname_or_filename, "dataset-payload.json")
        else:
            filename = dirname_or_filename
        with open(filename, "rb") as f:
            new_meta = maybe_uncompress_and_load_json(f)
        if name:
            new_meta["body"]["name"] = name
        if project:
            new_meta["body"]["owner"] = project.entity_url
        ds = create_dataset_from_csv2(
            site, new_meta, None, verbose=self.verbose, gzip_metadata=True
        )
        return ds

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

    def _translate_hier_to_order(self, item=None):
        """
        Translate the variable folder hierarchy from the format downloaded
        by GET /datasets/<dataset-id>/variables/hier/ to the format used
        to POST to /datasets/ .
        """
        if item is None:
            item = self._meta["variables"]["hier"].copy()
        if isinstance(item, list):
            return [self._translate_hier_to_order(i) for i in item]
        elif isinstance(item, dict):
            # Expecting a dictionary with one key, which is the folder name
            # The value is a list of items inside that folder
            assert len(item) == 1
            folder_name = list(item.keys())[0]
            folder_contents = item[folder_name]
            assert isinstance(folder_contents, list)
            return {
                "entities": self._translate_hier_to_order(folder_contents),
                "group": folder_name,
            }
        else:
            # Expecting a relative URL in the form "../000716/"
            # Convert the variable ID to variable alias
            var_id = get_id_from_url(item)
            assert var_id
            var_def = self._meta["table"][var_id]
            return var_def["alias"]

    def folderize(self, ds):
        self._trace("Setting hierarchical order")
        hier = self._translate_hier(ds, self._meta["variables"]["hier"])
        ds.variables.hier.put({"graph": hier})

    def load(self, dirname):
        """Load combined metadata info from JSON files"""
        self._meta = {}

        def _load_file(base_filename):
            filename = os.path.join(dirname, base_filename)
            self._trace("Loading: %s", filename)
            with open(filename, "r") as f:
                return json.load(f)

        # Load main metadata
        main = _load_file("dataset-main.json")
        self._meta["main"] = main["body"]
        self._meta["catalogs"] = main["catalogs"]

        # Load settings
        self._meta["settings"] = _load_file("dataset-settings.json")["body"]

        # Load preferences
        self._meta["preferences"] = _load_file("dataset-preferences.json")["body"]

        # Variable-related info
        self._meta["variables"] = {}

        # Load list of variables for this dataset
        self._meta["variables"]["index"] = _load_file("dataset-variables.json")["index"]

        # Load details of derived variables
        self._meta["variables"]["detail"] = {}
        for var_url, var_info in six.iteritems(self._meta["variables"]["index"]):
            if not var_info["derived"]:
                continue
            var_id = get_id_from_url(var_url)
            self._meta["variables"]["detail"][var_id] = _load_file(
                "var-{}-detail.json".format(var_id)
            )["body"]

        # Load weights
        self._meta["variables"]["weights"] = _load_file("dataset-weights.json")["graph"]

        # Load variable hierarchy
        hier = _load_file("variables-hier.json")["graph"]
        self._meta["variables"]["hier"] = hier

        # Load table of variable definitions
        self._meta["table"] = _load_file("dataset-table.json")["metadata"]

        # Load missing_rules for variables with non-default missing_reason codes
        var_ids_needing_missing_rules = []
        for var_id, var_def in six.iteritems(self._meta["table"]):
            if self._var_has_non_default_missing_reasons(var_def):
                var_ids_needing_missing_rules.append(var_id)
        self._trace(
            "Loading missing_rules for %s variables", len(var_ids_needing_missing_rules)
        )
        for var_id in var_ids_needing_missing_rules:
            base_filename = "var-{}-missing-rules.json".format(var_id)
            missing_rules = _load_file(base_filename)["body"]["rules"]
            self._meta["table"][var_id]["missing_rules"] = missing_rules

    def remove_variables_with_duplicate_names(self):
        """
        Find any variables with duplicate names.
        For any group of duplicate-named variables, remove from the loaded metadata  all
        variables whose aliases end with "#".
        If that doesn't result in exactly one variable with that name, raise an error.
        """
        self._trace("Removing variables with duplicate names")
        name_varid_map = defaultdict(list)
        for var_id, var_def in six.iteritems(self._meta["table"]):
            name_varid_map[var_def["name"]].append(var_id)
        var_ids_to_delete = []
        error_msgs = []
        for name, var_ids in six.iteritems(name_varid_map):
            if len(var_ids) == 1:
                continue
            deletable_vars = []
            non_deletable_vars = []
            for var_id in var_ids:
                var_def = self._meta["table"][var_id]
                if var_def["alias"].endswith("#"):
                    deletable_vars.append(var_id)
                else:
                    non_deletable_vars.append(var_id)
            if len(non_deletable_vars) != 1:
                error_msgs.append(
                    "Could not delete extra vars named '{}': "
                    "{} deletable, {} non-deletable.".format(
                        name, len(deletable_vars), len(non_deletable_vars)
                    )
                )
            else:
                var_ids_to_delete.extend(deletable_vars)
        if error_msgs:
            raise RuntimeError("\n".join(error_msgs))
        self._delete_variables(var_ids_to_delete)

    def _delete_variables(self, var_ids_to_delete):
        """
        Remove each variable in var_ids_to_delete from whereever it appears in the
        loaded metadata. This fails if one of the variables to be deleted is referred to
        by a derived variable that is NOT on this list.
        """
        self._trace("Removing %s variables", len(var_ids_to_delete))
        self._check_var_dependencies(var_ids_to_delete)

        weight_var_id = get_id_from_url(self._meta["settings"]["weight"])
        if weight_var_id in var_ids_to_delete:
            self._trace("Removing weight variable: %s", weight_var_id)
            self._meta["settings"]["weight"] = None

        var_index = self._meta["variables"]["index"]
        var_url_prefix = self._meta["catalogs"]["variables"]
        for var_id in var_ids_to_delete:
            var_url = "{}{}/".format(var_url_prefix, var_id)
            self._trace("Removing from variable index: %s", var_url)
            del var_index[var_url]

        var_detail = self._meta["variables"]["detail"]
        for var_id in var_ids_to_delete:
            self._trace("Removing from variable detail: %s", var_id)
            del var_detail[var_id]

        weights_before = self._meta["variables"]["weights"]
        weights_after = [
            item
            for item in self._meta["variables"]["weights"]
            if get_id_from_url(item) not in var_ids_to_delete
        ]
        if weights_before != weights_after:
            self._trace(
                "Removing from weights: %s", set(weights_before) - set(weights_after)
            )
            self._meta["variables"]["weights"] = weights_after

        self._delete_var_ids_from_hierarchy(
            self._meta["variables"]["hier"], var_ids_to_delete
        )

        var_table = self._meta["table"]
        for var_id in var_ids_to_delete:
            self._trace("Removing from table: %s", var_id)
            del var_table[var_id]

    def _delete_var_ids_from_hierarchy(self, hier, var_ids_to_delete, level=0):
        # Modifies hier in-place
        if isinstance(hier, list):
            result = []
            for item in hier:
                if isinstance(item, six.string_types):
                    if get_id_from_url(item) in var_ids_to_delete:
                        self._trace("Level: %s Filtering from order: %s", level, item)
                        continue
                else:
                    assert isinstance(item, dict)
                    self._delete_var_ids_from_hierarchy(
                        item, var_ids_to_delete, level=level + 1
                    )
                result.append(item)
            if hier != result:
                hier[:] = result
        elif isinstance(hier, dict):
            for value in six.itervalues(hier):
                self._delete_var_ids_from_hierarchy(
                    value, var_ids_to_delete, level=level + 1
                )
        else:
            raise AssertionError(
                "Unexpected data type while traversing hier: {}".format(hier)
            )

    def _check_var_dependencies(self, var_ids_to_delete):
        """
        Raise RuntimeError if any of the variables in var_ids_to_delete has a derivation
        expression depending on it, and the referring variable is not also in that list.
        """
        error_msgs = []
        for var_id, var_detail in six.iteritems(self._meta["variables"]["detail"]):
            expr = var_detail.get("derivation", {"args": []})
            for arg in expr["args"]:
                arg_var_id = get_id_from_url(arg.get("variable"))
                if arg_var_id in var_ids_to_delete and var_id not in var_ids_to_delete:
                    error_msgs.append(
                        "Variable {} is referred to by variable {}".format(
                            arg_var_id, var_id
                        )
                    )
        if error_msgs:
            raise RuntimeError("Cannot delete variables:\n" + "\n".join(error_msgs))

    def report(self):
        # general info
        meta = self._meta
        print("Dataset ID:", meta["main"]["id"])
        print("name:", meta["main"]["name"])
        print("description:", meta["main"]["description"])
        print("size:")
        print("  columns:", meta["main"]["size"]["columns"])
        print("  rows:", meta["main"]["size"]["rows"])
        print("  unfiltered_rows:", meta["main"]["size"]["unfiltered_rows"])
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

    def anonymize_payload(self, dirname):
        filename = os.path.join(dirname, "dataset-payload.json")
        print("Reading", filename)
        with open(filename, "rb") as f:
            payload = maybe_uncompress_and_load_json(f)
        print("Obfuscating...")
        # Save the name so it doesn't get scrambled
        name = payload["body"]["name"]
        obfuscate_metadata(payload)
        payload["body"]["name"] = name
        print("Writing", filename)
        with open(filename, "w") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")


def do_get(config, args):
    ds_id = args["<ds-id>"]
    dirname = args["<dirname>"]
    site = connect_api(config, args)
    meta = MetadataModel(verbose=args["-v"])
    meta.get(site, ds_id, dirname)
    if args["-i"]:
        import IPython

        IPython.embed()


def do_info(config, args):
    dirname = args["<dirname>"]
    meta = MetadataModel(verbose=args["-v"])
    meta.load(dirname)
    meta.report()


def do_create_payload(config, args):
    dirname = args["<dirname>"]
    meta = MetadataModel(verbose=args["-v"])
    meta.load(dirname)
    meta.create_payload(dirname, name=args["--name"])


def do_anonymize_payload(config, args):
    dirname = args["<dirname>"]
    meta = MetadataModel(verbose=args["-v"])
    meta.anonymize_payload(dirname)


def do_create(config, args):
    dirname_or_filename = args["<dirname-or-filename>"]
    site = connect_api(config, args)
    meta = MetadataModel(verbose=args["-v"])
    meta.create(site, dirname_or_filename, name=args["--name"])


def _generate_unique_subvar_aliases(var_meta):
    """
    Modify variable metadata in-place, replacing the alias of each subvarible
    (if any) with a guaranteed unique identifier.
    """
    if "subreferences" not in var_meta:
        return
    for subref in six.itervalues(var_meta["subreferences"]):
        subref["alias"] = uuid.uuid4().hex


def do_addvar(config, args):
    ds_id = args["<ds-id>"]
    filename = args["<filename>"]
    verbose = args["-v"]
    site = connect_api(config, args)
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
        log.info(
            "Creating variable '%s' with alias %s", var_def["name"], var_def["alias"]
        )
    t0 = time.time()
    variables = ds.variables
    t1 = time.time()
    log.info("GET /variables duration: %s", t1 - t0)
    try:
        variables.create({"body": var_def})
    finally:
        log.info("POST /variables duration: %s", time.time() - t1)


def do_folderize(config, args):
    ds_id = args["<ds-id>"]
    dirname = args["<dirname>"]
    site = connect_api(config, args)
    ds_url = "{}{}/".format(site.datasets["self"], ds_id)
    response = site.session.get(ds_url)
    ds = response.payload
    meta = MetadataModel(verbose=args["-v"])
    meta.load(dirname)
    meta.folderize(ds)


def do_list_datasets(config, args):
    site = connect_api(config, args)
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


def do_raw_request(config, args):
    method = args["<method>"]
    uri_path = args["<uri-path>"]
    filename = args["<filename>"]
    site = connect_api(config, args)
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


def do_sample_config(config, args):
    print(
        textwrap.dedent(
            """
    profiles:
        local:
            api_url: 'https://local.crunch.io:8443/api'
            users:
                default:
                    username: 'captain@crunch.io'
                    password: 'asdfasdf'
    """
        ).strip()
    )


if __name__ == "__main__":
    sys.exit(main())