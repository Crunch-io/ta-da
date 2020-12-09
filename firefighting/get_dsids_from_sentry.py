# Sentry API docs: https://docs.sentry.io/api/
import logging
import re
import sys

import requests
import yaml

log = logging.getLogger('get_dsids_from_sentry')

# All API requests should be made to the /api/0/ prefix, and will return JSON
# Example URLs:
# https://sentry.io/api/0/projects/1/groups/
# https://sentry.io/api/0/projects/1/groups/?status=unresolved

# List of DatasetIntegrityError events in past 24 hours in production
# https://sentry.io/organizations/crunchio/issues/?project=155823&query=is%3Aunresolved+%22DatasetIntegrityError%22&statsPeriod=24h

API_URL = 'https://sentry.io/api/0'
ORGANIZATION_SLUG ='crunchio'
PROJECT_SLUG = 'production'


def print_event_dataset_ids(session):
    # print("eventID,dataset")
    query_params = {
        "statsPeriod": "24h",
        "query": 'is:unresolved "DatasetIntegrityError"',
    }
    num_events = 0
    dataset_id_set = set()
    for issue in gen_project_issues(session, query_params):
        issue_id = issue['id']
        for event in gen_issue_events(session, issue_id):
            dataset_id = get_dataset_id_from_event(session, event)
            num_events += 1
            if dataset_id and dataset_id != 'None':
                dataset_id_set.add(dataset_id)
            # event_id = event['eventID']
            # print(f"{event_id},{dataset_id}")
    log.info("num_events: %d", num_events)
    log.info("num datasets: %d", len(dataset_id_set))
    for dataset_id in sorted(dataset_id_set):
        print(dataset_id)


def gen_project_issues(session, query_params):
    issues_url = f'{API_URL}/projects/{ORGANIZATION_SLUG}/{PROJECT_SLUG}/issues/'
    log.debug("GET %s", issues_url)
    r = session.get(issues_url, params=query_params)
    while True:
        r.raise_for_status()
        issues = r.json()
        log.debug("gen_project_issues: %d issues in this page", len(issues))
        for issue in issues:
            yield issue
        log.debug("gen_project_issues: cur page links %s:", r.links)
        if not r.links['next']['results'] == 'true':
            break
        r = session.get(r.links['next']['url'])


def gen_issue_events(session, issue_id):
    events_url = f'{API_URL}/issues/{issue_id}/events/'
    log.debug("GET %s", events_url)
    r = session.get(events_url)
    while True:
        r.raise_for_status()
        events = r.json()
        log.debug("gen_issue_events: %d events on this page", len(events))
        for event in events:
            yield event
        if not r.links['next']['results'] == 'true':
            break
        log.debug("gen_issue_events: cur page links: %s", r.links)
        r = session.get(r.links['next']['url'])


def get_dataset_id_from_event(session, event):
    tags = event['tags']
    dataset_id = None
    for tag in tags:
        if tag['key'] == 'dataset':
            dataset_id = tag['value']
            break
    if dataset_id == 'None':
        # Crazy stuff Sentry does to our data...
        dataset_id = None
    if dataset_id:
        return dataset_id
    # Dataset wasn't in tags, have to work harder to get it
    event_id = event['id']
    event_url = (
        f'{API_URL}/projects/{ORGANIZATION_SLUG}/{PROJECT_SLUG}/events/{event_id}/'
    )
    log.debug("GET %s", event_url)
    r = session.get(event_url)
    r.raise_for_status()
    event_details = r.json()
    context = event_details['context']
    task_id = context.get('task_id')
    if not task_id:
        return None
    m = re.search(r":(\w+)\$", task_id)
    if not m:
        return None
    return m.group(1)


def main():
    logging.basicConfig(level=logging.INFO)
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
    auth_token = config['auth_token']
    session = requests.Session()
    session.headers['Authorization'] = 'Bearer ' + auth_token
    print_event_dataset_ids(session)


if __name__ == '__main__':
    sys.exit(main())
