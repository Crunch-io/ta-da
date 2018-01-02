"""
Big Dataset data helper script

Usage:
    ds.data create
    ds.data append
"""
from __future__ import print_function
import docopt


def main():
    args = docopt.docopt(__doc__)
