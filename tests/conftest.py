import pytest
from reports import create_app
from moto.dynamodb2 import dynamodb_backend2, mock_dynamodb2
from schema import task_schema, release_summary_schema, study_summary_schema


@pytest.yield_fixture(scope='module')
def client():
    with mock_dynamodb2():
        schema = task_schema['KeySchema']
        indexes = task_schema['GlobalSecondaryIndexes']
        dynamodb_backend2.create_table('test', schema=schema, indexes=indexes)

        schema = release_summary_schema['KeySchema']
        dynamodb_backend2.create_table('release-summary',
                                       schema=schema, indexes=[])

        schema = study_summary_schema['KeySchema']
        dynamodb_backend2.create_table('study-summary',
                                       schema=schema, indexes=[])

        app = create_app()
        app.config['DYNAMO_ENDPOINT'] = None
        app.config['TASK_TABLE'] = 'test'
        app.config['RELEASE_SUMMARY_TABLE'] = 'release-summary'
        app.config['DATASERVICE_URL'] = 'http://dataservice'
        app.config['COORDINATOR_URL'] = 'http://coordinator'
        app_context = app.app_context()
        app_context.push()
        yield app.test_client()
