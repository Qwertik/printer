"""Text-to-image rendering for custom font printing.

Ported from printer/print_server_win32.py render_text_to_image().
Font objects are cached at module level to avoid repeated disk reads on Pi.
"""
import os
import logging
import textwrap
from typing import Optional, Dict

from PIL import Image, ImageDraw, ImageFont

import config

logger = logging.getLogger(__name__)

# Module-level font cache: {font_path_size: ImageFont}
_font_cache: Dict[str, ImageFont.FreeTypeFont] = {}

FONT_FILES = {
    'montserrat': {
        'regular': 'Montserrat-Regular.ttf',
        'bold': 'Montserrat-Bold.ttf',
    },
    'kings': {
        'regular': 'Kings-Regular.ttf',
        'bold': 'Kings-Regular.ttf',  # Kings has no bold variant
    },
}


def _get_font(font_style: str, bold: bool, font_size: int) -> ImageFont.FreeTypeFont:
    """Load a font, using the module-level cache."""
    variant = 'bold' if bold else 'regular'
    files = FONT_FILES.get(font_style, FONT_FILES['montserrat'])
    filename = files[variant]
    cache_key = f"{filename}:{font_size}"

    if cache_key not in _font_cache:
        font_path = os.path.join(config.FONT_DIR, filename)
        try:
            _font_cache[cache_key] = ImageFont.truetype(font_path, font_size)
        except IOError:
            logger.warning("Could not load font %s, falling back to default", font_path)
            _font_cache[cache_key] = ImageFont.load_default()

    return _font_cache[cache_key]


def render_text_to_image(
    text: str,
    font_style: str = 'montserrat',
    bold: bool = False,
    width: int = 512,
    font_size: int = 24,
    align: str = 'left',
) -> Optional[Image.Image]:
    """Render text to a PIL Image using the specified font and alignment.

    Returns None on failure.
    """
    try:
        font = _get_font(font_style, bold, font_size)

        # Create a dummy image to calculate text metrics
        dummy_img = Image.new('RGB', (width, 1000))
        draw = ImageDraw.Draw(dummy_img)

        # Estimate characters per line from average character width
        sample = "The quick brown fox jumps over the lazy dog"
        avg_char_width = draw.textlength(sample, font=font) / len(sample)
        chars_per_line = int(width / avg_char_width)

        # Wrap text
        lines = []
        for paragraph in text.split('\n'):
            wrapped = textwrap.wrap(paragraph, width=chars_per_line)
            lines.extend(wrapped if wrapped else [''])

        # Calculate total height
        line_height = int(font_size * 1.2)
        total_height = len(lines) * line_height + 20

        # Create actual image
        img = Image.new('RGB', (width, total_height), color='white')
        draw = ImageDraw.Draw(img)

        y = 10
        for line in lines:
            line_width = draw.textlength(line, font=font)

            if align == 'center':
                x = (width - line_width) / 2
            elif align == 'right':
                x = width - line_width
            else:
                x = 0

            x = max(0, x)
            draw.text((x, y), line, font=font, fill='black')
            y += line_height

        return img

    except Exception as e:
        logger.error("Text rendering failed: %s", e)
        return None
