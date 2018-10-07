import json
import pytest
from flask import url_for
from reports import create_app


def test_bad_verb(client):
    resp = client.get('/tasks')
    assert resp.status_code == 405


def test_no_body(client):
    resp = client.post('/tasks')
    assert resp.status_code == 400
    assert 'message' in resp.json
    assert 'could not understand' in resp.json['message']


def test_empty_body(client):
    resp = client.post('/tasks', json={})
    assert resp.status_code == 400
    assert 'message' in resp.json
    assert 'No body recieved' in resp.json['message']


def test_bad_input(client):
    resp = client.post('/tasks', json={'action': 'blah'})
    assert resp.status_code == 400
    assert 'message' in resp.json
    assert "'action' and 'task_id' fields" in resp.json['message']


def test_bad_action(client):
    resp = client.post('/tasks', json={'task_id': 'blah', 'action': 'blah'})
    assert resp.status_code == 400
    assert 'message' in resp.json
    assert "'blah' is not a known action" in resp.json['message']


def test_bad_task(client):
    resp = client.post('/tasks', json={'task_id': 'blah', 'action': 'start'})
    assert resp.status_code == 400
    assert 'message' in resp.json
    assert "'blah' is not a valid kf_id" in resp.json['message']
