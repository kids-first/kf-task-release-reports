import boto3
import datetime
from unittest.mock import patch


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


def test_publish(client, mocked_apis):
    """ Test that a task's state is updated to 'published' """
    db = boto3.resource('dynamodb')
    table = db.Table('test')

    _make_task('staged')

    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
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

    _make_task()

    resp = client.post('/tasks', json={'action': 'publish',
                                       'release_id': 'RE_00000000',
                                       'task_id': 'TA_00000000'})

    assert resp.status_code == 400
    assert "publishing a task that is 'init" in resp.json['message']

    task = table.get_item(Key={'task_id': 'TA_00000000'})['Item']
    assert task['state'] == 'initialized'


def _make_task(state='initialized'):
    db = boto3.resource('dynamodb')
    table = db.Table('test')

    response = table.put_item(
        Item={
            'task_id': 'TA_00000000',
            'release_id': 'RE_00000000',
            'created_at': str(datetime.datetime.now().timestamp()),
            'state': state,
        }
    )
    return response
