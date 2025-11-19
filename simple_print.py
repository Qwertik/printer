import win32print
import win32ui
from datetime import datetime

# Try both printer names
PRINTERS = ["RONGTA 80mm Series Printer(1)", "RONGTA 80mm Series Printer"]

def simple_text_print(printer_name, text):
    """Send simple text to printer using Windows GDI"""
    try:
        # Create device context
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        hDC.StartDoc("Test Document")
        hDC.StartPage()
        
        # Print text line by line
        y = 100
        for line in text.split('\n'):
            hDC.TextOut(100, y, line)
            y += 100
        
        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        return True
    except Exception as e:
        print(f"GDI print failed for {printer_name}: {e}")
        return False

def raw_print(printer_name, text):
    """Send raw text to printer"""
    try:
        printer = win32print.OpenPrinter(printer_name)
        try:
            job = win32print.StartDocPrinter(printer, 1, ("Test", None, "RAW"))
            win32print.StartPagePrinter(printer)
            
            # Convert text to bytes
            data = text.encode('utf-8')
            win32print.WritePrinter(printer, data)
            
            win32print.EndPagePrinter(printer)
            win32print.EndDocPrinter(printer)
            return True
        finally:
            win32print.ClosePrinter(printer)
    except Exception as e:
        print(f"Raw print failed for {printer_name}: {e}")
        return False

def text_mode_print(printer_name, text):
    """Send text using TEXT mode"""
    try:
        printer = win32print.OpenPrinter(printer_name)
        try:
            job = win32print.StartDocPrinter(printer, 1, ("Test", None, "TEXT"))
            win32print.StartPagePrinter(printer)
            
            # Convert text to bytes
            data = text.encode('utf-8')
            win32print.WritePrinter(printer, data)
            
            win32print.EndPagePrinter(printer)
            win32print.EndDocPrinter(printer)
            return True
        finally:
            win32print.ClosePrinter(printer)
    except Exception as e:
        print(f"TEXT mode print failed for {printer_name}: {e}")
        return False

if __name__ == "__main__":
    # Test text
    test_text = f"""
================================
        TEST RECEIPT
================================
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Item 1.................$10.00
Item 2.................$5.00
Item 3.................$7.50
--------------------------------
TOTAL:                 $22.50

Thank you for your purchase!
================================
"""

    print("Testing different print methods...\n")
    
    for printer_name in PRINTERS:
        print(f"\nTesting printer: {printer_name}")
        print("=" * 50)
        
        # Method 1: GDI printing
        print("1. Testing GDI printing...")
        if simple_text_print(printer_name, test_text):
            print("   ✓ GDI print sent successfully")
        
        # Method 2: RAW printing
        print("2. Testing RAW printing...")
        if raw_print(printer_name, test_text):
            print("   ✓ RAW print sent successfully")
        
        # Method 3: TEXT mode printing
        print("3. Testing TEXT mode printing...")
        if text_mode_print(printer_name, test_text):
            print("   ✓ TEXT print sent successfully")
        
        print("-" * 50)
        input("Press Enter to test next printer or Ctrl+C to stop...")