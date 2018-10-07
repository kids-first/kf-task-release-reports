import pytest
from flask import url_for
from reports import create_app


@pytest.yield_fixture(scope='session')
def client():
    app = create_app()
    app_context = app.app_context()
    app_context.push()
    yield app.test_client()
