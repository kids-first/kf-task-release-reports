import boto3
import datetime
import requests
import logging
from collections import Counter
from flask import current_app


logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Entities to collect total counts for
ENTITIES = [
    'participants',
    'biospecimens',
    'phenotypes',
    'genomic-files',
    'study-files',
    'read-groups',
    'diagnoses',
    'sequencing-experiments',
    'families'
]


def run(task_id, release_id):
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    release_table = db.Table(current_app.config['RELEASE_SUMMARY_TABLE'])
    study_table = db.Table(current_app.config['STUDY_SUMMARY_TABLE'])

    studies, version, state = get_studies(release_id)

    # Get counts by study
    study_counts = {study: Counter(count_study(study)) for study in studies}

    # Save each study summary to dynamo
    base_fields = {
        'task_id': task_id,
        'release_id': release_id,
        'version': version,
        'state': state,
        'created_at': datetime.datetime.now().isoformat()
    }

    for study, counts in study_counts.items():
        counts = dict(counts)
        counts.update(base_fields)
        counts.update({'study_id': study})
        response = study_table.put_item(
            Item=counts,
            ReturnValues='NONE',
            ReturnConsumedCapacity='NONE',
        )

    # Aggregate all entities
    counts = collect_counts(study_counts)
    counts.update(base_fields)
    logger.info(counts)

    # Store the release count summary in dynamo
    response = release_table.put_item(
        Item=counts,
        ReturnValues='NONE',
        ReturnConsumedCapacity='NONE',
    )
    return counts


def publish(release_id):
    """
    Update the study and release summary rows with the new version number and
    set state to published

    :param release_id: The kf_id of the release to update
    """
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    release_table = db.Table(current_app.config['RELEASE_SUMMARY_TABLE'])
    study_table = db.Table(current_app.config['STUDY_SUMMARY_TABLE'])

    studies, version, state = get_studies(release_id)

    # Update study summary rows
    for study_id in studies:
        st = study_table.update_item(
            Key={'release_id': release_id, 'study_id': study_id},
            UpdateExpression='SET #st= :new, #vr= :next',
            ExpressionAttributeNames={
                '#st': 'state',
                '#vr': 'version'
            },
            ExpressionAttributeValues={
                ':new': 'published',
                ':next': version
            },
            ReturnValues='ALL_NEW'
        )

    # Update the release summary row
    re = release_table.update_item(
        Key={'release_id': release_id},
        UpdateExpression='SET #st = :new, #ver = :next',
        ExpressionAttributeNames={'#st': 'state', '#ver': 'version'},
        ExpressionAttributeValues={':new': 'published', ':next': version},
        ReturnValues='ALL_NEW'
    )


def get_studies(release_id):
    """
    Retieve the study ids, version number, and state of a given release
    from the coordinator.

    :param release_id: The kf_id of the release to retrieve info for

    :returns: (List of study ids, version number, state)
    """
    coord_api = current_app.config['COORDINATOR_URL']
    resp = requests.get(f'{coord_api}/releases/{release_id}?limit=100',
                        timeout=current_app.config['TIMEOUT'])

    try:
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        logger.error(f'could not get studies for {release_id}')
        abort(500, 'there was a problem getting studies from the coordinator')

    studies = resp.json()['studies']
    version = resp.json()['version']
    state = resp.json()['state']
    return studies, version, state


def collect_counts(study_counts):
    """ Aggregates counts for specified entities in each study """
    # Total counts
    total_counts = Counter()
    for study, counts in study_counts.items():
        total_counts.update(counts)
    total_counts = dict(total_counts)
    total_counts['studies'] = len(study_counts.keys())

    return total_counts


def count_study(study_id):
    """
    Query the dataservice for totals of visible entities and return a dict
    containing the number of each

    :param study_id: The study id to filter entities by
    :returns: A dict of entities to  visible counts for the study
    """

    counts = {entity: count_entity(study_id, entity) for entity in ENTITIES}
    # Filter out entities that had request issues
    return {k: v for k, v in counts.items() if v is not None}


def count_entity(study_id, entity):
    """
    Query the dataservice for the total visible entities of a certain type
    """
    dataservice_api = current_app.config['DATASERVICE_URL']
    url = (f'{dataservice_api}/{entity}?' +
           f'study_id={study_id}&visible=true&limit=1')

    try:
        resp = requests.get(url, timeout=current_app.config['TIMEOUT'])
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        logger.error(f'could not get {url}')
        return None

    if 'total' not in resp.json():
        logger.error(f'mishaped response from {url}')
        return None

    return resp.json()['total']
