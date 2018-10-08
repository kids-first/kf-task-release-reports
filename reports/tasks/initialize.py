import datetime
import boto3
from flask import current_app, jsonify


def initialize(task_id, release_id):
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.client('dynamodb', endpoint_url=endpoint_url)

    table = current_app.config['DYNAMO_TABLE']
    response = db.put_item(
        TableName=table,
        Item={
            'task_id': {
                'S': task_id,
            },
            'release_id': {
                'S': release_id,
            },
            'created_at': {
                'N': str(datetime.datetime.now().timestamp())
            },
            'state': {
                'S': 'initialized',
            },
        },
        ReturnValues='NONE',
        ReturnConsumedCapacity='NONE',
    )

    return jsonify({
        'task_id': task_id,
        'release_id': release_id,
        'state': 'initialized'
    }), 201
