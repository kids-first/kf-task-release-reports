import boto3
import requests
from flask import current_app, abort
from zappa.async import task


@task
def run(task_id, release_id):
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    table = db.Table(current_app.config['TASK_TABLE'])

    get_studies(release_id)

    # Update the task to staged in db
    task = table.update_item(
        Key={'task_id': task_id},
        UpdateExpression='SET state = staged',
        ReturnValues='ALL_NEW'
    )


def get_studies(release_id):
    coord_api = current_app.config['COORDINATOR_URL']
    resp = requests.get(f'{coord_api}/releases/{release_id}',
                        timeout=current_app.config['TIMEOUT'])

    try:
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        abort(500, 'there was a problem getting studies from the coordinator')

    studies = resp.json()['studies']
