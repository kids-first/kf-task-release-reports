import boto3
from datetime import datetime
from moto.dynamodb2 import dynamodb_backend2, mock_dynamodb2


def test_initialize(client):
    """ Test that new task is created in db """
    db = boto3.client('dynamodb')
    resp = db.describe_table(TableName='test')
    assert resp['Table']['ItemCount'] == 0

    resp = client.post('/tasks', json={'action': 'initialize',
                        'release_id': 'RE_00000000',
                        'task_id': 'TA_00000000'})
    assert resp.status_code == 201
    assert resp.json['release_id'] == 'RE_00000000'
    assert resp.json['task_id'] == 'TA_00000000'
    assert resp.json['state'] == 'initialized'

    resp = db.describe_table(TableName='test')
    assert resp['Table']['ItemCount'] == 1

    resp = db.get_item(TableName='test',
        Key={'task_id': {'S': 'TA_00000000'}},
    )

    assert resp['Item']['release_id']['S'] == 'RE_00000000'
    assert float(resp['Item']['created_at']['N']) < datetime.now().timestamp()
    assert resp['Item']['task_id']['S'] == 'TA_00000000'
    assert resp['Item']['state']['S'] == 'initialized'

    resp = client.post('/tasks', json={'action': 'get_status',
                        'release_id': 'RE_00000000',
                        'task_id': 'TA_00000000'})

    assert resp.status_code == 200
    assert resp.json['release_id'] == 'RE_00000000'
    assert resp.json['task_id'] == 'TA_00000000'
    assert resp.json['state'] == 'initialized'
    assert type(resp.json['created_at']) is float
