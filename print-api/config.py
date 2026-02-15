import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Platform detection
IS_LINUX = sys.platform.startswith('linux')
IS_WINDOWS = sys.platform == 'win32'

# Printer Configuration
if IS_LINUX:
    PRINTER_DEVICE = os.getenv('PRINTER_DEVICE', '/dev/thermalprinter')
    PRINTER_BACKEND = 'file'
else:
    PRINTER_DEVICE = os.getenv('PRINTER_NAME', 'Generic / Text Only')
    PRINTER_BACKEND = os.getenv('PRINTER_BACKEND', 'dummy')

# Server Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8080))
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

# Security
API_TOKEN = os.getenv('API_TOKEN', '')
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', '')

# Queue Configuration
QUEUE_MAX_DEPTH = int(os.getenv('QUEUE_MAX_DEPTH', 20))
JOB_TIMEOUT = float(os.getenv('JOB_TIMEOUT', 30.0))

# Rate Limiting
RATE_LIMIT = os.getenv('RATE_LIMIT', '10 per minute')
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 65536))

# Logging
LOG_FILE = os.getenv('LOG_FILE', '')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, 'fonts')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
