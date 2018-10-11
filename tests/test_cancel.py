import boto3
import requests
from unittest.mock import patch
from moto.dynamodb2 import dynamodb_backend2, mock_dynamodb2
import reports.tasks


def test_cancel_from_init(client):
    """ Test that a task is set to canceled after being initialized """
    db = boto3.resource('dynamodb')
    table = db.Table('test')
    with patch('reports.tasks.run.requests') as mock_coord:
        resp = client.post('/tasks', json={'action': 'initialize',
                                           'release_id': 'RE_00000000',
                                           'task_id': 'TA_00000000'})

        resp = client.post('/tasks', json={'action': 'cancel',
                                           'release_id': 'RE_00000000',
                                           'task_id': 'TA_00000000'})

        assert resp.status_code == 200
        assert resp.json['state'] == 'canceled'

        task = table.get_item(Key={'task_id': 'TA_00000000'})['Item']
        assert task['state'] == 'canceled'


def test_cancel_from_staged(client):
    """ Test that a task is set to canceled after being staged """
    db = boto3.resource('dynamodb')
    table = db.Table('test')

    with patch('reports.tasks.run.requests') as mock_coord:
        resp = client.post('/tasks', json={'action': 'initialize',
                                           'release_id': 'RE_00000000',
                                           'task_id': 'TA_00000000'})

        resp = client.post('/tasks', json={'action': 'start',
                                           'release_id': 'RE_00000000',
                                           'task_id': 'TA_00000000'})

        resp = client.post('/tasks', json={'action': 'cancel',
                                           'release_id': 'RE_00000000',
                                           'task_id': 'TA_00000000'})

        assert resp.status_code == 200
        assert resp.json['state'] == 'canceled'

        task = table.get_item(Key={'task_id': 'TA_00000000'})['Item']
        assert task['state'] == 'canceled'
