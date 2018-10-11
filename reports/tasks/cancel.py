import boto3
import requests
import logging
from flask import current_app, abort, jsonify


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

    # Get task and check that it exists and may be canceled
    task = table.get_item(
        Key={'task_id': task_id},
        ProjectionExpression='#st',
        ExpressionAttributeNames={'#st': 'state'}
    )

    # If there's no 'Item', the task must not exist
    if 'Item' not in task or len(task['Item']) == 0:
        logger.error(f"tried to cancel a task that does not exist: {task_id}")
        abort(404, f"tried to cancel a task that does not exist: {task_id}")

    # We cannot publish a task which has not completed
    state = task['Item']['state']
    if state in ['published', 'canceled', 'failed']:
        logger.error(f"can not cancel task that is '{state}': {task_id}")
        abort(400, f"can not cancel task that is '{state}': {task_id}")

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
