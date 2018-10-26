import boto3
from datetime import datetime
from moto.dynamodb2 import dynamodb_backend2, mock_dynamodb2


def test_not_found(client):
    """ Test that an unkown task returns 404 """
    db = boto3.client('dynamodb')
    resp = db.describe_table(TableName='test')
    assert resp['Table']['ItemCount'] == 0

    resp = client.post('/tasks', json={'action': 'get_status',
                                       'release_id': 'RE_00000000',
                                       'task_id': 'TA_00000000'})

    assert resp.status_code == 404
    assert resp.json['message'] == "task 'TA_00000000' not found"
    assert 'Access-Control-Allow-Origin' in resp.headers
    assert resp.headers['Access-Control-Allow-Origin'] == '*'
