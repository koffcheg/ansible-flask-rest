from flask import request, jsonify, current_app, send_file
from functools import wraps
import google.auth.transport.requests
import google.oauth2.id_token
import subprocess
import os
import json

def register_routes(app):

    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid Authorization header"}), 401

            token = auth_header.replace("Bearer ", "")
            request_adapter = google.auth.transport.requests.Request()

            try:
                # Verify the token with GCP Identity Platform
                id_info = google.oauth2.id_token.verify_oauth2_token(token, request_adapter)
            
                # Optional: enforce specific audience or email
                # if id_info['aud'] != YOUR_EXPECTED_AUDIENCE:
                #     return jsonify({"error": "Invalid audience"}), 403

            except Exception as e:
                return jsonify({"error": "Invalid token", "details": str(e)}), 401

            return f(*args, **kwargs)
        return decorated

    def run_playbook(playbook_name, **extra_vars):
        playbook_path = os.path.join(current_app.config['ANSIBLE_PLAYBOOK_PATH'], playbook_name)
        cmd = [
            current_app.config['ANSIBLE_BIN'],
            playbook_path,
            "-e", json.dumps(extra_vars)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=current_app.config['ANSIBLE_CWD'])
        return result

    @app.route('/create', methods=['POST'])
    @require_auth
    def create():
        client_names = request.json.get('client_names')
        result = run_playbook('create_and_upload.yaml', client_names=client_names)
        return jsonify({"stdout": result.stdout, "stderr": result.stderr, "rc": result.returncode})

    @app.route('/update', methods=['POST'])
    @require_auth
    def update():
        client_names = request.json.get('client_names')
        result = run_playbook('update_and_install.yaml', client_names=client_names)
        return jsonify({"stdout": result.stdout, "stderr": result.stderr, "rc": result.returncode})

    @app.route('/delete', methods=['POST'])
    @require_auth
    def delete():
        client_names = request.json.get('client_names')
        result = run_playbook('delete_clients.yaml', client_names=client_names)
        return jsonify({"stdout": result.stdout, "stderr": result.stderr, "rc": result.returncode})

    @app.route('/factory_pull', methods=['POST'])
    @require_auth
    def factory_pull():
        client_name = request.json.get('client_name')
        result = run_playbook('factory_pull.yaml', client_name=client_name)

        if result.returncode != 0:
            return jsonify({
                "stdout": result.stdout,
                "stderr": result.stderr,
                "rc": result.returncode
            }), 500

        # Archive the folder
        output_dir = os.path.expanduser(
            f"{current_app.config['FACTORY_OUTPUT_DIR']}/{client_name}"
        )
        archive_path = os.path.join(current_app.config['FACTORY_OUTPUT_DIR'], f"{client_name}.tar.gz")
        subprocess.run(["tar", "czf", archive_path, "-C", output_dir, "."], check=True)

        return send_file(archive_path, as_attachment=True)