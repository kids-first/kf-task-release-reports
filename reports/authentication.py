import jwt
import logging
import requests
from urllib.parse import urlparse
from flask import current_app, request, abort


def authenticate_coordinator():
    """ Verify a jwt by performing token checks and validating with ego """
    logger = current_app.logger

    auth = request.headers.get('Authorization')
    if auth is None or not auth.lower().startswith('bearer'):
        logger.info(f'No authentication provided')
        abort(403, 'Must include an Authorization header with Bearer token')

    try:
        token = auth.split('Bearer ')[-1]
        decoded = jwt.decode(token, verify=False)
        name = decoded['context']['application']['name']
        url = decoded['context']['application']['redirectUri']
        status = decoded['context']['application']['status']
    except (KeyError, jwt.exceptions.DecodeError) as err:
        logger.info(f'Invalid JWT provided')
        abort(403, 'Invalid JWT provided')

    allowed = True

    # Check if the jwt redirect matches the url we have on hand
    domain = urlparse(url).netloc
    if domain != urlparse(current_app.config['COORDINATOR_URL']).netloc:
        logger.error(f'jwt provided with wrong redirect url: {url}')
        allowed = False

    if name != 'release-coordinator':
        logger.error(f'jwt provided with wrong app name: {name}')
        allowed = False

    if status != 'Approved':
        logger.error(f'jwt provided for unapproved app: {name}, {status}')
        allowed = False

    if not allowed:
        abort(403, 'JWT does not contain proper permissions')

    # Verify with ego now that prechecks have passed
    resp = requests.get(f"{current_app.config['EGO_URL']}/oauth/token/verify",
                        headers={'token': token})

    if resp.status_code != 200 or resp.json() is not True:
        logger.error(f'Ego failed to verify jwt for app: {name}')
        abort(403, 'JWT does not contain proper permissions')
