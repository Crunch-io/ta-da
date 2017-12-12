import sys
import uuid
import itertools
import random
from cr.lib.settings import settings
from cr.lib.index.es import get_es
from cr.lib.index.util import bulk
from datetime import datetime

es = None


def index_array(ds_id, name, cat_num, subvar_num, subvar_name, distribution):
    var_id = uuid.uuid4().hex
    id = '__'.join((ds_id, var_id))

    cat_names = ['cat %s' % i for i in xrange(cat_num)]
    subvar_names = ['subvar %s %s %s' % (i, subvar_name, random.choice(distribution)) for i in xrange(subvar_num)]

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

    NUM_DATASETS = 1
    NUM_CATS = 200

    distribution = [
{'no_vars': 5,    'no_subvars': 4000, 'name': "quattro"},
{'no_vars': 7,    'no_subvars': 3000, 'name': "trio"},
{'no_vars': 12,   'no_subvars': 2000, 'name': 'duo'},
{'no_vars': 20,   'no_subvars': 1000, 'name': 'uno'},
{'no_vars': 42,   'no_subvars': 500, 'name':  'cinq'},
{'no_vars': 53,   'no_subvars': 400, 'name':  'quarant'},
{'no_vars': 71,   'no_subvars': 300, 'name':  'tres'},
{'no_vars': 98,   'no_subvars': 200, 'name':  'duece'},
{'no_vars': 234,  'no_subvars': 100, 'name':  'hundy'},
{'no_vars': 1032, 'no_subvars': 50, 'name':   'fifty'},
{'no_vars': 5427, 'no_subvars': 10, 'name':   'ten'},
{'no_vars': 6229, 'no_subvars': 5, 'name':    "five"},
{'no_vars': 7572, 'no_subvars': 1, 'name':    "one"},
]

    names = {
        'colors': {'red': 5000, 'orange': 1000, 'yellow': 500, 'green': 100, 'cyan': 10, 'blue': 1},
        'animals': {'dogs': 5000, 'pigs': 1000, 'wolfs': 500, 'parrots': 100, 'fish': 10, 'dreams': 1},
        'shapes': {'circle': 5000, 'square': 1000, 'triangle': 500, 'pentagon': 100, 'decagon': 10, 'sphere': 1},
        'bikes': {'pivot': 5000, 'specialized': 1000, 'kona': 500, 'trek': 100, 'juliana': 10, 'santa cruz': 1},
        'cars': {'toyota': 5000, 'honda': 1000, 'bmw': 500, 'audi': 100, 'volkswagen': 10, 'ford': 1},
        'computers': {'compaq': 5000, 'apple': 1000, 'dell': 500, 'ibm': 100, 'hp': 10, 'acer': 1}
    }

    for db_name, colors in names.iteritems():
        print 'LOADING', db_name
        name_distribution = list(itertools.chain.from_iterable(([key] * value for key, value in colors.iteritems())))
        for d in xrange(NUM_DATASETS):
            ds_id = create_dataset("Search Test Dataset %s" %d, "Description for the search dataset %s" % d)
            for dist in distribution:
                print 'dataset: %s %s (%s vars)' % (d, ds_id, dist['no_vars'])
                bulk(es, (index_array(ds_id, "Array %s" % v, NUM_CATS, dist['no_subvars'], dist['name'], name_distribution) for v in xrange(dist['no_vars'])))


if __name__ == '__main__':
    main()
