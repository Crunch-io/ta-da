def analyze_log(data):
    '''Given a log data.frame-like dict, aggregate'''
    results = {}
    results['count_requests'] = len(data['elb'])
    times = zip(data['request_processing_time'], data['backend_processing_time'], data['response_processing_time'])
    total_time = [sum(list(x)) for x in times]
    results['mean_time'] = mean(total_time)
    results['max_time'] = max(total_time)
    results['count_500s'] = len([x for x in data['elb_status_code']
        if x >= 500.0])
    results['count_504s'] = len([x for x in data['elb_status_code']
        if x == 504])
    return results

def summarize(data):
    '''Compute some aggregates'''
    quantities = ['count_requests', 'mean_time', 'max_time', 'count_500s',
        'count_504s']
    ## First, reshape the data into something useful
    df = dict(zip(quantities, zip(*([v[i] for i in quantities] for v in data.values()))))

    out = {
        "sum_reqs": sum(df['count_requests']),
        "sum_500s": sum(df['count_500s']),
        "sum_504s": sum(df['count_504s']),
        "max_req_time": max(df['max_time']),
    }
    out['pct_500s'] = 100.0 * out['sum_500s'] / out['sum_reqs']
    out['mean_req_time'] = dot(df['count_requests'], df['mean_time']) / out['sum_reqs']
    return out

## Basic math

def mean(x):
    return float(sum(x))/len(x)

def quantile(x, q):
    i = int(q * len(x))
    return sorted(x)[i]

def median(x):
    return quantile(x, .5)

def dot(x, y):
    return sum([a*b for a, b in zip(x, y)])
