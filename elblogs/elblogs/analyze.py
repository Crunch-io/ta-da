def analyze_log(data):
    '''Given a log data.frame-like dict, aggregate'''
    results = {}
    results['count_requests'] = len(data['elb'])
    results['stream_requests'] = len([x for x in data['request_url'] if '/stream/' in x])
    times = zip(data['request_processing_time'], data['backend_processing_time'], data['response_processing_time'])
    total_time = [sum(list(x)) for x in times]
    results['mean_time'] = mean([x for x in total_time if x > 0])
    results['under_200ms'] = len([x for x in total_time if x > 0 and x <= .2])
    results['max_time'] = max(total_time)
    results['count_500s'] = len([x for x in data['elb_status_code']
        if x >= 500.0])
    results['count_504s'] = len([x for x in data['elb_status_code']
        if x == 504])
    return results

def summarize(data):
    '''Compute some aggregates'''
    quantities = ['count_requests', 'mean_time', 'max_time', 'count_500s',
        'count_504s', 'under_200ms', 'stream_requests']
    ## First, reshape the data into something useful
    df = dict(zip(quantities, zip(*([v[i] for i in quantities] for v in data.values()))))

    out = {
        "sum_reqs": sum(df.get('count_requests', [])),
        "stream_reqs": sum(df.get('stream_requests', [])),
        "sum_500s": sum(df.get('count_500s', [])),
        "sum_504s": sum(df.get('count_504s', [])),
    }
    if out['sum_reqs']:
        out["max_req_time"] = max(df.get('max_time', [-1]))
        out['pct_500s'] = 100.0 * out['sum_500s'] / out['sum_reqs']
        out['pct_under_200ms'] = 100.0 *  sum(df.get('under_200ms', [])) / out['sum_reqs']
        out['mean_req_time'] = dot(df.get('count_requests', []), df.get('mean_time', [])) / out['sum_reqs']
    return out

def format_summary(summary):
    beautifiers = {
        'mean_req_time': {
            'name': "Mean request time",
            'formatter': lambda x: round(x, 3)
        },
        'pct_500s': {
            'name': "5XX error rate (%)",
            'formatter': lambda x: round(x, 4)
        },
        'sum_500s': {
            'name': "Number of 5XX responses",
            'formatter': lambda x: "{:,}".format(x)
        },
        'sum_504s': {
            'name': "Number of 504 responses",
            'formatter': lambda x: "{:,}".format(x)
        },
        'max_req_time': {
            'name': "Max request time",
            'formatter': lambda x: round(x, 3)
        },
        'sum_reqs': {
            'name': "Total request count",
            'formatter': lambda x: "{:,}".format(x)
        },
        'stream_reqs': {
            'name': "Streaming request count",
            'formatter': lambda x: "{:,}".format(x)
        },
        'pct_under_200ms': {
            'name': "Requests under 200ms (%)",
            'formatter': lambda x: round(x, 1)
        }
    }
    return {beautifiers[k]['name']: beautifiers[k]['formatter'](v)
        for k, v in summary.iteritems()}


## Basic math

def mean(x):
    return float(sum(x))/len(x) if len(x) else None

def quantile(x, q):
    i = int(q * len(x))
    return sorted(x)[i]

def median(x):
    return quantile(x, .5)

def dot(x, y):
    return sum([a*b for a, b in zip(x, y) if a is not None and b is not None])
