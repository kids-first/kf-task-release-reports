import datetime
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
        app.config[
            "AUTH0_AUD"
        ] = "https://kf-release-coordinator.kidsfirstdrc.org"
        app_context = app.app_context()
        app_context.push()
        client = app.test_client()

        with open("tests/ego_token.json") as f:
            token = jwt.encode(json.load(f), "abc", "HS256").decode("utf-8")
        client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"

        # Allow all requests to be verified by ego
        mock_resp = MagicMock()
        mock_resp.json.return_value = True
        mock_resp.status_code = 200

        with patch('reports.authentication.requests.get') as mock_get:
            mock_get.return_value = mock_resp
            yield client


@pytest.fixture(scope="module", autouse=True)
def auth0_key_mock():
    """
    Mocks out the response from the /.well-known/jwks.json endpoint on auth0
    """
    middleware = "reports.authentication"
    with patch(f"{middleware}._get_new_key") as get_key:
        with open("tests/keys/jwks.json", "r") as f:
            get_key.return_value = json.load(f)["keys"][0]
            yield get_key


@pytest.fixture()
def service_token():
    """
    Generate a service token that will be used in machine-to-machine auth
    """
    with open("tests/keys/private_key.pem", "rb") as f:
        key = f.read()

    def make_token(scope="role:admin"):
        now = datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        token = {
            "iss": "auth0.com",
            "sub": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa@clients",
            "aud": "https://kf-release-coordinator.kidsfirstdrc.org",
            "iat": now.timestamp(),
            "exp": tomorrow.timestamp(),
            "azp": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "scope": scope,
            "gty": "client-credentials",
        }
        return jwt.encode(token, key, algorithm="RS256").decode("utf8")

    return make_token


@pytest.yield_fixture()
def no_auth_client(client, service_token):
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {service_token()}"
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
