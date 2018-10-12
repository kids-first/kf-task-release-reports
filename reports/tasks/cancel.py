import boto3
import requests
import logging
from flask import current_app, abort, jsonify
from reports.tasks.validation import validate_state


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def cancel(task_id, release_id):
    """
    Immediately cancel a task.
    In the case of reports, this only results in the state of the task
    being updated to 'canceled'.
    """
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    table = db.Table(current_app.config['TASK_TABLE'])

    validate_state(task_id, 'cancel')

    logger.info(f'{task_id} was told to cancel by the coordinator')
    # Update the task to staged in db
    task = table.update_item(
        Key={'task_id': task_id},
        UpdateExpression='SET #st = :new',
        ExpressionAttributeNames={'#st': 'state'},
        ExpressionAttributeValues={':new': 'canceled'},
        ReturnValues='ALL_NEW'
    )
    logger.info(f'{task_id} was canceled')

    return jsonify(task['Attributes']), 200
