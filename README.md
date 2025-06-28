
# Ansible Flask REST API (VPN Automation Hub)

This is a Flask-based REST API for automating VPN client lifecycle operations using Ansible.

## 🔐 Authentication

All routes except `/health` require a valid **Google Identity Token** (JWT) passed in the `Authorization` header:

```
Authorization: Bearer <your_token>
```

Set `API_AUDIENCE` in `.env` to match your Google OAuth client ID.

---

## 🔧 Endpoints

### ▶️ POST `/create`

Create and upload VPN client configuration.

#### Request
```json
{
  "client_names": ["client1", "client2"]
}
```

#### Response
- `stdout`: Ansible stdout log
- `stderr`: Ansible stderr log
- `rc`: Return code

---

### 🔁 POST `/update`

Update and reinstall configuration for clients.

#### Request
```json
{
  "client_names": ["client1"]
}
```

#### Response
Same as `/create`.

---

### ❌ POST `/delete`

Delete VPN clients and clean their configuration.

#### Request
```json
{
  "client_names": ["client1"]
}
```

#### Response
Same as above.

---

### 🏭 POST `/factory_pull`

Trigger client archive generation for factory provisioning.

#### Request
```json
{
  "client_name": "client1"
}
```

#### Response
- A `.tar.gz` archive with the OpenVPN client config.

---

### ❤️ GET `/health`

Returns uptime and status.

#### Response
```json
{
  "status": "ok",
  "uptime": 123.45
}
```

---

## ⚙️ Environment Configuration (`.env`)

```env
API_AUDIENCE=your-google-client-id.apps.googleusercontent.com
ANSIBLE_BIN=/usr/bin/ansible-playbook
ANSIBLE_PLAYBOOK_PATH=/home/koffcheg/ansible-hub/playbooks
ANSIBLE_CWD=/home/koffcheg/ansible-hub
FACTORY_OUTPUT_DIR=/home/koffcheg/factory-output
```

---

## 🛡️ Deployment Notes

- Gunicorn is launched via systemd.
- Only port 5000 should be open internally (use GCP firewall).
- TLS is not configured here — expected to be used behind dashboard or reverse proxy.
- Logs and archives are local unless offloaded externally.

---

## 📦 Example `curl` Command

```bash
curl -X POST http://your-server-ip:5000/create \
  -H "Authorization: Bearer <your_google_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"client_names": ["client1"]}'
```

curl -X POST http://10.142.0.8:5000/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"client_names": ["client88"]}'