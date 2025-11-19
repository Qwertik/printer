import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Printer Configuration
PRINTER_NAME = os.getenv('PRINTER_NAME', 'Generic / Text Only')

# Server Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

# Logging Configuration
LOG_FILE = os.getenv('LOG_FILE', 'print_server.log')
