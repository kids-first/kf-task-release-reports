import boto3
import datetime
import requests
import pytest
from unittest.mock import patch
from reports.reporting import release_summary
from collections import Counter
from functools import partial


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


def test_get_studies(client, mocked_apis):
    """ Test that a task is set to canceled after being initialized """
    db = boto3.resource('dynamodb')
    db = boto3.client('dynamodb')

    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        studies, version, state = release_summary.get_studies('RE_00000000')
        assert studies == ['SD_00000000']
        assert version == '0.0.0'
        assert state == 'staged'

        mock_request.assert_called_with(
            'http://coordinator/releases/RE_00000000?limit=100',
            timeout=10)


@pytest.mark.parametrize("entity", ENTITIES)
def test_entity_counts(client, entity, mocked_apis):
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        r = release_summary.count_entity('SD_00000000', entity)
        assert r == 1


def test_count_study(client, mocked_apis):
    """ Test that entities are counted within a study """
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        r = release_summary.count_study('SD_00000000')
        assert r == {k: 1 for k in ENTITIES}


def test_count_studies(client, mocked_apis):
    """ Test that study counts are aggregated across studies """
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        studies = ['SD_00000000', 'SD_00000001']
        study_counts = {study: Counter(release_summary.count_study(study))
                        for study in studies}
        r = release_summary.collect_counts(study_counts)
        assert r == {k: 2 for k in ENTITIES + ['studies']}


def test_run(client, mocked_apis):
    """ Test that study counts are aggregated across studies """
    db = boto3.resource('dynamodb')
    release_table = db.Table('release-summary')
    study_table = db.Table('study-summary')
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        r = release_summary.run('TA_00000000', 'RE_00000000')
        assert all(k in r for k in ENTITIES)
        assert r['release_id'] == 'RE_00000000'
        assert r['task_id'] == 'TA_00000000'
    assert release_table.item_count == 1
    assert study_table.item_count == 1
    st = study_table.get_item(Key={
        'release_id': 'RE_00000000',
        'study_id': 'SD_00000000'
    })['Item']
    assert st['study_id'] == 'SD_00000000'
    assert st['version'] == '0.0.0'
    assert st['state'] == 'staged'
    assert all(st[k] == 1 for k in ENTITIES)


def test_get_report(client, mocked_apis):
    """ Test that api returns release summary """
    db = boto3.resource('dynamodb')
    table = db.Table('release-summary')
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        r = release_summary.run('TA_00000000', 'RE_00000000')
    assert table.item_count == 1

    resp = client.get('/reports/releases/RE_00000000')
    assert all(k in resp.json for k in ENTITIES)
    assert all(resp.json[k] == 1 for k in ENTITIES)
    assert resp.json['release_id'] == 'RE_00000000'
    assert resp .json['task_id'] == 'TA_00000000'
    assert 'SD_00000000' in resp.json['study_summaries']
    st = resp.json['study_summaries']['SD_00000000']


def test_report_not_found(client, mocked_apis):
    resp = client.get('/reports/releases/RE_XXXXXXXX')

    assert resp.status_code == 404
    assert 'could not find a report for release RE_' in resp.json['message']


def test_publish(client, mocked_apis):
    """ Test that release and study summary rows are updated upon publish """
    db = boto3.resource('dynamodb')
    release_table = db.Table('release-summary')
    study_table = db.Table('study-summary')

    def _test_summaries(state, version):
        assert release_table.item_count == 1
        re = release_table.get_item(Key={
            'release_id': 'RE_00000000',
            'study_id': 'SD_00000000'
        })['Item']
        assert re['release_id'] == 'RE_00000000'
        assert re['version'] == version
        assert re['state'] == state

        assert study_table.item_count == 1
        st = study_table.get_item(Key={
            'release_id': 'RE_00000000',
            'study_id': 'SD_00000000'
        })['Item']
        assert st['study_id'] == 'SD_00000000'
        assert st['version'] == version
        assert st['state'] == state
        assert all(st[k] == 1 for k in ENTITIES)

    with patch('requests.get') as mock_request:
        # The release has been run as candidate release 0.0.3
        mock_request.side_effect = partial(mocked_apis, version='0.0.3')
        r = release_summary.run('TA_00000000', 'RE_00000000')

        _test_summaries('staged', '0.0.3')

        # Now the release has been published and its version number bumped
        # in the coordinator to 0.1.0
        mock_request.side_effect = partial(mocked_apis, version='0.1.0')
        r = release_summary.publish('RE_00000000')

        _test_summaries('published', '0.1.0')


def test_publish_does_not_exist(client, mocked_apis):
    """
    Test behavior if a release is published and one of the summary rows
    do not exist
    """
    db = boto3.resource('dynamodb')
    release_table = db.Table('release-summary')
    study_table = db.Table('study-summary')

    with patch('requests.get') as mock_request:
        mock_request.side_effect = partial(mocked_apis, version='0.0.3')
        r = release_summary.run('TA_00000000', 'RE_00000000')

        assert release_table.item_count == 1
        assert study_table.item_count == 1
        # Now delete the summaries, as if it never existed
        release_table.delete_item(Key={
            'release_id': 'RE_00000000'
        })
        study_table.delete_item(Key={
            'release_id': 'RE_00000000',
            'study_id': 'SD_00000000'
        })
        assert release_table.item_count == 0
        assert study_table.item_count == 0

        # Publish the release
        mock_request.side_effect = partial(mocked_apis, version='0.1.0')
        r = release_summary.publish('RE_00000000')
        # There should still be no summary rows
        assert release_table.item_count == 0
        assert study_table.item_count == 0


def test_get_report_per_study(client, mocked_apis):
    """ Test that api returns release summary for specific study"""
    db = boto3.resource('dynamodb')
    table = db.Table('release-summary')
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        s = release_summary.run('TA_00000000', 'RE_00000000')
    assert table.item_count == 1

    resp = client.get('/reports/RE_00000000/SD_00000000')
    assert all(k in resp.json for k in ENTITIES)
    assert all(resp.json[k] == 1 for k in ENTITIES)
    assert resp.json['release_id'] == 'RE_00000000'
    assert resp .json['task_id'] == 'TA_00000000'
    assert 'SD_00000000' in resp.json['study_id']


def test_get_report_per_study_not_found(client):
    resp = client.get('/reports/RE_XXXXXXXX/SD_XXXXXXXX')

    assert resp.status_code == 404
    assert 'could not find study'
    ' report for release RE_' in resp.json['message']
    assert 'and study id SD_' in resp.json['message']


def test_get_report_per_study_filter_by_state(client, mocked_apis):
    """ Test that api returns release summary for specific study"""
    db = boto3.resource('dynamodb')
    table = db.Table('release-summary')
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        s = release_summary.run('TA_00000000', 'RE_00000000')
    assert table.item_count == 1

    resp = client.get('/reports/studies/SD_00000000?state=staged')
    r1 = resp.json['releases'][0]['RE_00000000']
    assert all(k in r1 for k in ENTITIES)
    assert all(r1
               [k] == 1 for k in ENTITIES)
    assert r1['release_id'] == 'RE_00000000'
    assert r1['task_id'] == 'TA_00000000'
    assert 'SD_00000000' in r1['study_id']


def test_get_report_per_study_filter_by_state_not_found(client):
    resp = client.get('/reports/studies/SD_XXXXXXXX?state=published')

    assert resp.status_code == 404
    assert 'could not find study'
    ' report for study SD_' in resp.json['message']
