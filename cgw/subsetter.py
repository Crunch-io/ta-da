from zz9lib.dispatcher import ZZ9Dispatcher as Z
from itertools import izip
import os

import numpy as np
import marshal

z=Z('redis://crunch-vpc.u1zohq.0001.usw2.cache.amazonaws.com:6379/6', timeout=600)

dsn='3282f3c571594a6d9c1b7ddd75f97ba3'

ds=z.lease(dsn)
ds.lease()

data=ds.query({'command':'select',
           'system':'variables',
           'variables': {'derived': {'variable': 'derived'},
                         'id': {'variable': 'id'},
                         'references': {'variable': 'references'},
                         'type': {'variable': 'type'}},
           'filter': None,
           'limit': None})['result']['data']

#print r.keys()
id_to_name = {id:ref.get('name') for id, ref in izip(data['id'], data['references'])}
id_to_type = {id:typ for id, typ in izip(data['id'], data['type'])}

#derived id refererence type


import pymongo

cli = pymongo.connection.Connection('mongo.privaws.crunch.io')
db = cli['io_crunch_alpha_db']
coll = db['variable_ordering']
o = coll.find_one({'dataset_id': dsn})

s = set()

keep_vars = set()

def rec(x, path, level=0):
    if isinstance(x, dict):
        g = x.get('group')
        if g:
            path += '/'+g


        else:
            keep = False
            varid, table =  x.get('variable_id'), x.get('table_id')
            name = id_to_name.get(varid, varid)

            if path.startswith('/ungrouped'):
                if name == 'id':
                    keep = True
            if path.startswith('/Brand') and varid:
                keep = True

            if keep:
                keep_vars.add(varid)
                type = id_to_type.get(varid)
                matrix = type.get('matrix', [])
                for m in matrix:
                    keep_vars.add(m)


        for xx in x.values():
            rec(xx, path, level+1)            





    elif isinstance(x, list):
        for xx in x:
            rec(xx, path, level+1)
    

rec(o, '')

def mkdir(p):
    try:
        os.mkdir(p)
    except:
        pass


#derived id refererence type

derived = [d for i,d in izip(data['id'], data['derived']) if i in keep_vars]
type = [t for i,t in izip(data['id'], data['type']) if i in keep_vars]
references = [t for i,t in izip(data['id'], data['references']) if i in keep_vars]
id = [i for i in data['id'] if i in keep_vars]


mkdir('new_variables')
mkdir('new_variables/derived')

def npsave(fname, val):
    np.save(fname, val)
    os.rename(fname + '.npy', fname)

npsave('new_variables/derived/data.zz9', derived)
npsave('new_variables/derived/missing.zz9', np.zeros(len(derived), dtype=np.int8))

mkdir('new_variables/id')
npsave('new_variables/id/data.zz9', id)
npsave('new_variables/id/missing.zz9', np.zeros(len(id), dtype=np.int8))


mkdir('new_variables/references')
marshal.dump(references, open('new_variables/references/data.zz9', 'w'))

mkdir('new_variables/type')
marshal.dump(type, open('new_variables/type/data.zz9', 'w'))


#batch  query  revision timestamp 
data=ds.query({'command':'select',
               'system':'history',
               'variables': {'batch': {'variable': 'batch'},
                             'query': {'variable': 'query'},
                             'revision': {'variable': 'revision'},
                             'timestamp': {'variable': 'timestamp'}},
               'filter': None,
               'limit': None})['result']['data']


indices = []

for i,q in enumerate(data['query']):
    if q.get('command') == 'derive':
        for v in q['variables'].keys():
            if v in keep_vars:
                indices.append(i)

batch = [data['batch'][i] for i in indices]
query = [data['query'][i] for i in indices]
revision = [data['revision'][i] for i in indices]
timestamp= [data['timestamp'][i] for i in indices]

mkdir('new_history')
mkdir('new_history/batch')
npsave('new_history/batch/data.zz9', batch)
npsave('new_history/batch/missing.zz9', np.zeros(len(batch), dtype=np.int8))

mkdir('new_history/timestamp')
npsave('new_history/timestamp/data.zz9', timestamp)
npsave('new_history/timestamp/missing.zz9', np.zeros(len(timestamp), dtype=np.int8))

mkdir('new_history/revision')
npsave('new_history/revision/data.zz9', revision)
npsave('new_history/revision/missing.zz9', np.zeros(len(revision), dtype=np.int8))

mkdir('new_history/query')
marshal.dump(query, open('new_history/query/data.zz9', 'w'))


os.chdir('/var/lib/crunch.io/zz9data/%s/branches/master/frames/primary/tables/main/' % dsn)
print os.getcwd()
for f in os.listdir('.'):
    if f not in keep_vars and not f.startswith('_'):
        os.system('rm -rv %s' % f)

    
