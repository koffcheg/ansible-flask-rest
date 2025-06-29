import json
import os
import subprocess
import time
import logging
from functools import wraps
from flask import request, jsonify, send_file
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from werkzeug.exceptions import BadRequest

# Global timestamp for health check
START_TIME = time.time()

def register_routes(app):
    log = logging.getLogger("api")
    log.setLevel(logging.INFO)

    # Load factory token from file or env
    def get_factory_token():
        try:
            with open("/etc/ansible-hub/factory-token", "r") as f:
                return f.read().strip()
        except Exception:
            return os.getenv("FACTORY_TOKEN", "")

    FACTORY_TOKEN = get_factory_token()
    API_AUDIENCE = app.config.get("API_AUDIENCE")

    def verify_google_identity_token(token: str):
        try:
            claims = id_token.verify_oauth2_token(token, Request(), API_AUDIENCE)
            return claims
        except Exception as exc:
            log.error(f"JWT validation failed: {exc}")
            return None

    def require_auth(fn):
        @wraps(fn)
        def _wrapped(*args, **kwargs):
            raw = request.headers.get("Authorization", "")
            if not raw.startswith("Bearer "):
                return jsonify(error="Missing Bearer token"), 401

            token = raw.split(" ", 1)[1].strip()

            # Factory bypass only for /factory_pull
            if request.path == "/factory_pull" and token == FACTORY_TOKEN:
                return fn(*args, **kwargs)

            # Standard JWT verification
            claims = verify_google_identity_token(token)
            if not claims:
                return jsonify(error="Unauthorized"), 401

            request.view_args = request.view_args or {}
            request.view_args["claims"] = claims
            return fn(*args, **kwargs)

        return _wrapped

    def run_playbook(playbook_name: str, **extra_vars):
        playbook_path = os.path.join(app.config["ANSIBLE_PLAYBOOK_PATH"], playbook_name)
        cmd = [
            app.config["ANSIBLE_BIN"],
            playbook_path,
            "-e", json.dumps(extra_vars),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=app.config["ANSIBLE_CWD"]
        )
        log.info(f"Executed {playbook_name} rc={result.returncode}")
        return result

    def _ansible_endpoint(playbook: str):
        body = request.get_json(silent=True) or {}
        if "client_names" in body and not isinstance(body["client_names"], list):
            raise BadRequest("client_names must be an array")
        result = run_playbook(playbook, **body)
        return jsonify(stdout=result.stdout, stderr=result.stderr, rc=result.returncode), (
            200 if result.returncode == 0 else 500
        )

    @app.route("/create", methods=["POST"])
    @require_auth
    def create():
        return _ansible_endpoint("create_and_upload.yaml")

    @app.route("/update", methods=["POST"])
    @require_auth
    def update():
        return _ansible_endpoint("update_and_install.yaml")

    @app.route("/delete", methods=["POST"])
    @require_auth
    def delete():
        return _ansible_endpoint("delete_clients.yaml")

    @app.route("/factory_pull", methods=["POST"])
    @require_auth
    def factory_pull():
        body = request.get_json(silent=True) or {}
        client_name = body.get("client_name")
        if not client_name:
            raise BadRequest("client_name is required")

        result = run_playbook("factory_pull.yaml", client_name=client_name)
        if result.returncode != 0:
            return jsonify(stdout=result.stdout, stderr=result.stderr, rc=result.returncode), 500

        output_dir = os.path.expanduser(f"{app.config['FACTORY_OUTPUT_DIR']}/{client_name}")
        archive_path = f"{output_dir}.tar.gz"
        subprocess.run(["tar", "czf", archive_path, "-C", output_dir, "."], check=True)

        return send_file(archive_path, as_attachment=True)

    @app.route("/health")
    def health():
        return jsonify(status="ok", uptime=round(time.time() - START_TIME, 2)), 200
