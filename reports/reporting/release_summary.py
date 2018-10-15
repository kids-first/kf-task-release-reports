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
    table = db.Table(current_app.config['RELEASE_SUMMARY_TABLE'])

    studies, version = get_studies(release_id)

    counts = collect_counts(studies)

    base_fields = {
        'task_id': task_id,
        'release_id': release_id,
        'version': version
    }
    counts.update(base_fields)
    logger.info(counts)

    # Store the count summary in dynamo
    response = table.put_item(
        Item=counts,
        ReturnValues='NONE',
        ReturnConsumedCapacity='NONE',
    )
    return counts


def get_studies(release_id):
    """
    Retieve the study ids for the release and the release's version number
    from the coordinator
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
    return studies, version


def collect_counts(studies):
    """ Aggregates counts for specified entities in each study """
    # Counts by study
    study_counts = {study: Counter(count_study(study)) for study in studies}
    # Total counts
    total_counts = dict(sum(study_counts.values(), Counter()))
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
    url = f'{dataservice_api}/{entity}?{study_id}&visible=true&limit=1'

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
