import boto3
import datetime
import jwt
import pytest
from unittest.mock import patch, MagicMock


def test_no_header(no_auth_client):
    """ Test behavior when no authorization header is given """

    resp = no_auth_client.post('/tasks', json={'action': 'initialize',
                                               'release_id': 'RE_00000000',
                                               'task_id': 'TA_00000000'})

    assert resp.status_code == 403
    assert 'Must include an Authorization' in resp.json['message']


def test_no_bearer(no_auth_client):
    """ Test behavior when no token type is given """

    token = {
      "aud": [
        "release-coordinator"
      ],
      "context": {
        "application": {
          "name": "release-coordinator",
          "redirectUri": "http://coordinator",
          "status": "Approved",
        }
      }
    }

    encoded = jwt.encode(token, 'test').decode('utf-8')

    resp = no_auth_client.post('/tasks', json={'action': 'initialize',
                                               'release_id': 'RE_00000000',
                                               'task_id': 'TA_00000000'},
                               headers={'Authorization': encoded})

    assert resp.status_code == 403
    assert 'Must include an Authorization' in resp.json['message']


def test_no_context(no_auth_client):
    """ Test behavior when no context is given in token """

    token = {
      "aud": [
        "release-coordinator"
      ]
    }

    encoded = jwt.encode(token, 'test').decode('utf-8')

    resp = no_auth_client.post('/tasks', json={'action': 'initialize',
                                               'release_id': 'RE_00000000',
                                               'task_id': 'TA_00000000'},
                               headers={'Authorization': 'Bearer ' + encoded})

    assert resp.status_code == 403
    assert 'Invalid JWT provided' == resp.json['message']


def test_bad_redirect(no_auth_client):
    """ Test behavior when the redirect doesn't match the coordinator url """

    token = {
      "aud": [
        "release-coordinator"
      ],
      "context": {
        "application": {
          "name": "release-coordinator",
          "redirectUri": "http://not-coord",
          "status": "Approved",
        }
      }
    }

    encoded = jwt.encode(token, 'test').decode('utf-8')

    resp = no_auth_client.post('/tasks', json={'action': 'initialize',
                                               'release_id': 'RE_00000000',
                                               'task_id': 'TA_00000000'},
                               headers={'Authorization': 'Bearer ' + encoded})

    assert resp.status_code == 403
    assert 'JWT does not contain proper permissions' == resp.json['message']


def test_bad_name(no_auth_client):
    """ Test behavior when the name doesn't match the release-coordinator """

    token = {
      "aud": [
        "release-coordinator"
      ],
      "context": {
        "application": {
          "name": "not-coord",
          "redirectUri": "http://coordinator",
          "status": "Approved",
        }
      }
    }

    encoded = jwt.encode(token, 'test').decode('utf-8')

    resp = no_auth_client.post('/tasks', json={'action': 'initialize',
                                               'release_id': 'RE_00000000',
                                               'task_id': 'TA_00000000'},
                               headers={'Authorization': 'Bearer ' + encoded})

    assert resp.status_code == 403
    assert 'JWT does not contain proper permissions' == resp.json['message']


def test_disabled(no_auth_client):
    """ Test behavior when the name doesn't match the release-coordinator """

    token = {
      "aud": [
        "release-coordinator"
      ],
      "context": {
        "application": {
          "name": "release-coordinator",
          "redirectUri": "http://coordinator",
          "status": "Disabled",
        }
      }
    }

    encoded = jwt.encode(token, 'test').decode('utf-8')

    resp = no_auth_client.post('/tasks', json={'action': 'initialize',
                                               'release_id': 'RE_00000000',
                                               'task_id': 'TA_00000000'},
                               headers={'Authorization': 'Bearer ' + encoded})

    assert resp.status_code == 403
    assert 'JWT does not contain proper permissions' == resp.json['message']


def test_unauthed_ego(no_auth_client):
    """ Test behavior when ego cannot verify token """

    token = {
      "aud": [
        "release-coordinator"
      ],
      "context": {
        "application": {
          "name": "release-coordinator",
          "redirectUri": "http://coordinator",
          "status": "Approved",
        }
      }
    }

    encoded = jwt.encode(token, 'test').decode('utf-8')

    # Mock out ego response to return invalid token
    mock_resp = MagicMock()
    mock_resp.json.return_value = False
    mock_resp.status_code = 200

    with patch('reports.authentication.requests.get') as mock_req:
        mock_req.return_value = mock_resp
        headers = {'Authorization': 'Bearer ' + encoded}
        resp = no_auth_client.post('/tasks', json={'action': 'initialize',
                                                   'release_id': 'RE_00000000',
                                                   'task_id': 'TA_00000000'},
                                   headers=headers)

        assert mock_req.call_count == 1
        mock_req.assert_called_with('http://ego/oauth/token/verify',
                                    headers={'token': encoded})
    assert resp.status_code == 403
    assert 'JWT does not contain proper permissions' == resp.json['message']


def test_ego_error(no_auth_client):
    """ Test behavior when ego errors """

    token = {
      "aud": [
        "release-coordinator"
      ],
      "context": {
        "application": {
          "name": "release-coordinator",
          "redirectUri": "http://coordinator",
          "status": "Approved",
        }
      }
    }

    encoded = jwt.encode(token, 'test').decode('utf-8')

    # Mock out ego response to return invalid token
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_resp.status_code = 500

    with patch('reports.authentication.requests.get') as mock_req:
        mock_req.return_value = mock_resp
        headers = {'Authorization': 'Bearer ' + encoded}
        resp = no_auth_client.post('/tasks', json={'action': 'initialize',
                                                   'release_id': 'RE_00000000',
                                                   'task_id': 'TA_00000000'},
                                   headers=headers)

        assert mock_req.call_count == 1
        mock_req.assert_called_with('http://ego/oauth/token/verify',
                                    headers={'token': encoded})
    assert resp.status_code == 403
    assert 'JWT does not contain proper permissions' == resp.json['message']
