import boto3
import decimal
from flask import current_app, jsonify, abort


def get_status(task_id, release_id):
    """ Return basic task info including its state """
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    table = db.Table(current_app.config['DYNAMO_TABLE'])

    resp = table.get_item(Key={'task_id': task_id})

    if 'Item' not in resp:
        return abort(404, f"task '{task_id}' not found")
    return jsonify(resp['Item']), 200
