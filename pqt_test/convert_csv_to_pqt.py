import gc
import os
import sys
from docopt import docopt

import pandas as pd
from pyarrow import csv as pa_csv
import pyarrow.parquet as pq
import pyarrow as pa

import numpy as np
import ujson
from memory_profiler import memory_usage
# monkeypatch
pd.arrays.IntegerArray.__arrow_array__ = lambda self, type: pa.array(self._data, mask=self._mask, type=type)


CATEGORICAL_ATYPE = pa.int16()

ATYPE_LOOKUP = {
    "categorical": CATEGORICAL_ATYPE,
    "categorical_array": CATEGORICAL_ATYPE,
    "multiple_response": CATEGORICAL_ATYPE,
    "numeric": pa.float64(),
    "text": pa.string(),
}

CATEGORICAL_PTYPE = pd.Int16Dtype()

PTYPE_LOOKUP = {
    "categorical": CATEGORICAL_PTYPE,
    "categorical_array": CATEGORICAL_PTYPE,
    "multiple_response": CATEGORICAL_PTYPE,
    "numeric": np.float64,
    "text": np.str,
}

CATEGORICAL_DTYPE = np.int16

DTYPE_LOOKUP = {
    "categorical": CATEGORICAL_DTYPE,
    "categorical_array": CATEGORICAL_DTYPE,
    "multiple_response": CATEGORICAL_DTYPE,
    "numeric": np.float64,
    "text": np.str,
}


CHUNKSIZE = 100

def types_from_crunch_metadata(metadata, columns):
    dtypes = {'A': {}, 'P': {}, 'D':{}}
    categorical_types = {'A':ATYPE_LOOKUP['categorical'], 'P': PTYPE_LOOKUP['categorical']}
    for column_name, schema in metadata['body']['table']['metadata'].iteritems():
        subvariables = schema.get('subvariables')
        if subvariables:
            for subvariable in subvariables:
                alias = subvariable['alias']
                if alias not in columns:
                    # subvariables are all-or-nothing
                    break
                dtypes['A'][alias] = categorical_types['A']
                dtypes['P'][alias] = categorical_types['P']
                dtypes['D'][alias] = CATEGORICAL_DTYPE
                #print alias
        elif column_name not in columns:
            continue
        else:
            dtypes['A'][column_name] = ATYPE_LOOKUP[schema['type']]
            dtypes['P'][column_name] = PTYPE_LOOKUP[schema['type']]
            dtypes['D'][column_name] = DTYPE_LOOKUP[schema['type']]
            #dtypes['M'][column_name] = schema
    return dtypes



def load_columns_to_memory_map(src, columns, dtypes, map_dir):

    COLUMNS_PER_CHUNK = 100
    chunks = len(columns)/COLUMNS_PER_CHUNK + 1

    for chunk in range(chunks):
        print 'mmmap chunk %s:%s'%(chunk, chunks)
        start = chunk * COLUMNS_PER_CHUNK
        c_columns = columns[start:start + COLUMNS_PER_CHUNK]

        # only grab columns we haven't yet parsed
        chunk_columns = []
        for i, column in enumerate(c_columns):
            column_fn = map_dir + "/{}.npy".format(column)
            if not os.path.exists(column_fn):
                chunk_columns.append(column)

        if not chunk_columns:
            continue

        table = pd.read_csv(src, usecols=chunk_columns, dtype={c: dtypes[c] for c in chunk_columns})
        for i, column in enumerate(chunk_columns):
            column_fn = map_dir+"/{}.npy".format(column)
            if i % 20 == 0:
                print i, column
            array = table[column].values
            try:
                mf = np.memmap(column_fn, shape=array.shape, mode="w+", dtype=array.dtype)
                mf[:] = array[:]
            except (TypeError, ValueError):
                array = array.fillna(-1)._data
                mf = np.memmap(column_fn, shape=array.shape, mode="w+", dtype=array.dtype)
                mf[:] = array[:]
            # save yee
            del mf

import psutil

def memmap_columns(columns, dtypes, map_dir):
    proc = psutil.Process()
    mfs = {}
    for i, column in enumerate(columns):
        if i%10000 == 0:
            print i, column
            of = proc.open_files()
            print 'open fds', len(of)
        column_fn = map_dir+"/{}.npy".format(column)
        mfs[column] = np.memmap(column_fn, dtype=dtypes[column], mode="r")
    return mfs

