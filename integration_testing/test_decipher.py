#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Script to manually test surveymonkey integration.  This needs to be run in the context
of a crunch virtualenv.
"""
import sys
import os
import time
import requests_cache

from cr.lib.integrations.decipher import DecipherIntegration
from cr.lib.integrations.base import append_source_from_integration
from cr.lib.commands.common import load_settings
from cr.lib.settings import settings
from cr.lib import stores
from cr.lib.entities.datasets import Dataset

from mock import MagicMock

import cr.lib.integrations.decipher as decipher
decipher.DEBUG_DECIPHER_LIMIT_ROWS = 5
decipher.DEBUG_PRINT_DECIPHER_DATA = False

import logging
logger = logging.getLogger('cr.lib')
handler = logging.StreamHandler()
logger.addHandler(handler)

settings_yaml = sys.argv[1]
settings.update(load_settings(settings_yaml))

stores.stores.configure()
stores.stores.populate()


def as_entity(x):
    return {"element": "shoji:entity", "body": x}

requests_cache.install_cache("demo_cache", expire_after=50000)

DECIPHER_APIKEY = os.environ["DECIPHER_APIKEY"]
#DECIPHER_SURVEY_ID = os.environ["DECIPHER_SURVEY_ID"]
DECIPHER_COMPANY_NAME = os.environ["DECIPHER_COMPANY_NAME"]

#CRUNCH_USER = os.environ["CRUNCH_USER"]
#CRUNCH_PASSWORD = os.environ["CRUNCH_PASSWORD"]
#CRUNCH_API_URL = os.environ.get("CRUNCH_API_URL", "https://alpha.crunch.io/api")


no_rows = """
selfserve%2F548%2F130309
selfserve%2F548%2F150924
selfserve%2F548%2F141218""".split("\n")[1:]

def get_benchmark():
    SM_SURVEY_ID = "selfserve%2F548%2F171201"

    sm = DecipherIntegration(company_name=DECIPHER_COMPANY_NAME,
                             apikey=DECIPHER_APIKEY)
    survey = sm.get_survey(SM_SURVEY_ID)


    def set_progress(self, *args, **kwargs):
        print args, kwargs


    task = MagicMock()

    task.set_progress = set_progress


    print 'getting csv'

    import time

    now = time.time()
    survey.crunch_csv(task)

    print 'done in %s seconds' % (time.time() - now)


integration = DecipherIntegration(company_name=DECIPHER_COMPANY_NAME,
                                  apikey=DECIPHER_APIKEY)

print 'testing authentication...',
sys.stdout.flush()
#integration.authenticate()
print 'done'


print 'getting survey list...',
sys.stdout.flush()
surveys = integration.surveys
surveys_by_paths = {s['id']: s for s in surveys}
print 'done'


def get_survey(survey_id):
    survey = surveys_by_paths[survey_id]

    print "Getting survey: %s with id %s (%s responses, %s questions)" % (survey["title"],
                                                                          survey_id,
                                                                          survey["response_count"],
                                                                          survey["question_count"])

    import uuid
    new_dsid = uuid.uuid4().hex
    survey_name = survey["title"]
    request_info = {}
    user_id = '000001'  # captain

    def set_progress(self, *args, **kwargs):
        print args, kwargs

    task = MagicMock()

    task.set_progress = set_progress
    survey = integration.get_survey(survey_id)

    #metadata = survey.crunch_metadata(MagicMock())

    if survey._errors:
        print '*'*89
        print "warning: survey metadata had errors: %s" % survey._errors
        print '*' * 89
    #import ipdb; ipdb.set_trace()

    append_source_from_integration(
        integration, task, new_dsid, survey_id, survey_name, user_id, request_info
    )


    print 'done'
    return new_dsid

landmines = ['selfserve%2F548%2F150616']

win_for_life_id = "selfserve%2F548%2F130917"
all_types_id = "selfserve%2F548%2F190404"

surveys = "failures here".split('\n')[1:]

for survey in surveys:
    print '~'*80
    try:
        ds_id = get_survey(survey)
        ds = Dataset.find_by_id(id=ds_id, version="master__tip")

        # check that the first variable loaded
        assert len(ds.primary.select(limit=1)['data']['000001']) == 1
    except:
        print 'failed'
        #import ipdb; ipdb.set_trace()
        continue
    print 'passed'


# failed_id = "selfserve%2F548%2F130309"
#
# ds_id = get_survey(failed_id)
# ds = Dataset.find_by_id(id=ds_id, version="master__tip")
# print ds.primary.select(limit=100)['data']['000001']
# # import ipdb; ipdb.set_trace()
# exit()

#survey_entry = [x for x in survey_list if x['id'] == survey_id][0]

decipher_500_failures = ["selfserve%2F548%2F150720", "selfserve/548/150720",
                                 "selfserve%2F548%2F160505", "selfserve%2F548%2F161221",
                                 "selfserve%2F548%2F161201"
                                 ] # -- Decipher 500 on this DS

decipher_communication_failures = ["selfserve%2F548%2F150224", "selfserve%2F548%2F141212",
                                   "selfserve%2F548%2F150227", "selfserve%2F548%2F150224",
                                   "selfserve%2F548%2F141212", "selfserve%2F548%2F150227",
                                   "selfserve%2F548%2F130318", "selfserve%2F548%2F141215",
                                   "selfserve%2F548%2F151139", "selfserve%2F548%2F190405",
                                   "selfserve%2F548%2F161103", "selfserve%2F548%2F150209"]

gets_killed_failures = ["selfserve%2F548%2F131239"] #88110 responses - did eventually load on the last try

# still need to check these
expected_column_not_found = ["selfserve%2F548%2F160111", "selfserve%2F548%2F161021",
                             "selfserve%2F548%2F150202", "selfserve%2F548%2F170117"]

##################################
# working set of failures

category_not_defined = ["selfserve%2F548%2F130424"]

########################

known_failures = decipher_communication_failures + decipher_500_failures + gets_killed_failures

for survey_id in expected_column_not_found:
    try:
        print '*' * 89
        ds_id = get_survey(survey_id)
        ds = Dataset.find_by_id(id=ds_id, version="master__tip")
        assert len(ds.primary.select(limit=1)['data']['000001']) == 1
    except Exception as e:
        print e

exit()

def get_all_metadatas(surveys):

    for s in surveys:
        #if s['response_count'] > 100:
        #    continue
        if s['id'] in known_failures:
            continue
        survey_id = s['id']
        print 'trying metadata for survey: %s ' % s['title'],
        survey = integration.get_survey(survey_id)
        try:
            metadata = survey.crunch_metadata(MagicMock())
        except Exception as e:
            if e.message == 'Decipher communication error.':
                print '***** 403 *****', s['id']
                continue
        print "success"


def get_all_surveys():
    surveys = integration.surveys
    total_surveys = len(surveys)

    num_failures = 0
    for i, s in enumerate(surveys):
        survey_id = s['id']
        responses = int(s['response_count'])
        #if survey_id in four_oh_threes:
        #    continue
        if i < 1378:
            continue

        if survey_id in known_failures:
            continue

        if responses < 2:
            print '*' * 89
            print 'skipping', survey_id, "not enough responses"
            print '*' * 89
            continue

        # skip large responses
        if responses > 10000:
             print '*'*89
             print 'skipping', survey_id, "too many responses."
             print '*'*89
             continue

        #import ipdb; ipdb.set_trace()
        print '*' * 89
        print 'Trying survey %s/%s (%s%%) trying metadata for survey: %s (%s questions, %s responses)'\
              % (i, total_surveys, int(float(i + 1)/total_surveys * 1000)/10.0,
                 s['title'], s['question_count'], s['response_count'])
        try:
            now = time.time()
            ds_id = get_survey(survey_id)
        except:
            num_failures +=1
            import traceback
            traceback.print_exc()
            traceback.print_stack()
            print "FAILED: %s failures so far" % num_failures
            continue
        ds = Dataset.find_by_id(id=ds_id, version="master__tip")
        try:
            # check that the first variable loaded
            if int(s['response_count']) != 0:
                assert len(ds.primary.select(limit=1)['data']['000001']) == 1
        except:
            num_failures +=1
            import traceback
            traceback.print_exc()
            traceback.print_stack()
            print "FAILED: %s failures so far" % num_failures
            continue
        else:
            ds.release()

        print 'done in %s seconds.' % (time.time() - now)

if __name__ == '__main__':
    get_all_surveys()
