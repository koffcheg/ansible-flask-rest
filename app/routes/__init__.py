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

START_TIME = time.time()


def register_routes(app):
    log = logging.getLogger("api")
    log.setLevel(logging.INFO)

    API_AUDIENCE = app.config.get("API_AUDIENCE")

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #
    def get_factory_token():
        """Return factory token from file or env *every call*."""
        token_path = "/home/koffcheg/.ansible-hub/factory_token"
        if os.path.exists(token_path):
            try:
                with open(token_path, "r") as f:
                    return f.read().strip()
            except Exception as exc:
                log.error(f"Cannot read factory token file: {exc}")
        return os.getenv("FACTORY_TOKEN", "").strip()

    def verify_google_identity_token(token: str):
        try:
            return id_token.verify_oauth2_token(token, Request(), API_AUDIENCE)
        except Exception as exc:
            log.error(f"JWT validation failed: {exc}")
            return None

    # ------------------------------------------------------------------ #
    # Auth decorator                                                     #
    # ------------------------------------------------------------------ #
    def require_auth(fn):
        @wraps(fn)
        def _wrapped(*args, **kwargs):
            raw = request.headers.get("Authorization", "")
            if not raw.startswith("Bearer "):
                return jsonify(error="Missing Bearer token"), 401

            token = raw.split(" ", 1)[1].strip()
            factory_token = get_factory_token()

            # Factory bypass only for /factory_pull
            if request.path == "/factory_pull" and token == factory_token:
                return fn(*args, **kwargs)

            # Otherwise treat as Google JWT
            claims = verify_google_identity_token(token)
            if not claims:
                return jsonify(error="Unauthorized"), 401

            request.view_args = request.view_args or {}
            request.view_args["claims"] = claims
            return fn(*args, **kwargs)

        return _wrapped

    # ------------------------------------------------------------------ #
    # Exec Ansible                                                       #
    # ------------------------------------------------------------------ #
    def run_playbook(playbook_name: str, **extra_vars):
        playbook_path = os.path.join(app.config["ANSIBLE_PLAYBOOK_PATH"], playbook_name)
        cmd = [
            app.config["ANSIBLE_BIN"],
            playbook_path,
            "-e",
            json.dumps(extra_vars),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=app.config["ANSIBLE_CWD"]
        )
        log.info("Executed %s rc=%s", playbook_name, result.returncode)
        return result

    def _ansible_endpoint(playbook: str):
        body = request.get_json(silent=True) or {}
        if "client_names" in body and not isinstance(body["client_names"], list):
            raise BadRequest("client_names must be an array")

        result = run_playbook(playbook, **body)
        status = 200 if result.returncode == 0 else 500
        return (
            jsonify(stdout=result.stdout, stderr=result.stderr, rc=result.returncode),
            status,
        )

    # ------------------------------------------------------------------ #
    # Routes                                                             #
    # ------------------------------------------------------------------ #
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
            return (
                jsonify(stdout=result.stdout, stderr=result.stderr, rc=result.returncode),
                500,
            )

        archive_path = f"/tmp/client-configs/{client_name}.tar.gz"
        if not os.path.exists(archive_path):
            log.error(f"Expected archive not found: {archive_path}")
            return jsonify(error="Internal error: archive not found"), 500

        return send_file(archive_path, as_attachment=True)

    @app.route("/health")
    def health():
        return jsonify(status="ok", uptime=round(time.time() - START_TIME, 2)), 200
