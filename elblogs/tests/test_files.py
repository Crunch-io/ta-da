import contextlib
import os
import shutil
import subprocess

from tempfile import mkdtemp
from unittest import TestCase

from elblogs.files import find_dot, file_in_date_range, extract_dataset_id, logfile_to_datasets, get_error_entries


HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(HERE, "fixtures")

def file_line_count(filename):
    with open(filename) as f:
        count = sum(1 for line in f)
    return count


@contextlib.contextmanager
def tempdir(cleanup=True, **kwargs):
    tmpdir = mkdtemp(**kwargs)
    try:
        yield tmpdir
    finally:
        if cleanup:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestFiles(TestCase):

    def assertLength(self, obj, expected):
        self.assertEqual(len(obj), expected)

    def test_file_in_date_range(self):
        f1 = '9_elb_eu_eu_20151101T2300Z_ip_hash.log'
        self.assertTrue(file_in_date_range(f1, 20151030))
        self.assertTrue(file_in_date_range(f1, 20151030, 20160101))
        self.assertTrue(file_in_date_range(f1, 20151101, 20151101))
        self.assertTrue(file_in_date_range(f1, 20151101, 20151101, 2100))
        self.assertTrue(file_in_date_range(f1, 20151101, 20151101, 2130, 2300))
        self.assertFalse(file_in_date_range(f1, 20151130))
        self.assertFalse(file_in_date_range(f1, 20151030, 20151031))
        self.assertFalse(file_in_date_range(f1, 20151101, 20151101, 2310))
        self.assertFalse(file_in_date_range(f1, 20151101, 20151101, 2130, 2259))

    def test_find_dot(self):
        paths = ["2015/12/30", "2015/12/31", "2016/01/01", "2016/01/02", "2016/01/03", "2017/08/17"]
        nlogs = [48, 46, 46, 45, 0, 1]  # Apparently they aren't all 24*2, but that's ok
        for i, p in enumerate(paths):
            self.assertLength(find_dot(path=os.path.join(FIXTURES_DIR, p)),
                nlogs[i])
        self.assertLength(find_dot(path=FIXTURES_DIR), sum(nlogs))

    def test_find_dot_in_range(self):
        self.assertLength(find_dot("20151130", "20151230", path=FIXTURES_DIR),
            48)
        self.assertLength(find_dot("20151130T1200", "20151230", path=FIXTURES_DIR),
            48)
        self.assertLength(find_dot("20151130", "20151230T1100", path=FIXTURES_DIR),
            24)
        self.assertLength(find_dot("20151230T1100", "20151230T1100", path=FIXTURES_DIR),
            2)

    def test_get_dataset_id(self):
        str1 = '2015-12-30T00:25:16.917040Z eu-vpc 73.223.89.40:61889 10.30.0.5:443 0.000045 0.014786 0.000023 200 200 0 775 "GET https://beta.crunch.io:443/api/datasets/f468c1b325c44a8cbe5d6a4663f4be09/ HTTP/1.1" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36" ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2'
        str2 = '2015-12-30T00:25:16.917040Z eu-vpc 73.223.89.40:61889 10.30.0.5:443 0.000045 0.014786 0.000023 200 200 0 775 "GET https://beta.crunch.io:443/api/datasets/ HTTP/1.1" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36" ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2'
        self.assertEqual(extract_dataset_id(str1),
            'f468c1b325c44a8cbe5d6a4663f4be09')
        self.assertEqual(extract_dataset_id(str2),
            '__none__')

    def test_reshape_datasets(self):
        with tempdir() as testdir:
            lfile = '2015/12/30/910774676937_elasticloadbalancing_eu-west-1_eu-vpc_20151230T0000Z_46.51.204.253_5kghxkum.log'
            lfile = os.path.join(FIXTURES_DIR, lfile)
            logfile_to_datasets(lfile, testdir)

            outfiles = find_dot(path=testdir)
            filelengths = [file_line_count(f) for f in outfiles]
            print filelengths
            self.assertEqual(sum(filelengths), file_line_count(lfile))

    def test_reshape_many_files(self):
        with tempdir() as testdir:
            lfiles = find_dot(path=os.path.join(FIXTURES_DIR, "2015/12/30"))
            logfile_to_datasets(lfiles, testdir)

            outfiles = find_dot(path=testdir)
            filelengths = [file_line_count(f) for f in outfiles]
            originallengths = [file_line_count(f) for f in lfiles]
            self.assertEqual(sum(filelengths), sum(originallengths))

            # Now assert that a dataset file is all that dataset
            onefile = os.path.join(testdir, "1bf3f15e070541b88dc71f4dc5637819.log")
            with open(onefile) as onebf3f:
                for line in onebf3f:
                    self.assertEqual(extract_dataset_id(line),
                        "1bf3f15e070541b88dc71f4dc5637819")

    def test_reshape_script(self):
        with tempdir() as testdir:
            out = subprocess.call(["elb.ds", ".", testdir, "20151231", "20151231"])
            lfiles = find_dot(path=os.path.join(FIXTURES_DIR, "2015/12/31"))

            outfiles = find_dot(path=testdir)
            filelengths = [file_line_count(f) for f in outfiles]
            originallengths = [file_line_count(f) for f in lfiles]
            self.assertEqual(sum(filelengths), sum(originallengths))

            # Check our file that tracks what log files have been processed
            self.assertEqual(file_line_count(os.path.join(testdir, "processed_logs")),
                len(lfiles))

            # Now test that if I run it again, we won't get dupes
            out = subprocess.call(["elb.ds", FIXTURES_DIR, testdir, "20151231", "20151231"])
            filelengths = [file_line_count(f) for f in find_dot(path=testdir)]
            self.assertEqual(sum(filelengths), sum(originallengths))
            # Check that processed_logs is unchanged
            self.assertEqual(file_line_count(os.path.join(testdir, "processed_logs")),
                len(lfiles))

            # And it will add but not duplicate if the range overlaps
            lfiles2 = find_dot("20151231", "20160101",
                path=os.path.join(FIXTURES_DIR))
            out = subprocess.call(["elb.ds", FIXTURES_DIR, testdir, "20151231T1200", "20160101"])
            filelengths = [file_line_count(f) for f in find_dot(path=testdir)]
            neworiginallen = [file_line_count(f) for f in lfiles2]

            self.assertEqual(sum(filelengths), sum(neworiginallen))
            # Check that processed_logs is unchanged
            self.assertEqual(file_line_count(os.path.join(testdir, "processed_logs")),
                len(lfiles2))

    def test_reshape_script_no_end(self):
        with tempdir() as testdir:
            out = subprocess.call(["elb.ds", FIXTURES_DIR, testdir, "20160102"])
            # Collect the actual files from the remaining days
            lfiles = find_dot(path=os.path.join(FIXTURES_DIR, "2016/01/02"))
            lfiles += find_dot(path=os.path.join(FIXTURES_DIR, "2017"))
            # Collect the files from the reshaped directory
            outfiles = find_dot(path=testdir)
            filelengths = [file_line_count(f) for f in outfiles]
            originallengths = [file_line_count(f) for f in lfiles]
            self.assertEqual(sum(filelengths), sum(originallengths))

    def test_find_error_entries(self):
        jan2 = find_dot("20160102", "20160102")
        errs = []
        for f in jan2:
            errs += get_error_entries(f)
        self.assertLength(errs, 3)