import win32print
import win32ui
from PIL import Image, ImageWin
import tempfile
import os

PRINTER_NAME = "RONGTA 80mm Series Printer(5)"

def test_direct_print():
    """Test direct printing using win32print"""
    try:
        # Method 1: Direct raw printing
        print(f"Testing raw print to {PRINTER_NAME}")
        printer = win32print.OpenPrinter(PRINTER_NAME)
        try:
            # Start a print job
            job = win32print.StartDocPrinter(printer, 1, ("Test Print", None, "RAW"))
            win32print.StartPagePrinter(printer)
            
            # ESC/POS commands
            commands = b""
            commands += b"\x1B\x40"  # Initialize printer
            commands += b"\x1B\x61\x01"  # Center align
            commands += b"TEST PRINT\n"
            commands += b"\x1B\x61\x00"  # Left align
            commands += b"Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode() + b"\n"
            commands += b"Printer: RONGTA 80mm\n"
            commands += b"Status: OK\n"
            commands += b"\n\n\n"
            commands += b"\x1D\x56\x00"  # Cut paper
            
            win32print.WritePrinter(printer, commands)
            win32print.EndPagePrinter(printer)
            win32print.EndDocPrinter(printer)
            print("Raw print command sent successfully")
        finally:
            win32print.ClosePrinter(printer)
            
    except Exception as e:
        print(f"Error: {e}")

def test_text_print():
    """Test simple text printing"""
    try:
        print(f"Testing simple text print to {PRINTER_NAME}")
        printer = win32print.OpenPrinter(PRINTER_NAME)
        try:
            job = win32print.StartDocPrinter(printer, 1, ("Test Text", None, "TEXT"))
            win32print.StartPagePrinter(printer)
            
            text = "TEST RECEIPT\n"
            text += "=" * 30 + "\n"
            text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            text += "Item 1: $10.00\n"
            text += "Item 2: $5.00\n"
            text += "-" * 30 + "\n"
            text += "Total: $15.00\n"
            text += "\n\n\n\n"
            
            win32print.WritePrinter(printer, text.encode('utf-8'))
            win32print.EndPagePrinter(printer)
            win32print.EndDocPrinter(printer)
            print("Text print sent successfully")
        finally:
            win32print.ClosePrinter(printer)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    from datetime import datetime
    
    print("Testing RONGTA printer...")
    print("-" * 40)
    
    # List available printers
    printers = [printer[2] for printer in win32print.EnumPrinters(2)]
    print("Available printers:")
    for p in printers:
        print(f"  - {p}")
    print("-" * 40)
    
    # Test both methods
    print("\n1. Testing RAW ESC/POS printing:")
    test_direct_print()
    
    print("\n2. Testing simple TEXT printing:")
    test_text_print()