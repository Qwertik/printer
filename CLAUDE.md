# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview
This is a Flask-based thermal printer server that exposes REST API endpoints for printing receipts to a POS80 USB thermal printer on Windows. It uses the python-escpos library to communicate with Win32 raw printer drivers.

## Architecture
- **print_server.py**: Main Flask application exposing print endpoints
  - `/health` - Health check endpoint to verify printer connectivity
  - `/print` - Full-featured print endpoint supporting headers, formatting, QR codes, and barcodes
  - `/print/simple` - Simplified endpoint for plain text printing
  - `/test` - Test print endpoint that outputs a sample receipt

## Development Commands

### Install Dependencies
```bash
pip install flask python-escpos[win32]
```

### Run Server
```bash
python print_server.py
```
The server runs on `http://localhost:5000` by default.

### Test Printer Connection
```bash
curl http://localhost:5000/health
```

### Send Test Print
```bash
curl http://localhost:5000/test
```

## Important Configuration
- **Printer Name**: Currently configured to use "Generic / Text Only" driver
- **Working Server**: Use `print_server_win32.py` (uses win32print directly)
- **Note**: ESC/POS commands may not work with Generic driver, plain text printing works
- **Logging**: Logs are written to both console and `print_server.log` file
- **Server Host**: Runs on `0.0.0.0` to allow external connections (e.g., from n8n)

## API Usage Examples

### Simple Text Print
```json
POST /print/simple
{
  "text": "Hello World"
}
```

### Full Featured Print
```json
POST /print
{
  "header": "RECEIPT",
  "text": "Item 1: $10.00\nItem 2: $5.00\nTotal: $15.00",
  "bold": false,
  "align": "left",
  "qr_code": "https://example.com",
  "barcode": {"data": "123456789", "type": "CODE39"},
  "cut": true
}
```

## Key Dependencies
- Flask: Web framework for REST API
- python-escpos: Thermal printer communication library
- Win32Raw: Windows-specific printer driver interface