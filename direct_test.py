import win32print

# Test all available printers to find which one works
printers = ["Generic / Text Only", "RONGTA 80mm Series Printer", "RONGTA 80mm Series Printer(2)"]

for printer_name in printers:
    print(f"\nTrying printer: {printer_name}")
    print("-" * 40)
    
    try:
        # Open printer
        printer = win32print.OpenPrinter(printer_name)
        
        # Simple text without any ESC/POS commands
        simple_text = """
=============================
       TEST RECEIPT
=============================
This is a test print
If you can see this,
the printer is working!

Item 1: $10.00
Item 2: $5.00
-----------------------------
TOTAL: $15.00

Thank you!
=============================




"""
        
        # Try TEXT mode (most compatible)
        try:
            job = win32print.StartDocPrinter(printer, 1, ("Direct Test", None, "TEXT"))
            win32print.StartPagePrinter(printer)
            win32print.WritePrinter(printer, simple_text.encode('ascii', 'ignore'))
            win32print.EndPagePrinter(printer)
            win32print.EndDocPrinter(printer)
            print(f"OK - TEXT mode: Sent successfully")
        except Exception as e:
            print(f"FAILED - TEXT mode failed: {e}")
        
        # Try RAW mode
        try:
            job = win32print.StartDocPrinter(printer, 1, ("Direct Test RAW", None, "RAW"))
            win32print.StartPagePrinter(printer)
            win32print.WritePrinter(printer, simple_text.encode('ascii', 'ignore'))
            win32print.EndPagePrinter(printer)
            win32print.EndDocPrinter(printer)
            print(f"OK - RAW mode: Sent successfully")
        except Exception as e:
            print(f"FAILED - RAW mode failed: {e}")
        
        win32print.ClosePrinter(printer)
        
    except Exception as e:
        print(f"FAILED - Could not open printer: {e}")