import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ANSIBLE_PLAYBOOK_PATH = os.getenv("ANSIBLE_PLAYBOOK_PATH")
    ANSIBLE_BIN = os.getenv("ANSIBLE_BIN")
    ANSIBLE_CWD= os.getenv('ANSIBLE_CWD')
    FACTORY_OUTPUT_DIR = os.getenv("FACTORY_OUTPUT_DIR")
    API_AUDIENCE = os.getenv("API_AUDIENCE")