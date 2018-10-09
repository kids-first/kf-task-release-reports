import decimal
from flask import Flask, Blueprint, current_app, jsonify, request, abort, json
from werkzeug.exceptions import HTTPException
from . import tasks


class DynamoJSON(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.json_encoder = DynamoJSON

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
ROUTES = {
    'get_status': tasks.get_status,
    'initialize': tasks.initialize,
    'start': tasks.start
}


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
    action, task_id, release_id = validate_action(request.get_json(force=True))
    # Call into action
    return ROUTES[action](task_id, release_id)


def validate_action(body):
    if not body:
        abort(400, 'No body recieved in request')

    if ('action' not in body or
        'task_id' not in body or
        'release_id' not in body):
        abort(400, "Request body must include 'action', 'task_id', " +
              "and 'release_id' fields")

    action = body['action']
    task_id = body['task_id']
    release_id = body['release_id']

    if action not in ALLOWED_ACTIONS:
        abort(400, f"'{action}' is not a known action, "+
              'must be one of {",".join(ALLOWED_ACTIONS)}')

    validate_kf_id(task_id, 'TA')
    validate_kf_id(release_id, 'RE')

    return action, task_id, release_id


def validate_kf_id(kf_id, prefix='TA'):
    """ Abort if the kf_id does not have the right kf_id format """
    if len(kf_id) != 11 or kf_id[:3] != prefix+'_':
        abort(400, f"'{kf_id}' is not a valid kf_id")
