import boto3
import decimal
from flask import current_app, jsonify, abort
from .run import run


def start(task_id, release_id):
    """ Update a task's state to 'running' and start the background task """
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    table = db.Table(current_app.config['TASK_TABLE'])

    task = table.update_item(
        Key={'task_id': task_id},
        UpdateExpression='SET state = running',
        ReturnValues='ALL_NEW'
    )

    if 'Attributes' not in task or len(task['Attributes']) == 0:
        return abort(404, f"task '{task_id}' not found")

    run(task_id, release_id)

    return jsonify(task['Attributes']), 200
