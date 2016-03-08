import os

from elblogs.files import find_dot, file_in_date_range, extract_dataset_id


HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(HERE, "fixtures")

def test_file_in_date_range():
    f1 = '9_elb_eu_eu_20151101T2300Z_ip_hash.log'
    assert file_in_date_range(f1, 20151030)
    assert file_in_date_range(f1, 20151030, 20160101)
    assert file_in_date_range(f1, 20151101, 20151101)
    assert file_in_date_range(f1, 20151101, 20151101, 2100)
    assert file_in_date_range(f1, 20151101, 20151101, 2130, 2300)
    assert not file_in_date_range(f1, 20151130)
    assert not file_in_date_range(f1, 20151030, 20151031)
    assert not file_in_date_range(f1, 20151101, 20151101, 2310)
    assert not file_in_date_range(f1, 20151101, 20151101, 2130, 2259)

def test_find_dot():
    paths = ["2015/12/30", "2015/12/31", "2016/01/01", "2016/01/02", "2016/01/03", "2016/01/04", "2016/01/05"]
    nlogs = [48, 46, 46, 45, 45, 48, 48]  # Apparently they aren't all 24*2, but that's ok
    for i, p in enumerate(paths):
        dir1 = find_dot(path=os.path.join(FIXTURES_DIR, p))
        assert len(dir1) == nlogs[i], len(dir1)
    assert len(find_dot(path=FIXTURES_DIR)) == sum(nlogs)

def test_find_dot_in_range():
    assert len(find_dot("20151130", "20151230", path=FIXTURES_DIR)) == 48
    assert len(find_dot("20151130T1200", "20151230", path=FIXTURES_DIR)) == 48
    assert len(find_dot("20151130", "20151230T1100", path=FIXTURES_DIR)) == 24
    assert len(find_dot("20151230T1100", "20151230T1100", path=FIXTURES_DIR)) == 2

def test_get_dataset_id():
    str1 = '2015-12-30T00:25:16.917040Z eu-vpc 73.223.89.40:61889 10.30.0.5:443 0.000045 0.014786 0.000023 200 200 0 775 "GET https://beta.crunch.io:443/api/datasets/f468c1b325c44a8cbe5d6a4663f4be09/ HTTP/1.1" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36" ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2'
    str2 = '2015-12-30T00:25:16.917040Z eu-vpc 73.223.89.40:61889 10.30.0.5:443 0.000045 0.014786 0.000023 200 200 0 775 "GET https://beta.crunch.io:443/api/datasets/ HTTP/1.1" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36" ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2'
    assert extract_dataset_id(str1) == 'f468c1b325c44a8cbe5d6a4663f4be09'
    assert extract_dataset_id(str2) == '__none__'
