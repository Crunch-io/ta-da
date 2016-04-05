import os
import subprocess

from unittest import TestCase

from elblogs.analyze import format_summary
from elblogs.scripts.summary import elb_summary_stats


HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(HERE, "fixtures")


summary_for_Jan1 = {
    'mean_req_time': 0.06947418906236669,
    'pct_500s': 0.008531695247845746,
    'sum_500s': 1,
    'sum_504s': 0,
    'max_req_time': 4.1998690000000005,
    'sum_reqs': 11721
}


class TestSummary(TestCase):

    def test_format_summary(self):
        self.assertEqual(format_summary(summary_for_Jan1),
             {
                "Mean request time": 0.069,
                "5XX error rate (%)": 0.0085,
                "Number of 5XX responses": "1",
                "Number of 504 responses": "0",
                "Max request time": 4.200,
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
