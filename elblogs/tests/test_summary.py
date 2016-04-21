import os
import subprocess

from unittest import TestCase

from elblogs.analyze import format_summary, analyze_log
from elblogs.files import load_log
from elblogs.scripts.summary import elb_summary_stats


HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(HERE, "fixtures")


summary_for_Jan1 = {
    'mean_req_time': 0.06947418906236669,
    'pct_500s': 0.008531695247845746,
    'sum_500s': 1,
    'sum_504s': 0,
    'max_req_time': 4.1998690000000005,
    'pct_under_200ms': 99.889087961778,
    'sum_reqs': 11721
}


class TestSummary(TestCase):

    def test_analyze_log(self):
        lf = os.path.join(FIXTURES_DIR, "2016", "01", "01",
            "910774676937_elasticloadbalancing_eu-west-1_eu-vpc_20160101T0000Z_46.51.204.253_3y18pz09.log")
        anal = analyze_log(load_log(lf))
        self.assertEqual(anal,
            {
                'count_504s': 0,
                'count_requests': 279,
                'under_200ms': 279,
                'mean_time': 0.09160322580645158,
                'max_time': 0.15662500000000001,
                'count_500s': 0
            })

    def test_format_summary(self):
        self.assertEqual(format_summary(summary_for_Jan1),
             {
                "Mean request time": 0.069,
                "5XX error rate (%)": 0.0085,
                "Number of 5XX responses": "1",
                "Number of 504 responses": "0",
                "Max request time": 4.200,
                "Requests under 200ms (%)": 99.9,
                "Total request count": "11,721"
            })

    def test_e2e_function(self):
        summary, errs = elb_summary_stats("20160101", "20160101", path=FIXTURES_DIR)
        self.assertEqual(summary, summary_for_Jan1)

    def test_e2e_script(self):
        out = subprocess.call(["elb.summary", FIXTURES_DIR, "1", "20160102"])
        print summary_for_Jan1

    def test_e2e_script_today(self):
        out = subprocess.call(["elb.summary", FIXTURES_DIR, "3"])
