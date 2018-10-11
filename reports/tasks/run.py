import boto3
import requests
import logging
from flask import current_app, abort, jsonify
from zappa.async import task


logger = logging.getLogger()
logger.setLevel(logging.INFO)


@task
def run(task_id, release_id):
    """
    If this is being run as a seperate lambda call, a new app context needs to
    be made to access 'current_app'
    """
    if not current_app:
        from manage import app
        with app.app_context():
            run_it(task_id, release_id)
    else:
        run_it(task_id, release_id)


def run_it(task_id, release_id):
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    table = db.Table(current_app.config['TASK_TABLE'])

    get_studies(release_id)

    # Check the task's state to make sure it's ok to update to 'staged'
    task = table.get_item(
        Key={'task_id': task_id},
        ProjectionExpression='#st',
        ExpressionAttributeNames={'#st': 'state'}
    )

    # If there's no 'Item', the task must not exist
    if 'Item' not in task or len(task['Item']) == 0:
        logger.error(f"tried to stage task that does not exist: {task_id}")
        return

    # Need to verify that the task has not been canceled or failed since run
    if task['Item']['state'] != 'running':
        logger.error(f"tried to stage a task that is not running: {task_id}")
        return

    # Update the task to staged in db
    task = table.update_item(
        Key={'task_id': task_id},
        UpdateExpression='SET #st = :new',
        ExpressionAttributeNames={'#st': 'state'},
        ExpressionAttributeValues={':new': 'staged'},
        ReturnValues='ALL_NEW'
    )
    logger.info(f'{task_id} staged successfully')

    return jsonify(task['Attributes']), 200


def get_studies(release_id):
    coord_api = current_app.config['COORDINATOR_URL']
    resp = requests.get(f'{coord_api}/releases/{release_id}',
                        timeout=current_app.config['TIMEOUT'])

    try:
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        logger.error(f'could not get studies for {release_id}')
        abort(500, 'there was a problem getting studies from the coordinator')

    studies = resp.json()['studies']
