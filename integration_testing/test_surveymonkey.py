"""
Script to manually test surveymonkey integration.  This needs to be run in the context
of a crunch virtualenv.
"""

import os
import pprint
import time
import requests_cache

from cr.lib.integrations.surveymonkey import SurveyMonkeyIntegration

def as_entity(x):
    return {"element": "shoji:entity", "body": x}

requests_cache.install_cache("demo_cache", expire_after=50000)

SM_ACCESS_TOKEN = os.environ["SM_ACCESS_TOKEN"]
SM_SURVEY_ID = os.environ["SM_SURVEY_ID"]
CRUNCH_USER = os.environ["CRUNCH_USER"]
CRUNCH_PASSWORD = os.environ["CRUNCH_PASSWORD"]
CRUNCH_API_URL = os.environ.get("CRUNCH_API_URL", "https://alpha.crunch.io/api")

sm = SurveyMonkeyIntegration(SM_ACCESS_TOKEN)
survey = sm.get_survey(SM_SURVEY_ID)

crunchtable, tmpf = survey.get_crunchtable_and_csv()

with requests_cache.disabled():
    import uuid
    import pycrunch

    thisrun = uuid.uuid4().hex
    table = as_entity({"table": crunchtable, "name": "test_sm_import-%s" % thisrun})
    session = pycrunch.Session(CRUNCH_USER, CRUNCH_PASSWORD)
    session.hooks["response"].status_301 = lambda r: r
    site = session.get(CRUNCH_API_URL, verify=False).payload
    ds = site.datasets.create(table).refresh()

    batches_url = ds.catalogs["batches"]
    response = ds.session.post(
        batches_url, files={"file": ("ignored", tmpf, "text/csv")}
    )

    j = response.json()
    resource_url = response.headers["Location"]
    progress_url = j["value"]
    for x in range(0, 10):
        progress_json = ds.session.get(progress_url).json()
        progress = progress_json["value"]["progress"]
        if progress == 100 or progress == -1:
            break
        time.sleep(1)
    response = ds.session.get(resource_url)
    variables = ds.variables.by("alias")
    table_data = ds.follow("table", "limit=100")
    pprint.pprint(table_data)