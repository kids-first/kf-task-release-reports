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
        indexes = study_summary_schema['GlobalSecondaryIndexes']
        dynamodb_backend2.create_table('study-summary',
                                       schema=schema, indexes=indexes)

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


@pytest.yield_fixture(scope='function')
def mocked_apis():
    def get(url, *args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise requests.exceptions.HTTPError(self.status_code)

        # Coordinator response
        if 'coordinator' in url and url.split('/')[-2] == 'releases':
            return MockResponse({
                'studies': kwargs.get('studies', ['SD_00000000']),
                'version': kwargs.get('version', '0.0.0'),
                'state': kwargs.get('state', 'staged')
            }, 200)

        # Dataservice response
        if 'dataservice' in url:
            return MockResponse({'total': 1}, 200)

        # Ego response
        if 'ego' in url:
            mock_resp = MagicMock()
            mock_resp.json.return_value = True
            mock_resp.status_code = 200
            return mock_resp

        return MockResponse(None, 404)
    return get
