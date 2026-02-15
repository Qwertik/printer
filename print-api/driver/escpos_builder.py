"""Converts validated print job payloads into ESC/POS byte sequences.

Consolidates all ESC/POS byte construction from the original print_server_win32.py.
Uses python-escpos Dummy printer for image and barcode rendering.
"""
import os
import io
import base64
import logging
from typing import Optional

from PIL import Image
from escpos.printer import Dummy
from jinja2 import Environment, FileSystemLoader

import config
from .renderer import render_text_to_image

logger = logging.getLogger(__name__)

# ESC/POS command constants
ESC_INIT = b"\x1B\x40"
ESC_CENTER = b"\x1B\x61\x01"
ESC_LEFT = b"\x1B\x61\x00"
ESC_RIGHT = b"\x1B\x61\x02"
ESC_BOLD_ON = b"\x1B\x45\x01"
ESC_BOLD_OFF = b"\x1B\x45\x00"
ESC_DOUBLE_SIZE = b"\x1B\x21\x30"
ESC_NORMAL_SIZE = b"\x1B\x21\x00"
GS_CUT = b"\x1D\x56\x00"

ALIGN_MAP = {"left": ESC_LEFT, "center": ESC_CENTER, "right": ESC_RIGHT}

# Jinja2 environment for receipt templates
_jinja_env: Optional[Environment] = None


def _get_jinja_env() -> Environment:
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=FileSystemLoader(config.TEMPLATE_DIR),
            autoescape=False,
        )
    return _jinja_env


def _image_to_escpos(img: Image.Image) -> bytes:
    """Convert a PIL Image to ESC/POS image bytes using Dummy printer."""
    dummy = Dummy()
    dummy.image(img)
    return dummy.output


def _build_header(header: str, font_style: str, font_size: int) -> bytes:
    """Build ESC/POS bytes for a header line."""
    if font_style in ('montserrat', 'kings'):
        img = render_text_to_image(
            header,
            font_style=font_style,
            bold=True,
            font_size=max(font_size, 32),
            align='center',
        )
        if img:
            commands = ESC_CENTER
            commands += _image_to_escpos(img)
            commands += b"\n\n"
            return commands

    # Default or fallback: use ESC/POS double-size text
    commands = ESC_CENTER
    commands += ESC_DOUBLE_SIZE
    commands += header.encode('utf-8') + b"\n\n"
    commands += ESC_NORMAL_SIZE
    return commands


def _build_image(image_b64: str) -> bytes:
    """Decode a base64 image and convert to ESC/POS."""
    try:
        image_data = base64.b64decode(image_b64)
        img = Image.open(io.BytesIO(image_data))

        max_width = 512
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        return _image_to_escpos(img) + b"\n"
    except Exception as e:
        logger.error("Image processing failed: %s", e)
        return b""


def _build_text(text: str, font_style: str, font_size: int, align: str, bold: bool) -> bytes:
    """Build ESC/POS bytes for body text."""
    if font_style in ('montserrat', 'kings'):
        img = render_text_to_image(
            text,
            font_style=font_style,
            bold=bold,
            font_size=font_size,
            align=align,
        )
        if img:
            return _image_to_escpos(img) + b"\n"

    # Default: plain UTF-8 text
    return text.encode('utf-8') + b"\n"


def _build_qr(qr_data: str) -> bytes:
    """Build ESC/POS bytes for a QR code using Dummy printer."""
    dummy = Dummy()
    dummy.set(align='center')
    dummy.qr(qr_data, size=6)
    return dummy.output + b"\n"


def _build_barcode(barcode: dict) -> bytes:
    """Build ESC/POS bytes for a barcode using Dummy printer."""
    dummy = Dummy()
    dummy.set(align='center')
    dummy.barcode(barcode['data'], barcode['type'], height=50, width=2)
    return dummy.output + b"\n"


def build_escpos_commands(payload: dict) -> bytes:
    """Convert a validated print job payload into an ESC/POS byte sequence."""
    commands = ESC_INIT

    font_style = payload.get('font_style', 'default')
    align = payload.get('align', 'left')
    font_size = payload.get('font_size', 24)
    bold = payload.get('bold', False)

    # Template rendering: if a template is specified, render it to text
    if payload.get('template'):
        try:
            env = _get_jinja_env()
            template = env.get_template(payload['template'] + '.j2')
            rendered = template.render(**(payload.get('template_data') or {}))
            payload = dict(payload)  # copy to avoid mutating original
            payload['text'] = rendered
        except Exception as e:
            logger.error("Template rendering failed: %s", e)

    # Header
    if payload.get('header'):
        commands += _build_header(payload['header'], font_style, font_size)

    # Image
    if payload.get('image'):
        commands += _build_image(payload['image'])

    # Alignment
    commands += ALIGN_MAP.get(align, ESC_LEFT)

    # Bold
    if bold:
        commands += ESC_BOLD_ON

    # Main text
    if payload.get('text'):
        commands += _build_text(payload['text'], font_style, font_size, align, bold)

    # Reset bold
    if bold:
        commands += ESC_BOLD_OFF

    # QR code
    if payload.get('qr_code'):
        commands += _build_qr(payload['qr_code'])

    # Barcode
    if payload.get('barcode'):
        commands += _build_barcode(payload['barcode'])

    # Feed and cut
    commands += b"\n\n\n"
    if payload.get('cut', True):
        commands += GS_CUT

    return commands
