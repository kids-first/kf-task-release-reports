import boto3
from unittest.mock import patch


def test_not_found(service_client):
    """ Test that an unkown task returns 404 """
    db = boto3.client('dynamodb')
    resp = db.describe_table(TableName='test')
    assert resp['Table']['ItemCount'] == 0

    resp = service_client.post(
        "/tasks",
        json={
            "action": "start",
            "release_id": "RE_00000000",
            "task_id": "TA_00000000",
        },
    )

    assert resp.status_code == 404
    assert resp.json['message'] == "task 'TA_00000000' not found"


def test_start(client):
    """ Test that the task's state is updated in dynamo """
    db = boto3.resource('dynamodb')
    table = db.Table('test')

    with patch('reports.reporting.release_summary.run') as mock_summary:
        resp = client.post('/tasks', json={'action': 'initialize',
                                           'release_id': 'RE_00000000',
                                           'task_id': 'TA_00000000'})

        resp = client.post('/tasks', json={'action': 'start',
                                           'release_id': 'RE_00000000',
                                           'task_id': 'TA_00000000'})

        assert resp.status_code == 200
        assert resp.json['state'] == 'running'

        task = table.get_item(Key={'task_id': 'TA_00000000'})['Item']
        assert task['state'] == 'staged'
