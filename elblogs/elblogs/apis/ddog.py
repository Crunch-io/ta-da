from datadog import initialize, api

options = {
    'api_key': '77719a81684a5fb8d8596ccb294d506d',
    'app_key': '0eb4388b5f09189ab66a0c4a7123a1abff72d00d'
}

initialize(**options)


def count(metric, start, end, scope=None):
    ''' Get a total count of a dog metric for a date range, not a time series'''
    # metric = 'zz9.imports.frame.started'
    if scope is None:
        scope = 'autoscaling_group:eu-zz9' if metric[:3] == 'zz9' else 'region:eu-west-1'
    q = 'sum:%s{%s}.as_count()' % (metric, scope)
    return query(q, start, end)


def query(query, start, end):
    ''' Get a total count of a dog metric for a date range, not a time series'''
    response = api.Metric.query(start=start, end=end, query=query)
    if 'series' in response and len(response['series']):
        # We have data. Sum the points.
        # `or 0` is because apparently 0 is now coming back as `null`
        return sum(int(val[1] or 0) for val in response['series'][0]['pointlist'])
    else:
        # No values found in this range, which means 0 count
        return 0

def count_zz9(command, start, end, **tags):
    ''' Get a total count of a zz9 command for a date range, not a time series

        Usage:
        >>> dog_count_zz9("import_frame", <int time>, <int time>, status="success")

    '''
    tags['command'] = command
    tags['autoscaling_group'] = 'eu-zz9'
    tagstring = ','.join([':'.join((k, v)) for k, v in tags.iteritems()])
    # sum:zz9.factory.time.ms.count{command:import_frame,autoscaling_group:eu-zz9}.as_count()
    q = 'sum:zz9.factory.time.ms.count{%s}.as_count()' % tagstring
    return query(q, start, end)

def count_cr(controller, start, end, method=None, **tags):
    ''' Get a total count of a cr.server controller for a date range, not a
        time series

        Usage:
        >>> dog_count_cr("datasetactionscatalog", <int time>, <int time>, method="post")

    '''
    tags['controller'] = controller
    tags['region'] = 'eu-west-1'
    if method:
        tags['method'] = method.lower()
    tagstring = ','.join([':'.join((k, v)) for k, v in tags.iteritems()])
    # sum:cr.server.request.time.ms.count{controller:datasetactionscatalog,method:post}.as_count()
    q = 'sum:cr.server.request.time.ms.count{%s}.as_count()' % tagstring
    return query(q, start, end)

def count_task(task, start, end, status=None, **tags):
    ''' Get a total count of a background task for a date range, not a time
        series.

        Valid statuses: success, failed, invalid, retry, pending, corrupted

        Usage:
        >>> dog_count_task("play_workflow", <int time>, <int time>, status="failed")

    '''
    tags['task'] = task
    tags['region'] = "eu-west-1"
    if status:
        tags['task_status'] = status
    tagstring = ','.join([':'.join((k, v)) for k, v in tags.iteritems()])
    # sum:cr.server.request.time.ms.count{controller:datasetactionscatalog,method:post}.as_count()
    q = 'sum:task.run.ms.count{%s}.as_count()' % tagstring
    return query(q, start, end)
