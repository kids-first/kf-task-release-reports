import boto3
import requests
import logging
from flask import current_app, abort, jsonify
from zappa.async import task


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def publish(task_id, release_id):
    """ Set state to 'publishing' and call the publishing task """
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    table = db.Table(current_app.config['TASK_TABLE'])

    # Retrieve only the 'state' for the task to verify it is ready for publish
    task = table.get_item(
        Key={'task_id': task_id},
        ProjectionExpression='state'
    )

    # If there's no 'Item', the task must not exist
    if 'Item' not in task or len(task['Item']) == 0:
        logger.error(f"tried to publish task that does not exist: {task_id}")
        return abort(404, f"task '{task_id}' not found")

    # We cannot publish a task which has not completed
    if task['Item']['state'] != 'staged':
        logger.error(f"tried to publish task that is not staged: {task_id}")
        abort(400, 'may only publish a task that is staged')

    # Update the task to published in db
    task = table.update_item(
        Key={'task_id': task_id},
        UpdateExpression='SET state = publishing',
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

    # Retrieve only the 'state' for the task to verify it is ready for publish
    task = table.get_item(
        Key={'task_id': task_id},
        ProjectionExpression='state'
    )

    # If there's no 'Item', the task must not exist
    if 'Item' not in task or len(task['Item']) == 0:
        logger.error(f"tried to publish task that does not exist: {task_id}")
        return

    # We cannot publish a task which has not completed
    if task['Item']['state'] != 'publishing':
        logger.error("Can not publish task that is not 'publishing'")
        return

    # Update the task to published in db
    task = table.update_item(
        Key={'task_id': task_id},
        UpdateExpression='SET state = published',
        ReturnValues='ALL_NEW'
    )

    # Task should exist, give it returned earlier. Must be an update issue
    if 'Attributes' not in task or len(task['Attributes']) == 0:
        logger.error(f"problem updating task '{task_id}'")
        return abort(500, f"problem updating '{task_id}'")

    return jsonify(task['Attributes']), 200
