import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")
    ANSIBLE_PLAYBOOK_PATH = os.getenv("ANSIBLE_PLAYBOOK_PATH")
    ANSIBLE_BIN = os.getenv("ANSIBLE_BIN")