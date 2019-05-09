db.feature_flag.update({'dataset_search_index': 'off'}, {'dataset_search_index': 'on'}, {'upsert': true});
db.feature_flag.update({'variable_search_index': 'off'}, {'variable_search_index': 'on'}, {'upsert': true});
db.access_permissions.remove({});
db.projects.remove({});
db.geodata.remove({});
db.project_dataset_order.remove({});
db.project_membership.remove({});
