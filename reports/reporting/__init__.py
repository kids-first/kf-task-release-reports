import boto3
import logging
from collections import defaultdict
from boto3.dynamodb.conditions import Key, Attr
from flask import Flask, Blueprint, current_app, jsonify, request, abort, json

logger = logging.getLogger()
logger.setLevel(logging.INFO)


reports_api = Blueprint('reports', __name__, url_prefix='/reports')


@reports_api.route('/<kf_id>', methods=['GET'])
def get_report(kf_id):
    db = boto3.resource('dynamodb')
    release_table = db.Table(current_app.config['RELEASE_SUMMARY_TABLE'])
    study_table = db.Table(current_app.config['STUDY_SUMMARY_TABLE'])

    resp = release_table.get_item(Key={'release_id': kf_id})
    if 'Item' not in resp or len(resp['Item']) == 0:
        abort(404, f'could not find a report for release {kf_id}')

    # Get all study summaries in the release
    studies = study_table.query(
        KeyConditionExpression=Key('release_id').eq(kf_id)
    )

    # Key all studies by study kf_id
    studies = {sd['study_id']: sd for sd in studies['Items']}

    resp['Item']['study_summaries'] = studies

    return jsonify(resp['Item']), 200


@reports_api.route('/<re_id>/<sd_id>', methods=['GET'])
def get_report_per_study(re_id, sd_id):
    db = boto3.resource('dynamodb')
    study_table = db.Table(current_app.config['STUDY_SUMMARY_TABLE'])

    # get the study summaries for the release
    resp = study_table.get_item(Key={'release_id': re_id, 'study_id': sd_id})
    if 'Item' not in resp or len(resp['Item']) == 0:
        abort(404, f'could not find study report'
              f' for release {re_id} and study id {sd_id}')

    return jsonify(resp['Item']), 200


@reports_api.route('/<sd_id>/state=<state>', methods=['GET'])
def get_filter_by_state_study(sd_id, state):
    db = boto3.resource('dynamodb')
    study_table = db.Table(current_app.config['STUDY_SUMMARY_TABLE'])
    # get the study summaries for the release and state
    resp = study_table.query(IndexName='CreatedAtIndex',
                             Select='ALL_PROJECTED_ATTRIBUTES',
                             KeyConditionExpression=Key('study_id').eq(sd_id),
                             FilterExpression=Attr('state').eq(state),
                             ScanIndexForward=False)
    if 'Items' not in resp or len(resp['Items']) == 0:
        abort(404, f'could not find study report'
              f' for study id {sd_id}')

    # Key all studies by study kf_id
    releases = {re['release_id']: re for re in resp['Items']}
    response = defaultdict(dict)
    response['Item']['releases'] = [releases]

    return jsonify(response['Item']), 200
