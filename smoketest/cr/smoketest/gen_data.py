#!/usr/bin/env python
"""
Generate CSV data to append to a Crunch dataset.

Usage:
    gen_data.py [options] <input-filename-json> <output-filename-csv>

Options:
    --sparse-data       Make > 80% of the values system missing
    --num-rows=NUMROWS  [default: 10]
    --pk=ALIAS

If <output-filename-csv> is "-" then standard output is used.
If a --pk (Primary Key) alias is identified, that variable will be given random
integer values between 1 and 999999999.

Example:
    ./gen_data.py data/dataset.json big-data/dataset.csv
"""
from __future__ import print_function
from collections import OrderedDict
import csv
import datetime
import json
import random
import string
import sys
import tempfile
import time

import docopt
import six

CHARACTERS = string.ascii_letters + string.digits

DATETIME_FORMATS = {
    'Y': '%Y',
    'M': '%Y-%m',
    'D': '%Y-%m-%d',
    'h': '%Y-%m-%dT%H',
    'm': '%Y-%m-%dT%H:%M',
    's': '%Y-%m-%dT%H:%M:%S',
    'ms': '%Y-%m-%dT%H:%M:%S.%f',  # needs 3 rightmost digits trimmed
}


def _gen_random_value(vardef, pk=None, sparse_data=False):
    if pk == vardef['alias']:
        assert vardef['type'] == 'numeric'
        return random.randint(1, 999999999)
    if sparse_data and random.random() <= 0.9:
        # Assume empty string in CSV file gets treated as system missing
        return ""
    if 'categories' in vardef:
        return str(random.choice(_get_category_ids(vardef)))
    if vardef['type'] == 'text':
        return _gen_random_text()
    if vardef['type'] == 'numeric':
        return _gen_random_number(vardef.get('missing_rules', {}))
    if vardef['type'] == 'datetime':
        resolution = vardef['resolution']
        format = DATETIME_FORMATS[resolution]
        t = _gen_random_datetime()
        s = t.strftime(format)
        if resolution == 'ms':
            s = s[:-3]
        return s
    raise ValueError("Can't handle variable of type {}".format(vardef['type']))


def _get_category_ids(vardef):
    return [cat['id'] for cat in vardef['categories']]


def _gen_random_text():
    return ''.join(random.choice(CHARACTERS) for _ in six.moves.range(8))


def _gen_random_number(missing_rules):
    potential_values = [r['value'] for r in six.itervalues(missing_rules)]
    potential_values.extend(random.randrange(100) for _ in six.moves.range(10))
    return random.choice(potential_values)


def _gen_random_datetime():
    start_timestamp = 946702800.0  # 2000-01-01
    t = random.uniform(start_timestamp, time.time())
    return datetime.datetime.utcfromtimestamp(t)


def _iter_metadata(metadata, skip_derived=True):
    """
    Yield (alias, vardef) for all variables or sub-variables in the metadata.
    """
    for vardef in six.itervalues(metadata):
        if skip_derived and vardef.get('derived', None):
            continue
        if 'subvariables' in vardef:
            subreferences = vardef['subreferences']
            for subvar_id in vardef['subvariables']:
                subvar_def = subreferences[subvar_id].copy()
                subvar_def['categories'] = vardef['categories']
                yield (subvar_def['alias'], subvar_def)
        else:
            yield (vardef['alias'], vardef)


def open_csv_writefile(filename):
    """
    Open a disk file for writing usable by csv.writer
    Details can depend on the Python version.
    """
    if six.PY2:
        return open(filename, 'wb')
    return open(filename, 'w', newline='')


def open_csv_tempfile(prefix='tmp', suffix='.csv', dir=None):
    """
    Open a temporary file usable by csv.writer
    Details can depend on the Python version.
    The file will be automatically deleted when it is closed.
    """
    if six.PY2:
        return tempfile.TemporaryFile(mode='w+b', suffix=suffix, prefix=prefix,
                                      dir=dir)
    return tempfile.TemporaryFile(mode='w+', newline='', suffix=suffix,
                                  prefix=prefix, dir=dir)


def write_random_rows(metadata, pk, num_rows, f, sparse_data=False):
    """
    metadata: Object returned by get_var_defs() containing variable definitions
    pk: Name of primary key alias, or None if no PK
    num_rows: Number of CSV rows to write
    f: File returned from open_csv_writefile() or open_csv_tempfile()
    """
    w = csv.writer(f)
    w.writerow([alias for (alias, _) in _iter_metadata(metadata)])
    for i in six.moves.range(num_rows):
        row = [
            _gen_random_value(vardef, pk=pk, sparse_data=sparse_data)
            for (_, vardef) in _iter_metadata(metadata)
        ]
        w.writerow(row)


def main():
    args = docopt.docopt(__doc__)
    input_filename = args['<input-filename-json>']
    output_filename = args['<output-filename-csv>']
    num_rows = int(args['--num-rows'])
    with open(input_filename) as f:
        schema = json.load(f, object_pairs_hook=OrderedDict)
    metadata = schema['body']['table']['metadata']
    if output_filename == '-':
        f = sys.stdout
    else:
        f = open_csv_writefile(output_filename)
    try:
        write_random_rows(
            metadata, args['--pk'], num_rows, f,
            sparse_data=args['--sparse-data'])
    finally:
        f.flush()
        if output_filename != '-':
            f.close()


if __name__ == '__main__':
    sys.exit(main())
