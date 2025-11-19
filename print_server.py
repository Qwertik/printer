from flask import Flask, request, jsonify
from escpos.printer import Win32Raw
import logging
from datetime import datetime
import config

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_printer():
    """Initialize printer connection"""
    try:
        return Win32Raw(config.PRINTER_NAME)
    except Exception as e:
        logging.error(f"Failed to connect to printer: {e}")
        raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        printer = get_printer()
        return jsonify({
            "status": "healthy",
            "printer": config.PRINTER_NAME,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503

@app.route('/print', methods=['POST'])
def print_receipt():
    """
    Main print endpoint
    Accepts JSON: {
        "text": "Receipt content",
        "header": "Optional header text",
        "bold": true/false,
        "align": "left/center/right",
        "cut": true/false,
        "qr_code": "Optional QR data",
        "barcode": {"data": "123456", "type": "EAN13"}
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        logging.info(f"Print job received: {data}")
        
        # Initialize printer
        printer = get_printer()
        
        # Initialize printer (important!)
        printer.hw("init")
        
        # Print header if provided
        if data.get('header'):
            printer.set(align='center', font='b', width=2, height=2)
            printer.text(data['header'] + '\n')
            printer.text('\n')
        
        # Set alignment
        align_map = {'left': 'left', 'center': 'center', 'right': 'right'}
        alignment = align_map.get(data.get('align', 'left'), 'left')
        printer.set(align=alignment)
        
        # Print main text
        if data.get('text'):
            if data.get('bold'):
                printer.set(font='b')
            printer.text(data['text'] + '\n')
        
        # Print QR code if provided
        if data.get('qr_code'):
            printer.set(align='center')
            printer.qr(data['qr_code'], size=6)
            printer.text('\n')
        
        # Print barcode if provided
        if data.get('barcode'):
            barcode_data = data['barcode']
            printer.set(align='center')
            printer.barcode(
                barcode_data.get('data', ''),
                barcode_data.get('type', 'CODE39'),
                height=50,
                width=2
            )
            printer.text('\n')
        
        # Cut paper if requested (default: true)
        if data.get('cut', True):
            printer.cut()
        
        logging.info("Print job completed successfully")
        
        return jsonify({
            "status": "success",
            "message": "Print job completed",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Print job failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/print/simple', methods=['POST'])
def print_simple():
    """
    Simplified endpoint that just takes plain text
    Accepts JSON: {"text": "Your text here"}
    """
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({"status": "error", "message": "No text provided"}), 400
        
        logging.info(f"Simple print job: {text[:50]}...")
        
        printer = get_printer()
        printer.text(text + '\n')
        printer.cut()
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logging.error(f"Simple print failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/test', methods=['GET'])
def test_print():
    """Test endpoint that prints a sample receipt"""
    try:
        printer = get_printer()
        
        printer.hw("init")
        printer.set(align='center', font='b', width=2, height=2)
        printer.text('TEST PRINT\n')
        printer.text('\n')
        printer.set(align='left', font='a', width=1, height=1)
        printer.text(f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        printer.text(f'Printer: {config.PRINTER_NAME}\n')
        printer.text('Server: Windows Flask\n')
        printer.text('Status: OK\n')
        printer.text('\n')
        printer.cut()
        
        logging.info("Test print completed")
        return jsonify({"status": "success", "message": "Test print sent"}), 200
        
    except Exception as e:
        logging.error(f"Test print failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print(f"Starting print server for printer: {config.PRINTER_NAME}")
    print(f"Server will run on http://{config.HOST}:{config.PORT}")
    print(f"Test endpoint: http://{config.HOST}:{config.PORT}/test")
    
    # Run on all interfaces so n8n can reach it
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)