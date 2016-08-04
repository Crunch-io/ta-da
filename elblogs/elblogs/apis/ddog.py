from datadog import initialize, api

options = {
    'api_key': '77719a81684a5fb8d8596ccb294d506d',
    'app_key': '52e4b512d223ce4d104da319008b8d81d070e940'
}

initialize(**options)


def dog_count(metric, start, end, scope=None):
    ''' Get a total count of a dog metric for a date range, not a time series'''
    # metric = 'zz9.imports.frame.started'
    if scope is None:
        scope = 'autoscaling_group:eu-zz9' if metric[:3] == 'zz9' else 'host:eu-backend.priveu.crunch.io'
    q = 'sum:%s{%s}.as_count()' % (metric, scope)
    response = api.Metric.query(start=start, end=end, query=q)
    if 'series' in response and len(response['series']):
        # We have data. Sum the points.
        return sum(int(val[1]) for val in response['series'][0]['pointlist'])
    else:
        # No values found in this range, which means 0 count
        return 0
