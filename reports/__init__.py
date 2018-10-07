from flask import Flask, Blueprint, current_app, jsonify, request, abort
from werkzeug.exceptions import HTTPException


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    @app.errorhandler(400)
    def json_error(error):
        description = 'error'
        code = 500
        if hasattr(error, 'description'):
            description = error.description
        if hasattr(error, 'code'):
            code = error.code
        return jsonify({'message': description}), code

    from werkzeug.exceptions import default_exceptions
    for ex in default_exceptions:
        app.register_error_handler(ex, json_error)

    app.register_blueprint(api)

    return app


api = Blueprint('api', __name__, url_prefix='')
ALLOWED_ACTIONS = ['get_status', 'initialize', 'start', 'publish', 'cancel']


@api.route("/status", methods=['GET'])
def status():
    return jsonify({
        'name': 'kf-task-release-reports',
        'version': '0.1.0'
    })


@api.route("/tasks", methods=['POST'])
def tasks():
    """
    RPC-like endpoint specified by the coordinator
    """
    action = validate_action(request.get_json(force=True))
    return jsonify({
        'status': 'ok'
    }), 200


def validate_action(body):
    if not body:
        abort(400, 'No body recieved in request')

    if 'action' not in body or 'task_id' not in body:
        abort(400, "Request body must include 'action' and 'task_id' fields")

    action = body['action']
    task_id = body['task_id']

    if action not in ALLOWED_ACTIONS:
        abort(400, f"'{action}' is not a known action, "+
              'must be one of {",".join(ALLOWED_ACTIONS)}')

    validate_task(task_id)

    return action


def validate_task(task_id):
    if len(task_id) != 11 or task_id[:3] != 'TA_':
        abort(400, f"'{task_id}' is not a valid kf_id")
