import os


class Config():
    # Load vars from settings file into environment if in local
    if ('SERVERTYPE' not in os.environ):
        import json
        import os
        json_data = open('zappa_settings.json')
        env_vars = json.load(json_data)['dev']['aws_environment_variables']
        for key, val in env_vars.items():
            os.environ[key] = val

    STAGE = os.environ.get('STAGE', 'dev')

    DATASERVICE_URL = os.environ.get('DATASERVICE_URL',
                                     'http://localhost:5000')
    COORDINATOR_URL = os.environ.get('COORDINATOR_URL',
                                     'http://localhost:5001')
    DYNAMO_ENDPOINT = os.environ.get('DYNAMO_ENDPOINT',
                                     'http://localhost:8050')
    DYNAMO_TABLE = os.environ.get('DYNAMO_TABLE',
                                  'release-reports')
