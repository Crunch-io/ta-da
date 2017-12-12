import sys
import uuid
from cr.lib.settings import settings
from cr.lib.index.es import get_es
from cr.lib.index.util import bulk
from datetime import datetime

es = None


def index_array(ds_id, name, cat_num, subvar_num):
    var_id = uuid.uuid4().hex
    id = '__'.join((ds_id, var_id))

    cat_names = ['cat %s' % i for i in xrange(cat_num)]
    subvar_names = ['subvar %s' % i for i in xrange(subvar_num)]

    array = {
       u'_op_type': 'update',
       u'_id': id,
       u'_index': es.current_index,
       u'_parent': ds_id,
       u'_retry_on_conflict': 4,
       u'_type': 'variable',
     'doc': {'alias': name,
       'category_names': cat_names,
       'dataset_id': ds_id,
       'description': '',
       'discarded': False,
       'group_names': None,
       'id': var_id,
       'name': name,
       'subvar_names': subvar_names,
       'variable_type': 'categorical_array'},
      'doc_as_upsert': True}
    return array

many_cats = [{'update': {u'_id': u'5d069970c6734101b451b931559d54cd__7184bf88f0aa45e7a437add41d4b61fd',
   u'_index': 'crunch_app_db_prod',
   u'_parent': '5d069970c6734101b451b931559d54cd',
   u'_retry_on_conflict': 4,
   u'_type': 'variable'}},
 {'doc': {'alias': u'var 0 a',
   'category_names': [u'not selected'], # <----- add lots of categories here
   'dataset_id': '5d069970c6734101b451b931559d54cd',
   'description': '',
   'discarded': False,
   'group_names': None,
   'id': u'7184bf88f0aa45e7a437add41d4b61fd',
   'name': u'var 0 a',
   'variable_type': u'categorical'},
  'doc_as_upsert': True},
]


def create_dataset(name, description):

    now = datetime.utcnow()
    id = uuid.uuid4().hex

    doc = {'description': description,
         'dataset_users': ['00002'],
         'labels': None,
         'projects': [],
         'teams': [],
         'modification_time': now,
         'owner': '00002',
         'owner_type': 'user',
         'organizations': ['00001'],
          'id': id,
          'name': name,
          'archived': False,
          'is_published': True,
          'start_date': now,
          'end_date': None,
          # 'notes',  todo: this causes a parsing error when indexing alpha
          'creation_time': now
         }

    es.update(index=es.current_index,
              doc_type='dataset',
              id=id,
              body={'doc': doc,
                    'doc_as_upsert': True})

    return id


def load_settings(configfilename):

    global es
    try:
        settings.update(settings.from_file(configfilename))
    except IOError:
        sys.exit(u'File "%s" cannot be read' % configfilename)

    es = get_es()


def main():

    settings_file = sys.argv[1]
    load_settings(settings_file)


    NUM_DATASETS = 100
    NUM_SUBVARS = 10000
    NUM_CATS = 500
    NUM_VARS = 100

    for d in xrange(NUM_DATASETS):
        ds_id = create_dataset("Search Test Dataset %s" %d, "Description for the search dataset %s" % d)
        print 'dataset: %s %s' % (d, ds_id)
        bulk(es, (index_array(ds_id, "Array %s" % v, NUM_CATS, NUM_SUBVARS) for v in xrange(NUM_VARS)))

if __name__ == '__main__':
    main()
