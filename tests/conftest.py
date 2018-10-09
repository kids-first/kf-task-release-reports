import pytest
from reports import create_app
from moto.dynamodb2 import dynamodb_backend2, mock_dynamodb2
from schema import task_schema


@pytest.yield_fixture(scope='module')
def client():
    with mock_dynamodb2():
        dynamodb_backend2.create_table('test',
            schema=task_schema['KeySchema'],
            indexes=task_schema['LocalSecondaryIndexes'])
        app = create_app()
        app.config['DYNAMO_ENDPOINT'] = None
        app.config['DYNAMO_TABLE'] = 'test'
        app_context = app.app_context()
        app_context.push()
        yield app.test_client()
