from docopt import docopt
import pyarrow.parquet as pq


if __name__ == "__main__":
    helpstr = """Copy crunch.io s3 data from one set of buckets to another. Run this on a system that has access to the source data.

    Usage:
        %(script)s (-h | --help)
        %(script)s <metadata_json> <src_pqt>

    Options:
    <metadata_json> crunch metadata to pull schema from
    <src_pqt>       source pqt file
    """


    arguments = docopt(helpstr)
    metadata = arguments['<metadata_json>']
    src_pqt = arguments['<src_pqt>']

    schema = pq.read_schema(src_pqt)
    import ipdb; ipdb.set_trace()

    pandas_metadata = schema.pandas_metadata["columns"]

    parquet_file = pq.ParquetFile(src_pqt)
    #col_index = parquet_file.reader.column_name_idx("pdlc_age")
    col_index = schema.get_field_index('pdlc_age')
    column = parquet_file.reader.read_column(col_index)
    import ipdb; ipdb.set_trace()