def memmap_column(column, schema, map_dir):
    column_fn = map_dir+"/{}.npy".format(column)
    return np.memmap(column_fn, dtype=schema, mode="r")


def create_memory_map_files(src, column_names, pandas_dtypes, map_dir):

    if not os.path.exists(map_dir):
        os.makedirs(map_dir)

    def _load_memmaps(src, columns, pandas_dtypes, map_dir):
        load_columns_to_memory_map(src, columns, pandas_dtypes, map_dir)

    print 'memmap file creation'

    #load_columns_to_memory_map(src, column_names, pandas_dtypes, map_dir)

    import multiprocessing
    NUMPYING_THREADS = 25
    threads = []
    chunk_size = len(column_names) / (NUMPYING_THREADS)
    for i in range(NUMPYING_THREADS):
        start = chunk_size * i
        #print 'chunk', i
        sys.stdout.flush()
        thread_columns = column_names[start: start + chunk_size]

        t = multiprocessing.Process(target=_load_memmaps, args=(src, thread_columns , pandas_dtypes, map_dir))
        threads.append(t)
        t.start()

    print 'waiting for memmap completion'
    for t in threads:
        t.join()


class MemMappedColumns(object):
    def __init__(self, column_names, schemas, map_dir):
        self._column_index = {i: c for i, c in enumerate(column_names)}
        self._column_names = column_names
        self._map_dir = map_dir
        self._schemas = schemas
        self._proc = psutil.Process()


    def __iter__(self):
        for name in self._column_names:
            memmap = memmap_column(column_name, self._schemas[column_name], self._map_dir)
            yield pa.array(memmap)
            memmap._mmap.close()

    # def __getitem__(self, item):
    #     #of = self._proc.open_files()
    #     #print 'open fds', len(of)
    #
    #     column_name = self._column_index[item]
    #     return self._array(column_name)
    #
    def __len__(self):
        return len(self._column_index)

def convert_csv(metadata, src, dst):

    # read the headers from the csv file
    with open(src) as f:
        columns = f.readline().split(',')

    print 'computing column types'
    sys.stdout.flush()
    schemas = types_from_crunch_metadata(metadata, set(columns))
    pandas_dtypes = schemas['P']

    # only consider columns we found in the schema
    column_names = [c for c in columns if c in schemas['P']]

    #column_names = column_names[:10000]

    print memory_usage()

    map_dir = os.path.dirname(src) + '/map'

    print 'creating memory map files...'
    #create_memory_map_files(src, column_names, pandas_dtypes, map_dir)

    print 'loading memory map for columns to memory...'
    #columns = memmap_columns(column_names, schemas['D'], map_dir)

    print 'making a pa table'
    print memory_usage()

    a_schemas = schemas['A']
    fields = [pa.field(name, a_schemas[name]) for name in column_names]
    pa_schema = pa.schema(fields)

    columns = MemMappedColumns(column_names, schemas['D'], map_dir)

    pa_tab = pa.Table.from_arrays(columns, schema=pa_schema)
    print 'writing to pqt file'
    print memory_usage()
    parquet_writer = pq.ParquetWriter(dst, pa_schema, use_dictionary=False)
    parquet_writer.write_table(pa_tab)
    print memory_usage()
    print 'done.'





if __name__ == "__main__":
    helpstr = """Copy crunch.io s3 data from one set of buckets to another. Run this on a system that has access to the source data.

    Usage:
        %(script)s (-h | --help)
        %(script)s <metadata_json> <src_csv> [<dst_pqt>]

    Options:
    <metadata_json> crunch metadata to pull schema from
    <src_csv>       source csv file
    <dst_pqt>       (optional) destination csv file, if this is missing, the script will use src_csv and replace .csv with .pqt
    """


    arguments = docopt(helpstr)
    metadata = arguments['<metadata_json>']
    src_csv = arguments['<src_csv>']
    dst_pqt = arguments.get('<dst_pqt>', '.'.join(src_csv.split('.')[:-1]) + '.pqt')

    print 'loading metadata into memories'
    with open(metadata) as f:
        metadata = ujson.load(f)

    for column_name, var_def in metadata['body']['table']['metadata'].items():
        if 'derivation' in var_def:
            del metadata['body']['table']['metadata'][column_name]

    gc.collect()

    import time
    before = time.time()
    convert_csv(metadata, src_csv, dst_pqt)

    print "%.2f " % (time.time() - before)
