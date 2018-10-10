def test_bad_verb(client):
    resp = client.get('/tasks')
    assert resp.status_code == 405


def test_no_body(client):
    resp = client.post('/tasks')
    assert resp.status_code == 400
    assert 'message' in resp.json
    assert 'could not understand' in resp.json['message']


def test_empty_body(client):
    resp = client.post('/tasks', json={})
    assert resp.status_code == 400
    assert 'message' in resp.json
    assert 'No body recieved' in resp.json['message']


def test_bad_input(client):
    resp = client.post('/tasks', json={'action': 'initialize'})
    assert resp.status_code == 400
    assert 'message' in resp.json
    assert "'action', 'task_id', and 'release_id'" in resp.json['message']

    resp = client.post('/tasks', json={'action': 'initialize',
                                       'task_id': 'TA_00000000'})
    assert resp.status_code == 400
    assert 'message' in resp.json
    assert "'action', 'task_id', and 'release_id'" in resp.json['message']

    resp = client.post('/tasks', json={'action': 'initialize',
                                       'release_id': 'RE_00000000',
                                       'task_id': 'TA_00000000'})
    assert resp.status_code == 200


def test_bad_action(client):
    resp = client.post('/tasks', json={
        'task_id': 'TA_00000000',
        'release_id': 'RE_00000000',
        'action': 'blah'})
    assert resp.status_code == 400
    assert 'message' in resp.json
    assert "'blah' is not a known action" in resp.json['message']


def test_bad_task_id(client):
    resp = client.post('/tasks', json={
        'task_id': 'blah',
        'release_id': 'RE_00000000',
        'action': 'initialize'})
    assert resp.status_code == 400
    assert 'message' in resp.json
    assert "'blah' is not a valid kf_id" in resp.json['message']


def test_bad_release_id(client):
    resp = client.post('/tasks', json={
        'task_id': 'TA_00000000',
        'release_id': 'blah',
        'action': 'initialize'})
    assert resp.status_code == 400
    assert 'message' in resp.json
    assert "'blah' is not a valid kf_id" in resp.json['message']
