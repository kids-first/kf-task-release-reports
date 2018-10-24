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
    TASK_TABLE = os.environ.get('TASK_TABLE',
                                'release-reports')
    RELEASE_SUMMARY_TABLE = os.environ.get('RELEASE_SUMMARY_TABLE',
                                           'release-summary')
    STUDY_SUMMARY_TABLE = os.environ.get('STUDY_SUMMARY_TABLE',
                                         'study-summary')
    TIMEOUT = os.environ.get('TIMEOUT', 10)
