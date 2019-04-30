#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Script to manually test surveymonkey integration.  This needs to be run in the context
of a crunch virtualenv.
"""
import sys
import os
import pprint
import time
import requests_cache

from cr.lib.integrations.decipher import DecipherIntegration
from cr.lib.integrations.base import append_source_from_integration
from cr.lib.commands.common import load_settings
from cr.lib.settings import settings
from cr.lib import stores
from cr.lib.entities.datasets import Dataset

from mock import MagicMock


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

#sm = DecipherIntegration(SM_ACCESS_TOKEN)
#survey = sm.get_survey(SM_SURVEY_ID)

decipher_connect_error = """
selfserve%2F548%2F150227
selfserve%2F548%2F141212
selfserve%2F548%2F140827
selfserve%2F548%2F150224
selfserve%2F548%2F130704
selfserve%2F548%2F170719
selfserve%2F548%2F130318"""

retry = """
selfserve%2F548%2F160320
selfserve%2F548%2F131234
selfserve%2F548%2F150932"""

error13 = """
selfserve%2F548%2F161114
selfserve%2F548%2F140121
selfserve%2F548%2F150337"""

dup_cats = """
selfserve%2F548%2F160120
selfserve%2F548%2F170209
selfserve%2F548%2F160605"""

no_rows = """
selfserve%2F548%2F130309
selfserve%2F548%2F150924
selfserve%2F548%2F141218"""


values_error = """
selfserve%2F548%2F160412
selfserve%2F548%2Fyg14001"""


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

    print "Getting survey: %s with id %s" % (surveys_by_paths[survey_id]['title'], survey_id)
    import uuid
    new_dsid = uuid.uuid4().hex
    survey_name = 'All Types Survey'
    request_info = {}
    user_id = '000001'  # captain

    def set_progress(self, *args, **kwargs):
        print args, kwargs

    task = MagicMock()

    task.set_progress = set_progress

    append_source_from_integration(
        integration, task, new_dsid, survey_id, survey_name, user_id, request_info
    )
    print 'done'
    return new_dsid


win_for_life_id = "selfserve%2F548%2F130917"
all_types_id = "selfserve%2F548%2F190404"
failed_id = "selfserve%2F548%2Fyg14001"

surveys = "failures here".split('\n')[1:]

for survey in surveys:
    print '~'*80
    try:
        ds_id = get_survey(survey)
        ds = Dataset.find_by_id(id=ds_id, version="master__tip")

        # check that the first variable loaded
        assert len(ds.select(limit=1)['data']['000001']) == 1
    except:
        print 'failed'
        #import ipdb; ipdb.set_trace()
        continue
    print 'passed'

ds_id = get_survey(failed_id)
# ds = Dataset.find_by_id(id=ds_id, version="master__tip")
# print ds.select(limit=100)['data']['000001']
# import ipdb; ipdb.set_trace()
exit()

#get_survey(all_types_id)
#exit()
#get_survey(win_for_life_id)

#exit()

#import ipdb; ipdb.set_trace()
#exit()

#survey_id = 'selfserve%2F548%2F181103'
#survey_id = 'selfserve%2F548%2F130630'


#survey_entry = [x for x in survey_list if x['id'] == survey_id][0]

four_oh_threes = ['selfserve%2F548%2F150224', 'selfserve%2F548%2F150227',
                  'selfserve%2F548%2F150209', 'selfserve%2F548%2F141212',
                  'selfserve%2F548%2F130318', 'selfserve%2F548%2F170719',
                  'selfserve%2F548%2F130704', 'selfserve%2F548%2F151139',
                  'selfserve%2F548%2F180203', 'selfserve%2F548%2F141215',
                  ]

def get_all_metadatas(surveys):

    for s in surveys:
        #if s['response_count'] > 100:
        #    continue
        if s['id'] in four_oh_threes:
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
        #if survey_id in four_oh_threes:
        #    continue
        if i < 301:
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
            if s['question_count'] != 0:
                assert len(ds.select(limit=1)['data']['000001']) == 1
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
