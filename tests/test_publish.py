import boto3
from datetime import datetime
from unittest.mock import patch
from moto.dynamodb2 import dynamodb_backend2, mock_dynamodb2


def test_not_found(client):
    """ Test that an unkown task returns 404 """
    db = boto3.client('dynamodb')
    resp = db.describe_table(TableName='test')
    assert resp['Table']['ItemCount'] == 0

    resp = client.post('/tasks', json={'action': 'publish',
                                       'release_id': 'RE_00000000',
                                       'task_id': 'TA_00000000'})

    assert resp.status_code == 404
    assert 'a task that does not exist' in resp.json['message']


def test_publish(client):
    """ Test that a task's state is updated to 'published' """
    db = boto3.resource('dynamodb')
    table = db.Table('test')

    with patch('reports.tasks.run.requests') as mock_coord:
        resp = client.post('/tasks', json={'action': 'initialize',
                                           'release_id': 'RE_00000000',
                                           'task_id': 'TA_00000000'})

        resp = client.post('/tasks', json={'action': 'start',
                                           'release_id': 'RE_00000000',
                                           'task_id': 'TA_00000000'})

        resp = client.post('/tasks', json={'action': 'publish',
                                           'release_id': 'RE_00000000',
                                           'task_id': 'TA_00000000'})

        # API should respond with publish, but task should be published in db
        assert resp.status_code == 200
        assert resp.json['state'] == 'publishing'

        task = table.get_item(Key={'task_id': 'TA_00000000'})['Item']
        assert task['state'] == 'published'


def test_premature_publish(client):
    """ Test that a task cannot be published before it is staged """
    db = boto3.resource('dynamodb')
    table = db.Table('test')

    with patch('reports.tasks.run.requests') as mock_coord:
        resp = client.post('/tasks', json={'action': 'initialize',
                                           'release_id': 'RE_00000000',
                                           'task_id': 'TA_00000000'})

        resp = client.post('/tasks', json={'action': 'publish',
                                           'release_id': 'RE_00000000',
                                           'task_id': 'TA_00000000'})

        assert resp.status_code == 400
        assert "publishing a task that is 'init" in resp.json['message']

        task = table.get_item(Key={'task_id': 'TA_00000000'})['Item']
        assert task['state'] == 'initialized'
