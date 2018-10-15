import boto3
import requests
from unittest.mock import patch
from datetime import datetime
from moto.dynamodb2 import dynamodb_backend2, mock_dynamodb2
import reports.tasks


def test_get_studies(client):
    """ Test that studies are fetched from the dataservice """
    pass
