import boto3
import datetime


def test_cancel_from_init(client):
    """ Test that a task is set to canceled after being initialized """
    db = boto3.resource('dynamodb')
    table = db.Table('test')

    _make_task('initialized')

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

    _make_task('staged')

    resp = client.post('/tasks', json={'action': 'cancel',
                                       'release_id': 'RE_00000000',
                                       'task_id': 'TA_00000000'})

    assert resp.status_code == 200
    assert resp.json['state'] == 'canceled'

    task = table.get_item(Key={'task_id': 'TA_00000000'})['Item']
    assert task['state'] == 'canceled'


def test_cancel_from_running(client):
    """ Test that task may not be canceled twice """
    db = boto3.resource('dynamodb')
    table = db.Table('test')

    _make_task('running')

    resp = client.post('/tasks', json={'action': 'cancel',
                                       'release_id': 'RE_00000000',
                                       'task_id': 'TA_00000000'})

    assert resp.status_code == 200
    assert resp.json['state'] == 'canceled'

    task = table.get_item(Key={'task_id': 'TA_00000000'})['Item']
    assert task['state'] == 'canceled'


def test_cancel_from_canceled(client):
    """ Test that task may not be canceled twice """
    db = boto3.resource('dynamodb')
    table = db.Table('test')

    _make_task()

    resp = client.post('/tasks', json={'action': 'cancel',
                                       'release_id': 'RE_00000000',
                                       'task_id': 'TA_00000000'})

    resp = client.post('/tasks', json={'action': 'cancel',
                                       'release_id': 'RE_00000000',
                                       'task_id': 'TA_00000000'})

    assert resp.status_code == 400
    assert "not cancel a task that is 'canceled'" in resp.json['message']

    task = table.get_item(Key={'task_id': 'TA_00000000'})['Item']
    assert task['state'] == 'canceled'


def test_cancel_from_published(client):
    """ Test that published task may not be canceled """
    db = boto3.resource('dynamodb')
    table = db.Table('test')

    _make_task('published')

    resp = client.post('/tasks', json={'action': 'cancel',
                                       'release_id': 'RE_00000000',
                                       'task_id': 'TA_00000000'})

    assert resp.status_code == 400
    assert "not cancel a task that is 'published'" in resp.json['message']

    task = table.get_item(Key={'task_id': 'TA_00000000'})['Item']
    assert task['state'] == 'published'


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
