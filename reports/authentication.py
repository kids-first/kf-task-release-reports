import json
import jwt
import logging
import requests
from urllib.parse import urlparse
from flask import current_app, request, abort


def _get_new_key():
    resp = requests.get(
        current_app.config["AUTH0_JWKS"], timeout=current_app.config["TIMEOUT"]
    )
    return resp.json()["keys"][0]


def authenticate_coordinator():
    """ Verify a jwt by performing token checks and validating with ego """
    logger = current_app.logger

    auth = request.headers.get("Authorization")
    if auth is None or not auth.startswith("Bearer "):
        logger.info(f"No authentication provided")
        abort(403, "Must include an Authorization header with Bearer token")
    token = auth.replace("Bearer ", "")

    # Get the public key from Auth0
    public_key = None
    try:
        key = _get_new_key()
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
    except requests.exceptions.RequestException as err:
        logger.error(f"Problem fetching key from Auth0: {err}")
        abort(500, "Problem authenticating")
    except KeyError:
        logger.error(f"Unexpected response from Auth0")
        abort(500, "Problem authenticating")

    # Verify the token
    try:
        token = jwt.decode(
            token,
            public_key,
            algorithms="RS256",
            audience=current_app.config["AUTH0_AUD"],
        )
    except jwt.exceptions.DecodeError as err:
        logger.error(f"Problem authenticating request from Auth0: {err}")
        abort(403, "Invalid JWT provided")
    except jwt.exceptions.InvalidTokenError as err:
        logger.error(f"Token provided is not valid for Auth0: {err}")
        abort(403, "Invalid JWT provided")

    if not token.get("gty") == "client-credentials":
        logger.error(f"Non-service token tried to access reports")
        abort(403, "Only service tokens are allowed")

    logger.info(
        f"Verified request from the Release Coordinator for {token['sub']}"
    )
