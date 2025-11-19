from flask import Flask, request, jsonify
import win32print
import logging
from datetime import datetime
import config
import base64
import io
from PIL import Image, ImageDraw, ImageFont
from escpos.printer import Dummy
import textwrap

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

def send_raw_data(data):
    """Send raw data directly to printer"""
    try:
        printer = win32print.OpenPrinter(config.PRINTER_NAME)
        try:
            job = win32print.StartDocPrinter(printer, 1, ("Receipt", None, "RAW"))
            win32print.StartPagePrinter(printer)
            win32print.WritePrinter(printer, data)
            win32print.EndPagePrinter(printer)
            win32print.EndDocPrinter(printer)
            return True
        finally:
            win32print.ClosePrinter(printer)
    except Exception as e:
        logging.error(f"Print error: {e}")
        raise

def render_text_to_image(text, font_path, width=512, font_size=24, align='left'):
    """Render text to an image using the specified font and alignment"""
    try:
        # Load font
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            logging.warning(f"Could not load font {font_path}, falling back to default")
            font = ImageFont.load_default()

        # Create a dummy image to calculate text size
        dummy_img = Image.new('RGB', (width, 1000))
        draw = ImageDraw.Draw(dummy_img)
        
        # Wrap text
        lines = []
        # Improve char width estimation using a representative string
        avg_char_width = draw.textlength("The quick brown fox jumps over the lazy dog", font=font) / 43
        # Add a small buffer to be safe, but less aggressive than before
        chars_per_line = int(width / avg_char_width)
        
        for paragraph in text.split('\n'):
            lines.extend(textwrap.wrap(paragraph, width=chars_per_line))
            if not paragraph: # Preserve empty lines
                lines.append("")

        # Calculate total height
        line_height = int(font.size * 1.2)
        total_height = len(lines) * line_height + 20 # Add some padding
        
        # Create actual image
        img = Image.new('RGB', (width, total_height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw text
        y = 10
        for line in lines:
            line_width = draw.textlength(line, font=font)
            
            if align == 'center':
                x = (width - line_width) / 2
            elif align == 'right':
                x = width - line_width
            else:
                x = 0
                
            # Ensure x is not negative
            x = max(0, x)
            
            draw.text((x, y), line, font=font, fill='black')
            y += line_height
            
        return img
    except Exception as e:
        logging.error(f"Text rendering failed: {e}")
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check if printer exists
        printers = [printer[2] for printer in win32print.EnumPrinters(2)]
        if config.PRINTER_NAME in printers:
            return jsonify({
                "status": "healthy",
                "printer": config.PRINTER_NAME,
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "status": "unhealthy",
                "error": f"Printer {config.PRINTER_NAME} not found",
                "available_printers": printers,
                "timestamp": datetime.now().isoformat()
            }), 503
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
        "cut": true/false
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        logging.info(f"Print job received: {data}")
        
        # Build ESC/POS command sequence
        commands = b""
        
        # Initialize printer
        commands += b"\x1B\x40"
        
        # Print header if provided
        if data.get('header'):
            font_style = data.get('font_style', 'default')
            if font_style == 'montserrat':
                # Render header as image (Bold, larger size)
                # Header is always centered
                img = render_text_to_image(data['header'], 'fonts/Montserrat-Bold.ttf', font_size=32, align='center')
                if img:
                    dummy = Dummy()
                    dummy.set(align='center')
                    dummy.image(img)
                    commands += dummy.output
                    commands += b"\n\n"
            elif font_style == 'kings':
                # Render header as image (Kings font)
                img = render_text_to_image(data['header'], 'fonts/Kings-Regular.ttf', font_size=32, align='center')
                if img:
                    dummy = Dummy()
                    dummy.set(align='center')
                    dummy.image(img)
                    commands += dummy.output
                    commands += b"\n\n"
                else:
                    # Fallback
                    commands += b"\x1B\x61\x01"  # Center align
                    commands += b"\x1B\x21\x30"  # Double height and width
                    commands += data['header'].encode('utf-8') + b"\n\n"
                    commands += b"\x1B\x21\x00"  # Normal size
            else:
                commands += b"\x1B\x61\x01"  # Center align
                commands += b"\x1B\x21\x30"  # Double height and width
                commands += data['header'].encode('utf-8') + b"\n\n"
                commands += b"\x1B\x21\x00"  # Normal size

        # Handle Image if present
        if data.get('image'):
            try:
                # Decode base64 image
                image_data = base64.b64decode(data['image'])
                img = Image.open(io.BytesIO(image_data))
                
                # Resize if too wide (max 512 dots for standard 80mm)
                max_width = 512
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Generate ESC/POS commands for image using Dummy printer
                dummy = Dummy()
                dummy.image(img)
                commands += dummy.output
                commands += b"\n" # Add a newline after image
                
            except Exception as img_err:
                logging.error(f"Image processing failed: {img_err}")
                # Continue printing text even if image fails
        
        # Set alignment
        align = data.get('align', 'left')
        if align == 'center':
            commands += b"\x1B\x61\x01"
        elif align == 'right':
            commands += b"\x1B\x61\x02"
        else:
            commands += b"\x1B\x61\x00"
        
        # Set bold if requested
        if data.get('bold'):
            commands += b"\x1B\x45\x01"
        
        # Print main text
        if data.get('text'):
            font_style = data.get('font_style', 'default')
            if font_style == 'montserrat':
                # Render text as image
                font_path = 'fonts/Montserrat-Bold.ttf' if data.get('bold') else 'fonts/Montserrat-Regular.ttf'
                # Pass alignment and font size
                align = data.get('align', 'left')
                font_size = data.get('font_size', 24)
                img = render_text_to_image(data['text'], font_path, align=align, font_size=font_size)
                if img:
                    dummy = Dummy()
                    dummy.image(img)
                    commands += dummy.output
                    commands += b"\n"
                else:
                    # Fallback to normal text
                    commands += data['text'].encode('utf-8') + b"\n"
            elif font_style == 'kings':
                # Render text as image
                font_path = 'fonts/Kings-Regular.ttf'
                # Pass alignment and font size
                align = data.get('align', 'left')
                font_size = data.get('font_size', 24)
                img = render_text_to_image(data['text'], font_path, align=align, font_size=font_size)
                if img:
                    dummy = Dummy()
                    dummy.image(img)
                    commands += dummy.output
                    commands += b"\n"
                else:
                    # Fallback to normal text
                    commands += data['text'].encode('utf-8') + b"\n"
            else:
                # Normal text printing
                commands += data['text'].encode('utf-8') + b"\n"
        
        # Reset bold
        if data.get('bold'):
            commands += b"\x1B\x45\x00"
        
        # Feed lines
        commands += b"\n\n\n"
        
        # Cut paper if requested
        if data.get('cut', True):
            commands += b"\x1D\x56\x00"  # Full cut
        
        # Send to printer
        send_raw_data(commands)
        
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
        
        # Simple ESC/POS commands
        commands = b"\x1B\x40"  # Initialize
        commands += text.encode('utf-8') + b"\n\n\n"
        commands += b"\x1D\x56\x00"  # Cut
        
        send_raw_data(commands)
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logging.error(f"Simple print failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/test', methods=['GET'])
def test_print():
    """Test endpoint that prints a sample receipt"""
    try:
        # ESC/POS commands for test receipt
        commands = b""
        commands += b"\x1B\x40"  # Initialize
        commands += b"\x1B\x61\x01"  # Center
        commands += b"\x1B\x21\x30"  # Double size
        commands += b"TEST PRINT\n\n"
        commands += b"\x1B\x21\x00"  # Normal size
        commands += b"\x1B\x61\x00"  # Left align
        commands += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n".encode()
        commands += f"Printer: {config.PRINTER_NAME}\n".encode()
        commands += b"Server: Windows Flask\n"
        commands += b"Status: OK\n"
        commands += b"\n" + b"-" * 32 + b"\n"
        commands += b"If you see this,\n"
        commands += b"the printer is working!\n"
        commands += b"\n\n\n"
        commands += b"\x1D\x56\x00"  # Cut
        
        send_raw_data(commands)
        
        logging.info("Test print completed")
        return jsonify({"status": "success", "message": "Test print sent"}), 200
        
    except Exception as e:
        logging.error(f"Test print failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print(f"Starting print server for printer: {config.PRINTER_NAME}")
    print(f"Server will run on http://{config.HOST}:{config.PORT}")
    print(f"Test endpoint: http://{config.HOST}:{config.PORT}/test")
    
    # Run on all interfaces
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)