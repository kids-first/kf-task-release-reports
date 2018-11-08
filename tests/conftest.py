import pytest
import json
import jwt
from reports import create_app
from unittest.mock import patch, MagicMock
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
        app.config['EGO_URL'] = 'http://ego'
        app_context = app.app_context()
        app_context.push()
        client = app.test_client()

        with open('tests/ego_token.json') as f:
            token = jwt.encode(json.load(f), 'abc', 'HS256').decode('utf-8')
        client.environ_base['HTTP_AUTHORIZATION'] = f"Bearer {token}"

        # Allow all requests to be verified by ego
        mock_resp = MagicMock()
        mock_resp.json.return_value = True
        mock_resp.status_code = 200

        with patch('reports.authentication.requests.get') as mock_get:
            mock_get.return_value = mock_resp
            yield client


@pytest.yield_fixture(scope='module')
def no_auth_client(client):
    client.environ_base['HTTP_AUTHORIZATION'] = ''
    yield client
