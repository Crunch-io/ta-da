#!/usr/bin/env python

import sys
from collections import OrderedDict as od
import Queue
import threading

import simplejson as json
from pprint import pprint

from cr.lib.entities.datasets import Dataset
from cr.lib.entities.variables import VariableDefinition
from cr.lib.entities.variables.ordering import VariableOrder
from cr.lib.entities.variables.multiple_response import prepare_subvars, category_ids_for_value
from cr.lib.settings import Settings, settings
from cr.lib.stores import init


DSID='000000000000002'
CONF = '/var/lib/crunch.io/cr.server-0.conf'
settings.update(Settings.from_file(CONF))
init()

ds = Dataset(id=DSID, name='SQUARE-2', user_id='00002')
#ds.deny()
#ds.create()

Q = {"?": -1}

fname = 'square13_2014_09_07_metadata.json' #  sys.argv[1]
meta = json.load(open(fname))
#print meta.keys()

hdr = open('header').readline().strip().split(',')
hdr.insert(1, 'wt') # Weight var not present in header!
hdr = dict((b.strip(), a) for (a, b) in enumerate(hdr))

seen = set()
def mkuniq(name):
    if name not in seen:
        seen.add(name)
        return name
    n=0
    while '%s-%d'%(name, n) in seen:
        n += 1
    name = '%s-%d'%(name, n)
    seen.add(name)
    return name

def worker(q):
    global ds
    while True:
        (var, values) = q.get()
        if var is None:
            break
        try:
            # Can we skip unique-name check by adding to ds.primary instad of ds?
            r=ds.add_variable(VariableDefinition.from_data(var),
                              values=values)
        except Exception, e:
            print e
            print 'RETRY'
            ds = Dataset(id=DSID, name='SQUARE-1', user_id='00002')
            r=ds.add_variable(VariableDefinition.from_data(var),
                              values=values)
        print r


p = ds.primary
alias_to_id_map = {v.alias: v.id for v in p.all_variables.itervalues()}


def load_vars():
    q = Queue.Queue(maxsize=100)
    t = threading.Thread(target=worker, args=(q,))
    t.start()

    for i,v in enumerate(meta['variables']):
        name = v['name']
        if name not in hdr:
            print "NOT FOUND |%s|" % name
            continue

        print i, name,

        if name in alias_to_id_map:
            print "exists"
            continue

        datafile = 'SPLIT/%06d.dat' % hdr[name]
        with open(datafile) as f:
            data = [l.strip() for l in f]

        values = v.get('values')
        if values is None:
            print "No values", name
            continue

        codes = v['values'].get('codes')
        if codes is not None:
            print "CAT"
            categories = [{'name': c['label'],
                           'numeric_value': c['value'],
                           'missing': False,
                           'id': i
                           } for (i, c) in enumerate(codes, 1)]
            categories.append({'name': "No Data",
                               'numeric_value': None,
                               'id': -1,
                               'missing': True})
            var_data = {
                'name' : mkuniq(v['label']),
                'alias': v['name'],
                'type': 'categorical',
                'categories': categories
                }

            cat_map = {str(c['numeric_value']) : i  for (i,c) in enumerate(categories, 1)}
            values = [cat_map.get(d, -1) for d in data]

        else:
            # Treat as numeric
            print "NUM"
            values = []
            mc = 1
            reasons = {}
            for d in data:
                if not d:
                    values.append(Q)
                else:
                    try:
                        values.append(int(d))
                    except ValueError:
                        try:
                            values.append(float(d))
                        except ValueError:
                            if d in reasons:
                                values.append({"?": reasons[d]})
                            else:
                                reasons[d] = mc
                                values.append({"?": mc})
                                mc += 1


            var_data = {
                'name' : mkuniq(v['label']),
                'alias': v['name'],
                'type': 'numeric'
                }

            if reasons:
                var_data['missing_reasons'] = reasons


        q.put((var_data, values))

    q.put((None, None))

    t.join()



