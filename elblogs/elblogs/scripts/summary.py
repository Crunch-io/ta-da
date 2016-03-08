from ..files import find_dot
from ..analyze import analyze_log, summarize

def elb_summary_stats(start=None, end=None):
    ''' Find log files, possibly for a time range, read them, and return the
        indicated quantities for all.
    '''
    files = find_dot(start, end)
    results = {}
    for f in files:
        results[f] = analyze_log(load_log(f))
    return summarize(results)
