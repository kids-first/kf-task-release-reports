import boto3
import requests
from unittest.mock import patch
from datetime import datetime
from moto.dynamodb2 import dynamodb_backend2, mock_dynamodb2
import reports.tasks


def mocked_coordinator_releases(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.exceptions.HTTPError(self.status_code)

    if args[0].split('/')[-2] == 'releases':
        return MockResponse({"studies": ["SD_00000000"]}, 200)

    return MockResponse(None, 404)


def test_get_studies(client):
    """ Test that studies are fetched from the dataservice """
    with patch('requests.get') as mock_coord:
        mock_coord.side_effect = mocked_coordinator_releases
        resp = reports.tasks.run.get_studies('RE_00000000')
        mock_coord.assert_called_with(
            'http://localhost:5001/releases/RE_00000000',
            timeout=10)
