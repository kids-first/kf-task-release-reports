import boto3
import datetime
import jwt
import pytest
from unittest.mock import patch, MagicMock


def test_no_header(client):
    """ Test behavior when no authorization header is given """

    resp = client.post(
        "/tasks",
        json={
            "action": "initialize",
            "release_id": "RE_00000000",
            "task_id": "TA_00000000",
        },
    )

    assert resp.status_code == 403
    assert "Must include an Authorization" in resp.json["message"]
