import boto3
import requests
import logging
from flask import current_app, abort, jsonify
from zappa.asynchronous import task
from reports.tasks.validation import validate_state
from reports.reporting import release_summary


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

    release_summary.run(task_id, release_id)

    validate_state(task_id, 'stage')

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
