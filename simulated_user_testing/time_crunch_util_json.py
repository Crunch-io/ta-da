# Time the performance of JSON helpers in crunch_util
from __future__ import print_function
import gzip
import io
import json
import shutil
import time

import six

import crunch_util


class DevNull:
    def write(self, b):
        return len(b)


devnull = DevNull()


def time_stream_and_compress_json_no_tempfile(filename):
    print("time_stream_and_compress_json_no_tempfile:", filename)
    with io.open(filename, "r", encoding="utf-8") as f:
        obj = json.load(f)
    t0 = time.time()
    with crunch_util.stream_and_compress_json(obj) as f:
        shutil.copyfileobj(f, devnull)
    print(time.time() - t0)


def time_stream_and_compress_json_use_tempfile(filename):
    print("time_stream_and_compress_json_use_tempfile:", filename)
    with io.open(filename, "r", encoding="utf-8") as f:
        obj = json.load(f)
    t0 = time.time()
    with crunch_util.stream_and_compress_json(obj, use_tempfile=True) as f:
        shutil.copyfileobj(f, devnull)
    print(time.time() - t0)


def time_stream_and_compress_json_use_ram(filename):
    print("time_stream_and_compress_json_use_ram:", filename)
    with io.open(filename, "r", encoding="utf-8") as f:
        obj = json.load(f)
    t0 = time.time()
    f = io.BytesIO()
    with gzip.GzipFile(mode="wb", fileobj=f) as g:
        g.write(json.dumps(obj).encode("utf-8"))
    shutil.copyfileobj(f, devnull)
    print(time.time() - t0)


def time_uncompress_and_load_json_save_ram(filename):
    print("time_uncompress_and_load_json_save_ram:", filename)
    t0 = time.time()
    with open(filename, "rb") as f:
        obj = crunch_util.maybe_uncompress_and_load_json(f)
    print(time.time() - t0)
    assert isinstance(obj, dict)
    assert len(obj) > 0


def time_uncompress_and_load_json_use_ram(filename):
    print("time_uncompress_and_load_json_use_ram:", filename)
    t0 = time.time()
    f = open(filename, "rb")
    try:
        if filename.endswith(".gz"):
            with gzip.GzipFile(mode="rb", fileobj=f) as g:
                json_str = g.read()
                if not six.PY2:
                    json_str = json_str.decode("utf-8")
        else:
            json_str = f.read()
            if not six.PY2:
                json_str = json_str.decode("utf-8")
        obj = json.loads(json_str)
    finally:
        f.close()
    print(time.time() - t0)
    assert isinstance(obj, dict)
    assert len(obj) > 0


if __name__ == "__main__":
    time_stream_and_compress_json_no_tempfile(
        "metadata/Profiles-plus-GB-Feb-2019-metadata.json"
    )
    time_stream_and_compress_json_use_tempfile(
        "metadata/Profiles-plus-GB-Feb-2019-metadata.json"
    )
    time_stream_and_compress_json_use_ram(
        "metadata/Profiles-plus-GB-Feb-2019-metadata.json"
    )

    time_uncompress_and_load_json_save_ram(
        "metadata/Profiles-plus-GB-Feb-2019-metadata.json"
    )
    time_uncompress_and_load_json_save_ram(
        "metadata/Profiles-plus-GB-Feb-2019-metadata.json.gz"
    )
    time_uncompress_and_load_json_use_ram(
        "metadata/Profiles-plus-GB-Feb-2019-metadata.json"
    )
    time_uncompress_and_load_json_use_ram(
        "metadata/Profiles-plus-GB-Feb-2019-metadata.json.gz"
    )
