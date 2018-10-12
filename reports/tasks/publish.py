import boto3
import requests
import logging
from flask import current_app, abort, jsonify
from zappa.async import task
from reports.tasks.validation import validate_state


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def publish(task_id, release_id):
    """ Set state to 'publishing' and call the publishing task """
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    table = db.Table(current_app.config['TASK_TABLE'])

    validate_state(task_id, 'begin publishing')

    # Update the task to published in db
    task = table.update_item(
        Key={'task_id': task_id},
        UpdateExpression='SET #st = :new',
        ExpressionAttributeNames={'#st': 'state'},
        ExpressionAttributeValues={':new': 'publishing'},
        ReturnValues='ALL_NEW'
    )

    # Task should exist, give it returned earlier. Must be an update issue
    if 'Attributes' not in task or len(task['Attributes']) == 0:
        return abort(500, f"problem updating '{task_id}'")

    # Invoke the publish task
    do_publish(task_id, release_id)

    return jsonify(task['Attributes']), 200


@task
def do_publish(task_id, release_id):
    """
    All work is done in the 'running' state, so just update to 'published'
    here and report to coordinator.
    """
    if not current_app:
        from manage import app
        with app.app_context():
            publish_in_context(task_id, release_id)
    else:
        publish_in_context(task_id, release_id)


def publish_in_context(task_id, release_id):
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    table = db.Table(current_app.config['TASK_TABLE'])

    validate_state(task_id, 'publish')

    # Update the task to published in db
    task = table.update_item(
        Key={'task_id': task_id},
        UpdateExpression='SET #st = :new',
        ExpressionAttributeNames={'#st': 'state'},
        ExpressionAttributeValues={':new': 'published'},
        ReturnValues='ALL_NEW'
    )

    # Task should exist, give it returned earlier. Must be an update issue
    if 'Attributes' not in task or len(task['Attributes']) == 0:
        logger.error(f"problem updating task '{task_id}'")
        return abort(500, f"problem updating '{task_id}'")

    return jsonify(task['Attributes']), 200
