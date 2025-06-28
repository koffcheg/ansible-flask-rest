
# Ansible Flask REST API (VPN Automation Hub)

A minimal REST API for managing OpenVPN clients using Ansible playbooks.

---

## 🔐 Authentication

All API routes (except `/health`) require a valid **Google Identity Token (JWT)** in the `Authorization` header:

```
Authorization: Bearer <your_token>
```

Set `API_AUDIENCE` in `.env` to match your Google OAuth Client ID.

---

## 🔧 Endpoints Overview

### ▶️ POST `/create`
Creates and uploads VPN client configurations.
```json
{ "client_names": ["client1"] }
```

### 🔁 POST `/update`
Updates existing VPN client configuration.
```json
{ "client_names": ["client1"] }
```

### ❌ POST `/delete`
Deletes VPN client config and GCP secrets.
```json
{ "client_names": ["client1"] }
```

### 🏭 POST `/factory_pull`
Generates `.tar.gz` archive for USB provisioning.
```json
{ "client_name": "client1" }
```

### ❤️ GET `/health`
Basic health check:
```json
{ "status": "ok", "uptime": 123.45 }
```

---

## 📦 Example `curl` Request

```bash
curl -X POST http://<host>:5000/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"client_names": ["client1"]}'
```

---

## ⚙️ Quick Setup Notes

- Ansible playbooks live in `/home/koffcheg/ansible-hub/playbooks`
- Systemd `gunicorn` service must:
  - Set full `PATH` including `gcloud` location
  - Set `PrivateTmp=false`
  - NOT set `NoNewPrivileges=true` (or use APT `gcloud`)

---

## 🌱 .env Required Variables

```env
API_AUDIENCE=your-google-client-id.apps.googleusercontent.com
ANSIBLE_BIN=/usr/bin/ansible-playbook
ANSIBLE_PLAYBOOK_PATH=/home/koffcheg/ansible-hub/playbooks
ANSIBLE_CWD=/home/koffcheg/ansible-hub
FACTORY_OUTPUT_DIR=/home/koffcheg/factory-output
```

---

## ✅ Status

✔️ API-ready for VPN automation  
✔️ Google JWT authenticated  
✔️ Safe to call via curl or clients
