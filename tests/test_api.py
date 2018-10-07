import json
import pytest
from flask import url_for
from reports import create_app


def test_status(client):
    resp = client.get('/status')
    assert resp.status_code == 200
    assert 'name' in json.loads(resp.data.decode())
    assert 'version' in json.loads(resp.data.decode())