def cleanup():
    p = ds.primary
    for v in p.all_variables.itervalues():
        if v.type in {'numeric', 'categorical'}:
            continue
        p.unbind(v)
        p.delete_variable(v)
        print "bye", v



subvar_to_mr = {}

def make_mrsets():
    mr_to_subvars = {}
    for i,mr in enumerate(meta['mrsets']):
        name = mr['name']
        path = mr['category']
        if path and path[-1]=='Lifestyle ': # data glitch?
            continue
        for v in mr['variables']:
            if v not in subvar_to_mr:
                subvar_to_mr[v] = []
            subvar_to_mr[v].append((path, name))
    for (v, x) in subvar_to_mr.iteritems():
        mr = max( (len(p[0]), p) for p in x)[1][1]
        if mr not in mr_to_subvars:
            mr_to_subvars[mr] = []
        mr_to_subvars[mr].append(v)


    for i,mr in enumerate(meta['mrsets']):
        name = mr['name']
        path = mr['category']
        if path and path[-1]=='Lifestyle ': # data glitch?
            continue

        print i, name,
        sys.stdout.flush()
        if name in alias_to_id_map:
            print "exists"
            continue

        var_ids = []
        for sub_name in mr_to_subvars.get(name, []):
            id = alias_to_id_map.get(sub_name)
            if id:
                var_ids.append(id)
            else:
                print "Not found!", sub_name
        if not var_ids:
            print "no subvars!"
            continue
        # This is expensive.  Do the import so categories
        # are matching, then all this casting can be skipped
        supertype = prepare_subvars(ds.primary, var_ids)
        new_var = ds.bind(var_ids,
                        mr['label'],
                        alias=name)
        print "bind returns", new_var

        v = mr.get('value')
        if v is None:
            continue
        v = int(v)

        selected_cats = category_ids_for_value(
            supertype['categories'],
            v)

        r =  p.dichotomize(new_var, selected_cats)
        print "dichotomize returns", r


root = od()
def get_node(path):
    node = root
    for p in path:
        if p in node:
            node = node[p]
        else:
            node[p] = od()
            node = node[p]
    return node

def vref(v):
    return {'variable_id': v, 'table_id': 'primary'}

def make_order():
    for i,mr in enumerate(meta['mrsets']):
        name = mr['name']
        path = mr['category']
        #print name,
        #sys.stdout.flush()
        if path and path[-1]=='Lifestyle ': # data glitch?
            continue
        id = alias_to_id_map.get(name)
        if id is None:
            print "does not exist"
            continue
        node = get_node(path)
        node[id] = None # leaf node

    ungrouped = []
    o = VariableOrder.for_dataset(ds)
    o.groups = []
    for k in root.keys():
        print "K=", k
        # Stray vars at global scope,
        if root[k] is None:
            print "UNGROUP"
            ungrouped.append(k)
        else:
            print "NEST"
            o.groups.append(mkgroup(k, root[k]))
    o.groups.append({'group': 'ungrouped',
                     'entities': map(vref, ungrouped)})
    return o


def mkgroup(key, node):
    return {'group': key,
            'entities': [mkgroup(subkey, node[subkey]) if node[subkey]
                         else vref(subkey)
                         for subkey in node.iterkeys()]}


#var_data = {
#    'name' : 'dummy',
#    'alias': 'dummy',
#    'type': 'numeric'
#    }
#print "Force save"
#r=ds.add_variable(VariableDefinition.from_data(var_data),
#                  values=[0]*len(data),
#                  save=True)
#print "RET", r


ref={
    'values': {'codes': [{'label': 'Agree', 'value': '1'},
                         {'label': 'Neither agree not disagree', 'value': '0'},
                         {'label': 'Disagree', 'value': '-1'}]}}


#load_vars()
#ds.save()

#make_mrsets()
#ds.save()
