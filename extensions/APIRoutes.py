from hashlib import sha256
from functools import wraps
from flask import Blueprint, jsonify, request
from utils.SanitizeText import sanitize_helix_id, sanitize_discord_id

api_blueprint = Blueprint('api', __name__)

def base_required(f, api_key, *args, **kwargs):
    request_key = request.headers.get("X-API-KEY")
    if not request_key:
        return jsonify({"error": "API key missing"}), 401
    hashed_request_key = sha256(request_key.encode("utf-8")).hexdigest()
    if hashed_request_key != api_key:
        return jsonify({"error": "Invalid API key"}), 401
    return f(*args, **kwargs)


def setup(app):
    def code_api_key_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return base_required(f, app.code_api_key, *args, **kwargs)

        return decorated_function

    def api_key_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return base_required(f, app.api_key, *args, **kwargs)

        return decorated_function

    @api_blueprint.get('/get-code/<string:helix_id>')
    @code_api_key_required
    def get_code(helix_id):
        try:
            helix_id = sanitize_helix_id(helix_id)
            if not app.helix_utils.validate_helix_id(helix_id):
                return jsonify({"error": "Invalid Helix ID"}), 400
            code = app.dbutils.generate_helix_code(helix_id, app.get_sender_ip())
            if not code:
                return jsonify({"error": "Could not generate code"}), 500
            return jsonify({"helix_id": helix_id, "code": code}), 200
        except Exception as e:
            return jsonify({"error": f"Could not generate code: {e}"}), 500

    @api_blueprint.get('/users')
    @api_key_required
    def get_users():
        try:
            r_data = request.json if request.is_json else {}
            requested_users = r_data.get("users", [])
            if type(requested_users) is not list:
                return jsonify({"error": "Invalid users list"}), 400
            sanitized_ids = [sanitize_discord_id(str(uid)) for uid in requested_users]
            all_users = app.dbutils.get_users_by_discord_ids(sanitized_ids, to_dict=True)
            return jsonify({"users": all_users}), 200
        except Exception as e:
            return jsonify({"error": f"Could not retrieve users: {e}"}), 500

    app.register_blueprint(api_blueprint, url_prefix='/api')
