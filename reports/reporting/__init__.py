import boto3
import logging
from boto3.dynamodb.conditions import Key
from flask import Flask, Blueprint, current_app, jsonify, request, abort, json

logger = logging.getLogger()
logger.setLevel(logging.INFO)


reports_api = Blueprint('reports', __name__, url_prefix='/reports')


@reports_api.route('/<kf_id>', methods=['GET'])
def get_report(kf_id):
    endpoint_url = current_app.config['DYNAMO_ENDPOINT']
    db = boto3.resource('dynamodb', endpoint_url=endpoint_url)
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
