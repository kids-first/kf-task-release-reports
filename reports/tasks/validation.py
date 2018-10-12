import boto3
import logging
from flask import abort, current_app


logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Contains a map of actions to states which that action may be applied to
ALLOWED_STATES = {
    'initialize': [],
    'start': ['initialized'],
    'stage': ['running'],
    'begin publishing': ['staged'],
    'publish': ['publishing'],
    'cancel': ['initialized', 'running', 'staged']
}


def validate_state(task_id, action):
    """
    Check a given task's state stored on the db

    If the task with `task_id` is not found, abort with a 404.
    If the action is not allowed for the current state, abort with 400.

    :return: `True` if valid, aborts otherwise
    """
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    table = db.Table(current_app.config['TASK_TABLE'])

    # Get the given task's state
    task = table.get_item(
        Key={'task_id': task_id},
        ProjectionExpression='#st',
        ExpressionAttributeNames={'#st': 'state'}
    )

    # If there's no 'Item', the task must not exist
    if 'Item' not in task or len(task['Item']) == 0:
        logger.error(f"can not {action} a task that does not exist: {task_id}")
        abort(404, f"can not {action} a task that does not exist: {task_id}")

    # Don't validate action if it's not in the state mapping
    if action not in ALLOWED_STATES:
        return True

    # Check if the transition is allowed
    state = task['Item']['state']
    if state not in ALLOWED_STATES[action]:
        logger.error(f"can not {action} a task that is '{state}': {task_id}")
        abort(400, f"can not {action} a task that is '{state}': {task_id}")

    return True
