#!/var/lib/crunch.io/venv/bin/python
import sys
import os.path

from cr.lib.settings import settings
from cr.lib.entities.sources import Source
from cr.lib.entities.users import User
from cr.lib.entities.datasets import Dataset
from cr.lib.entities.projects import Project
from cr.lib.entities.teams import Team
from cr.lib.entities.geodata import GeoDatum, VariableGeoDatum
from cr.lib.stores import stores
from cr.lib.exceptions import NotFound

import logging

logger = logging.getLogger('cr.lib.index')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

logger.setLevel(logging.DEBUG)


def load_settings(configfilename):
    try:
        settings.update(settings.from_file(configfilename))
    except IOError:
        sys.exit(u'File "%s" cannot be read' % configfilename)

    #set up mongo
    stores.configure()
    stores.populate()

    #turn projects on
    stores.feature_flag.activate('projects')
    stores.feature_flag.activate('public_widget')

file_type_lookup = {'csv': 'csv', 'sav': 'spss'}

def create_source_from_file(file_name, user):
    with open(file_name) as f:
        return Source.from_file(f, file_type_lookup[file_name.split('.')[-1]], user_id=user.id)


def load_dataset_from_file(file_name, name=None, team=None, project=None, user=None):

    print 'loading dataset from file: %s with name: %s ' % (file_name, name)

    if name is None:
        name = os.path.basename(file_name).split('.')[0]

    file_name = os.path.abspath(os.path.dirname(__file__)) + '/swoosh/files/' + file_name

    captain = User.find_by_id(id='00002')

    if user is None:
        user = captain

    source = create_source_from_file(file_name, user)

    print 'creating dataset'
    ds = Dataset(owner_type='User', owner_id=user.id).create()
    ds.name = name
    ds.save()

    print 'appending source'
    # Add it to the dataset
    ds.append_source(source)

    print 'assigning first officer'
    first_officer = User.find_by_id(id='00004')

    ds.permissions.assign(user, first_officer, {'view': ['add_users', 'change_weight']})

    if team:
        ds.permissions.assign_team(team, {'view': ['add_users', 'change_weight']})

    if project:
        project.datasets.add(ds)

    ds.reindex()
    ds.release()
    return ds


def create_team():

    member_ids = ['00002', '00004']
    t = Team()
    t.name = 'Enterprise'
    t.owner_id = '00002'
    t.account_id = '00001'
    t.create()

    t.save()

    for user_id in member_ids:
        u = User.find_by_id(id=user_id)
        t.add_member(u, {'view': True})

    t.save()

    return t

def create_geodata():

    gb = GeoDatum()
    gb.location = 'https://s.crunch.io/geodata/UK-GeoJSON-part/json/eurostat/ew/topo_nuts1.json'
    #gb.location = 'http://local.crunch.io/geodata/UK-GeoJSON-part/json/eurostat/ew/topo_nuts1.json'
    gb.name = 'Great Britain'
    gb.description = ''
    gb.owner_id = '00002'
    gb.create()
    gb.save()

    us = GeoDatum()
    us.location = 'https://s.crunch.io/geodata/leafletjs/us-states.geojson'
    #us.location = 'http://local.crunch.io/geodata/leafletjs/us-states.topojson'
    us.name = 'United States'
    us.description = ''
    us.owner_id = '00002'
    us.create()
    us.save()

    return {'us': us, 'gb': gb}


def main():

    settings_file = 'backend-http/settings_local.py'
    try:
        settings_file = sys.argv[1]
    except IndexError:
        pass

    load_settings(settings_file)

    team = create_team()

    print 'setting up test users',

    captain = User.find_by_id(id='00002')
    captain.preferences = {'projects': True, 'labs': True}
    captain.permissions = {'create_users': True,
                           'create_datasets': True,
                           'alter_users': True}
    captain.save()

    project = Project(
            name='a_test_project',
            owner_id=captain.id,
            account_id='00001',
            id='08ed498c0aa1422491b95a6b04c69653'
        ).create()

    for name in ('captain',
                 'firstofficer',
                 'borg',
                 'armus',
                 'quark',
                 'grob',
                 'test.drop-zones',
                 'test.cat-array-filter',
                 'test.count-mr-filtered-rows',
                 'test.navigation',
                 'test.decimal-places-and-counts@crunch.io',
                 ):
        email = name+'@crunch.io'
        try:
            user = User.find_many_by_email([email])[0]
        except (NotFound, IndexError):
            user = User(email=email).create()
            user.permissions = {'create_datasets': True}
            auth = user.get_auth()
            auth.gen_password('asdfasdf')
            auth.save()

        user.save()
        project.members.add(user)

        if 'navigation' in email:
            navigation_user = user

        team.add_member(user, {'view': True})


    print 'done.'
    #for i in xrange(0, 100):
    #    load_dataset_from_file('simple_alltypes.sav', name='a_simple_alltypes_%s' % i, team=team, project=project)
    #    load_dataset_from_file('UCBAdmissions.csv', name='Admissions_%s' % i, team=team, project=project)
    #    load_dataset_from_file('ECON_few_columns.sav', name='econ_few_columns_%s' % i, team=team, project=project)


    load_dataset_from_file('simple_alltypes.sav', name='a_simple_alltypes', project=project)
    load_dataset_from_file('UCBAdmissions.csv', name='Admissions', team=team, project=project)
    load_dataset_from_file('ECON_few_columns.sav', name='a_econ_few_columns', team=team, project=project)

    #load_dataset_from_file('UCBAdmissions.csv', name='test-navigation_admissions', team=team, project=project, user=navigation_user)
    #load_dataset_from_file('simple_alltypes.sav', name='test-navigation_simple-alltypes', team=team, project=project, user=navigation_user)

    geodata = create_geodata()

    ds = load_dataset_from_file('pollsterdata.csv',
                                 name='a_pollsterdata',
                                 team=team, project=project)

    print 'setting geodata for pollsterdata'
    vg = VariableGeoDatum()
    vg.geodatum_id = geodata['us'].id
    vg.dataset_id = ds.id
    vg.variable_id = ds.primary.find_by_name('stabbr').id
    vg.display_field = 'name'
    vg.feature_key = 'properties.postal-code'
    vg.create()
    vg.save()

    vg = VariableGeoDatum()
    vg.geodatum_id = geodata['us'].id
    vg.dataset_id = ds.id
    vg.variable_id = ds.primary.find_by_name('state').id
    vg.display_field = 'name'
    vg.feature_key = 'properties.name'
    vg.create()
    vg.save()

if __name__ == '__main__':
    main()
