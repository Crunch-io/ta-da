# ssh root@ahsoka.crunch.io
# cd /var/www/logs/AWSLogs/910774676937/elasticloadbalancing/eu-west-1/2015
# cd /var/www/logs/AWSLogs/910774676937/elasticloadbalancing/us-west-2/2015

# '2015-09-30T06:20:32.642821Z Beta-VPC 38.102.150.18:34525 10.0.1.86:443 0.000038 2.068878 0.000036 200 200 0 439679 "GET https://beta.crunch.io:443/api/datasets/ HTTP/1.1" "-" ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2'.split(' ')
# ['2015-09-30T06:20:32.642821Z', 'Beta-VPC', '38.102.150.18:34525', '10.0.1.86:443', '0.000038', '2.068878', '0.000036', '200', '200', '0', '439679', '"GET', 'https://beta.crunch.io:443/api/datasets/', 'HTTP/1.1"', '"-"', 'ECDHE-RSA-AES128-GCM-SHA256', 'TLSv1.2']

#'910774676937_elasticloadbalancing_eu-west-1_eu-vpc_20151101T2300Z_52.19.22.234_16gycro6.log'.split('_')
# ['910774676937', 'elasticloadbalancing', 'eu-west-1', 'eu-vpc', '20151101T2300Z', '52.19.22.234', '16gycro6.log']

import os


fields = 'timestamp elb client:port backend:port request_processing_time backend_processing_time response_processing_time elb_status_code backend_status_code received_bytes sent_bytes request_verb request_url request_protocol user_agent ssl_cipher ssl_protocol'.split(' ')

numeric_fields = 'request_processing_time backend_processing_time response_processing_time elb_status_code backend_status_code received_bytes sent_bytes'.split(' ')

def do_all(start=None, end=None):
    ''' Find log files, possibly for a time range, read them, and return the
        indicated quantites for all
    '''
    files = find_dot(start, end)
    results = {}
    for f in files:
        results[f] = analyze_log(load_log(f))
    return summarize(results)

def load_log(filename):
    '''Take an ELB file and return a data.frame-like dict of columns'''
    with open(filename) as f:
        cols = zip(*(line.split(' ') for line in f))
    out = dict(zip(fields, cols))
    for i in numeric_fields:
        ## Make these numeric so we can do math on them
        out[i] = [float(x) for x in out[i]]
    return out

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
    

def find_dot(start=None, end=None):
    '''Find all log files, perhaps filtered by a date range (as 8 digit integers)'''
    files = []
    for dirpath, dirnames, filenames in os.walk("."):
        files.extend([os.path.join(dirpath, name) for name in filenames 
            if name[-4:] == ".log" and 
            file_in_date_range(name, start, end)])
    return files

def file_in_date_range(filename, start=None, end=None):
    '''Given a file name format like '910774676937_elasticloadbalancing_eu-west-1_eu-vpc_20151101T2300Z_52.19.22.234_16gycro6.log', parse the date and do math on it to determine whether it is in the specified range'''
    out = True
    if start or end:
        try:
            date = int(filename.split("_")[4][:8])
            if start:
                out &= date >= start
            if end:
                out &= date <= end
        except:
            print "Error parsing filename", filename
            out = False
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

