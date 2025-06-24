from flask import request, jsonify, current_app
from functools import wraps
import subprocess
import os

def register_routes(app):

    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token != current_app.config['API_AUTH_TOKEN']:
                return jsonify({"error": "Unauthorized"}), 401
            return f(*args, **kwargs)
        return decorated

    def run_playbook(playbook_name, extra_vars: dict):
        playbook_path = os.path.join(current_app.config['ANSIBLE_PLAYBOOK_PATH'], playbook_name)
        ansible_cwd = current_app.config['ANSIBLE_CWD']
        # Convert extra_vars dict into proper CLI args string for Ansible
        extra_vars_string = " ".join([
            f"{key}={value if isinstance(value, str) else repr(value)}"
            for key, value in extra_vars.items()
        ])

        cmd = [
            current_app.config['ANSIBLE_BIN'],
            playbook_path,
            "-e", extra_vars_string
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=ansible_cwd)
        return result

    @app.route('/create', methods=['POST'])
    @require_auth
    def create():
        client_names = request.json.get('client_names')
        if not client_names or not isinstance(client_names, list):
            return jsonify({"error": "client_names must be a non-empty list"}), 400

        result = run_playbook('create_and_upload.yaml', {"client_names": client_names})
        return jsonify({"stdout": result.stdout, "stderr": result.stderr, "rc": result.returncode})

    @app.route('/update', methods=['POST'])
    @require_auth
    def update():
        client_names = request.json.get('client_names')
        if not client_names or not isinstance(client_names, list):
            return jsonify({"error": "client_names must be a non-empty list"}), 400

        result = run_playbook('update_and_install.yaml', {"client_names": client_names})
        return jsonify({"stdout": result.stdout, "stderr": result.stderr, "rc": result.returncode})

    @app.route('/delete', methods=['POST'])
    @require_auth
    def delete():
        client_names = request.json.get('client_names')
        if not client_names or not isinstance(client_names, list):
            return jsonify({"error": "client_names must be a non-empty list"}), 400

        result = run_playbook('delete_clients.yaml', {"client_names": client_names})
        return jsonify({"stdout": result.stdout, "stderr": result.stderr, "rc": result.returncode})

    @app.route('/factory_pull', methods=['POST'])
    @require_auth
    def factory_pull():
        client_name = request.json.get('client_name')
        if not client_name:
            return jsonify({"error": "client_name is required"}), 400

        result = run_playbook('factory_pull.yaml', {"client_name": client_name})
        return jsonify({"stdout": result.stdout, "stderr": result.stderr, "rc": result.returncode})