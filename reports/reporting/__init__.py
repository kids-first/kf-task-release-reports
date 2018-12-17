import boto3
import logging
from collections import defaultdict
from boto3.dynamodb.conditions import Key, Attr
from flask import Flask, Blueprint, current_app, jsonify, request, abort, json

logger = logging.getLogger()
logger.setLevel(logging.INFO)


reports_api = Blueprint('reports', __name__, url_prefix='/reports')


@reports_api.route('releases/<kf_id>', methods=['GET'])
def get_report(kf_id):
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)

    release_table = db.Table(current_app.config['RELEASE_SUMMARY_TABLE'])
    study_table = db.Table(current_app.config['STUDY_SUMMARY_TABLE'])

    resp = release_table.get_item(Key={'release_id': kf_id})
    if 'Item' not in resp or len(resp['Item']) == 0:
        abort(404, f'could not find a report for release {kf_id}')

    # Get all studies that are publicly released and are
    # not released in this release
    past_released_studies = study_table.scan(
        FilterExpression=Attr('state').eq('published')
    )
    for item in past_released_studies['Items']:
        item.update({"was_updated": False})

    # Key all publicly released studies by study kf_id
    studies = {sd['study_id']: sd for sd in
               past_released_studies['Items']}

    # Get all study summaries in the release
    current_studies = study_table.query(
        KeyConditionExpression=Key('release_id').eq(kf_id)
    )
    for item in current_studies['Items']:
        item.update({"was_updated": True})

    # Key all studies released in this release by
    # study kf_id and past releases
    studies.update({sd['study_id']: sd for sd in current_studies['Items']})

    resp['Item']['study_summaries'] = studies

    return jsonify(resp['Item']), 200


@reports_api.route('/<re_id>/<sd_id>', methods=['GET'])
def get_report_per_study(re_id, sd_id):
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    study_table = db.Table(current_app.config['STUDY_SUMMARY_TABLE'])

    # get the study summaries for the release
    resp = study_table.get_item(Key={'release_id': re_id, 'study_id': sd_id})
    if 'Item' not in resp or len(resp['Item']) == 0:
        abort(404, f'could not find study report'
              f' for release {re_id} and study id {sd_id}')

    return jsonify(resp['Item']), 200


@reports_api.route('studies/<sd_id>', methods=['GET'])
def get_filter_by_state_study(sd_id):
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)

    state = request.args.get('state')
    study_table = db.Table(current_app.config['STUDY_SUMMARY_TABLE'])
    # get the study summaries for the release and state
    query_parameters = {'IndexName': 'CreatedAtIndex',
                        'Select': 'ALL_PROJECTED_ATTRIBUTES',
                        'KeyConditionExpression':
                        Key('study_id').eq(sd_id),
                        'ScanIndexForward': False
                        }
    if state:
        query_parameters.update({'FilterExpression':
                                 Attr('state').eq(state)})
    resp = study_table.query(**query_parameters)

    if 'Items' not in resp or len(resp['Items']) == 0:
        abort(404, f'could not find study report'
              f' for study id {sd_id}')

    # Key all studies by study kf_id
    releases = {re['release_id']: re for re in resp['Items']}
    response = defaultdict(dict)
    response['Item']['releases'] = [releases]

    return jsonify(response['Item']), 200
