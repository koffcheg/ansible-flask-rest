import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ANSIBLE_PLAYBOOK_PATH = os.getenv("ANSIBLE_PLAYBOOK_PATH")
    ANSIBLE_BIN = os.getenv("ANSIBLE_BIN")
    ANSIBLE_CWD= os.getenv('ANSIBLE_CWD')
    API_AUDIENCE = os.getenv("API_AUDIENCE")