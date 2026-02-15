# CLAUDE.md

## Overview
Raspberry Pi thermal print server — a Flask REST API that accepts structured JSON and generates ESC/POS commands server-side. Targets a VCP-8370 (Zjiang ZJ-8370) 80mm thermal printer over USB.

## Architecture
Five layers: Network (Tailscale) → HTTP API (Flask) → Job Queue (threading.Queue) → ESC/POS Driver (python-escpos) → USB Hardware (/dev/thermalprinter).

- `server.py` — Entry point, app factory, wires queue + driver
- `api/v1/routes.py` — All endpoints (print, print/raw, status)
- `api/v1/auth.py` — Bearer token auth decorators
- `api/v1/validation.py` — Input sanitization, schema validation
- `print_queue/manager.py` — FIFO job queue with single consumer thread
- `print_queue/job.py` — PrintJob dataclass, JobState enum
- `driver/printer.py` — Printer handle lifecycle, reconnection, platform backends
- `driver/escpos_builder.py` — JSON → ESC/POS byte conversion
- `driver/renderer.py` — Text-to-image rendering for custom fonts

## Development Commands

### Install
```bash
pip install -r requirements.txt
```

### Run (dev mode with dummy printer)
```bash
# Copy and edit .env
cp .env.example .env
# Set PRINTER_BACKEND=dummy in .env for testing without hardware
python server.py
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8080/health

# Print (no auth in dev when API_TOKEN is empty)
curl -X POST http://localhost:8080/api/v1/print \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World", "cut": true}'

# Check job status
curl http://localhost:8080/api/v1/status?job_id=<id>

# With auth (when API_TOKEN is set)
curl -X POST http://localhost:8080/api/v1/print \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "header": "TEST", "align": "center"}'
```

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | None | Service health + printer status |
| `/api/v1/print` | POST | Bearer | Structured JSON print job → 202 |
| `/api/v1/print/raw` | POST | Admin | Base64 ESC/POS bytes → 202 |
| `/api/v1/status` | GET | Bearer | Printer state, optional ?job_id= |

## Deployment (Raspberry Pi)
```bash
cd print-api
sudo bash deploy/install.sh
# Edit /opt/print-api/.env
# Edit /etc/udev/rules.d/99-thermal-printer.rules (USB VID/PID)
sudo systemctl start print-api
```

## Key Configuration (.env)
- `PRINTER_DEVICE` — Linux device path (default: /dev/thermalprinter)
- `PRINTER_BACKEND` — file | win32raw | dummy
- `API_TOKEN` — Bearer auth token (empty = auth disabled)
- `QUEUE_MAX_DEPTH` — Max pending jobs before 429 (default: 20)
- `JOB_TIMEOUT` — Seconds before a stuck job is killed (default: 30)
