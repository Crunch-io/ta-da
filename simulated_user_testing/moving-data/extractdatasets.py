import requests
import os
import json
import pprint

session = requests.session

SENTRY_API_TOKEN = os.environ['SENTRY_API_TOKEN']


session = requests.Session()

session.headers.update({"Authorization": "Bearer %s" % SENTRY_API_TOKEN})
projects_resp = session.get("https://sentry.io/api/0/projects/")


production_id = 155823

issues_url = "https://sentry.io/api/0/organizations/crunchio/issues/?limit=25&project=%s&query=is%%3Aunresolved%%20timesSeen%%3A%%3E100&shortIdLookup=1&sort=freq&statsPeriod=14d" % (production_id)

issues_resp = session.get(issues_url)

issues = json.loads(issues_resp.text)

issue_ids = [issue['id'] for issue in issues]

datasets = {}

for issue_id in issue_ids:

    issue_url = "https://sentry.io/api/0/issues/%s/" % issue_id
    issue_resp = session.get(issue_url)
    issue = json.loads(issue_resp.text)

    dataset_id_tags_url = "https://sentry.io/api/0/issues/%s/tags/?key=dataset&enable_snuba=1" % issue_id
    tags_resp = session.get(dataset_id_tags_url)
    tags = json.loads(tags_resp.text)

    if not tags:
        continue

    for tag in tags[0]['topValues']:
        datasets.setdefault(tag['name'], 0)
        datasets[tag['name']] += tag['count']

pprint.pprint(datasets)
