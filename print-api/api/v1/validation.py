import re
import base64

ALLOWED_ALIGNS = {"left", "center", "right"}
ALLOWED_FONTS = {"default", "montserrat", "kings"}
ALLOWED_BARCODE_TYPES = {"CODE39", "CODE128", "EAN13", "EAN8", "UPC-A"}
MAX_TEXT_LENGTH = 4096

# Matches control characters 0x00-0x1F except newline (0x0A)
_CONTROL_CHARS = re.compile(r'[\x00-\x09\x0b-\x1f]')


def sanitize_text(text: str) -> str:
    """Strip ESC/POS-injectable control characters, keeping newlines."""
    return _CONTROL_CHARS.sub('', text)


def validate_print_request(data: dict) -> tuple:
    """Validate and sanitize a structured print request.

    Returns (cleaned_data, errors). If errors is non-empty, the request is invalid.
    """
    errors = []
    cleaned = {}

    # At least one content source required
    if not data.get('text') and not data.get('template') and not data.get('image'):
        errors.append("At least one of 'text', 'template', or 'image' is required")

    # Text
    if data.get('text'):
        text = str(data['text'])
        if len(text) > MAX_TEXT_LENGTH:
            errors.append(f"Text exceeds {MAX_TEXT_LENGTH} characters")
        else:
            cleaned['text'] = sanitize_text(text)

    # Header
    if data.get('header'):
        header = str(data['header'])
        if len(header) > 256:
            errors.append("Header exceeds 256 characters")
        else:
            cleaned['header'] = sanitize_text(header)

    # Alignment
    align = data.get('align', 'left')
    if align not in ALLOWED_ALIGNS:
        errors.append(f"Invalid align '{align}', must be one of {ALLOWED_ALIGNS}")
    else:
        cleaned['align'] = align

    # Bold
    cleaned['bold'] = bool(data.get('bold', False))

    # Font style
    font_style = data.get('font_style', 'default')
    if font_style not in ALLOWED_FONTS:
        errors.append(f"Invalid font_style '{font_style}', must be one of {ALLOWED_FONTS}")
    else:
        cleaned['font_style'] = font_style

    # Font size
    font_size = data.get('font_size', 24)
    try:
        font_size = int(font_size)
        if not 12 <= font_size <= 72:
            errors.append("font_size must be between 12 and 72")
        else:
            cleaned['font_size'] = font_size
    except (ValueError, TypeError):
        errors.append("font_size must be an integer")

    # Image (base64)
    if data.get('image'):
        try:
            base64.b64decode(data['image'], validate=True)
            cleaned['image'] = data['image']
        except Exception:
            errors.append("Invalid base64 image data")

    # QR code
    if data.get('qr_code'):
        qr = str(data['qr_code'])
        if len(qr) > 2048:
            errors.append("QR code data exceeds 2048 characters")
        else:
            cleaned['qr_code'] = qr

    # Barcode
    if data.get('barcode'):
        bc = data['barcode']
        if not isinstance(bc, dict):
            errors.append("barcode must be an object with 'data' and 'type' fields")
        else:
            bc_data = bc.get('data', '')
            bc_type = bc.get('type', 'CODE39')
            if not bc_data:
                errors.append("barcode.data is required")
            if bc_type not in ALLOWED_BARCODE_TYPES:
                errors.append(f"Invalid barcode type '{bc_type}', must be one of {ALLOWED_BARCODE_TYPES}")
            else:
                cleaned['barcode'] = {'data': str(bc_data), 'type': bc_type}

    # Cut
    cleaned['cut'] = bool(data.get('cut', True))

    # Template
    if data.get('template'):
        cleaned['template'] = str(data['template'])
        if data.get('template_data') and isinstance(data['template_data'], dict):
            cleaned['template_data'] = data['template_data']

    return cleaned, errors


def validate_raw_request(data: dict) -> tuple:
    """Validate a raw ESC/POS print request.

    Returns (decoded_bytes, errors).
    """
    errors = []
    raw_bytes = b''

    if not data.get('data'):
        errors.append("'data' field with base64-encoded ESC/POS bytes is required")
    else:
        try:
            raw_bytes = base64.b64decode(data['data'], validate=True)
        except Exception:
            errors.append("Invalid base64 data")

    return raw_bytes, errors
