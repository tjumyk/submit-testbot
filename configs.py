import json

with open('config.json') as _f:
    config = json.load(_f)
site_config = config['SITE']
celery_config = config['AUTO_TEST']
worker_config = config.get('AUTO_TEST_WORKER')

server_url = site_config['root_url'] + site_config['base_url']
data_folder = config['DATA_FOLDER']
