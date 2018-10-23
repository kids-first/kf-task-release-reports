import boto3
import datetime
import requests
import pytest
from unittest.mock import patch
from reports.reporting import release_summary
from collections import Counter


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


def mocked_apis(url, *args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.exceptions.HTTPError(self.status_code)

    # Coordinator response
    if 'coordinator' in url and url.split('/')[-2] == 'releases':
        return MockResponse({
            'studies': ['SD_00000000'],
            'version': '0.0.0'
        }, 200)

    # Dataservice response
    if 'dataservice' in url:
        return MockResponse({'total': 1}, 200)

    return MockResponse(None, 404)


def test_get_studies(client):
    """ Test that a task is set to canceled after being initialized """
    db = boto3.resource('dynamodb')
    db = boto3.client('dynamodb')

    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        studies, version = release_summary.get_studies('RE_00000000')
        assert studies == ['SD_00000000']
        assert version == '0.0.0'

        mock_request.assert_called_with(
            'http://coordinator/releases/RE_00000000?limit=100',
            timeout=10)


@pytest.mark.parametrize("entity", ENTITIES)
def test_entity_counts(client, entity):
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        r = release_summary.count_entity('SD_00000000', entity)
        assert r == 1


def test_count_study(client):
    """ Test that entities are counted within a study """
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        r = release_summary.count_study('SD_00000000')
        assert r == {k: 1 for k in ENTITIES}


def test_count_studies(client):
    """ Test that study counts are aggregated across studies """
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        studies = ['SD_00000000', 'SD_00000001']
        study_counts = {study: Counter(release_summary.count_study(study))
                        for study in studies}
        r = release_summary.collect_counts(study_counts)
        assert r == {k: 2 for k in ENTITIES + ['studies']}


def test_run(client):
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
    assert all(st[k] == 1 for k in ENTITIES)


def test_get_report(client):
    """ Test that api returns release summary """
    db = boto3.resource('dynamodb')
    table = db.Table('release-summary')
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mocked_apis
        r = release_summary.run('TA_00000000', 'RE_00000000')
    assert table.item_count == 1

    resp = client.get('/reports/RE_00000000')
    assert all(k in resp.json for k in ENTITIES)
    assert all(resp.json[k] == 1 for k in ENTITIES)
    assert resp.json['release_id'] == 'RE_00000000'
    assert resp .json['task_id'] == 'TA_00000000'
    assert len(resp.json['study_summaries']) == 1


def test_report_not_found(client):
    resp = client.get('/reports/RE_XXXXXXXX')

    assert resp.status_code == 404
    assert 'could not find a report for release RE_' in resp.json['message']
