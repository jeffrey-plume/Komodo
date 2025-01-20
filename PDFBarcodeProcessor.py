import os
import fitz  # PyMuPDF
from PIL import Image
from pyzbar.pyzbar import decode

class PDFBarcodeProcessor:
    def __init__(self, pdf_path, dpi=200):
        """
        Initialize the PDFBarcodeProcessor with the path to the PDF and the desired DPI for image conversion.
        """
        self.pdf_path = pdf_path
        self.dpi = dpi

    def pdf_page_to_image(self, page_number):
        """
        Converts a specific page of a PDF to an image using PyMuPDF.
        """
        doc = fitz.open(self.pdf_path)  # Open the PDF
        page = doc[page_number]  # Get the specified page
        pix = page.get_pixmap(dpi=self.dpi)  # Render the page to a pixmap
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)  # Convert to PIL Image
        return img

    def extract_barcodes(self):
        """
        Extracts barcode content from each page of the PDF and returns the first detected barcode value.
        """
        doc = fitz.open(self.pdf_path)
        for page_number in range(len(doc)):
            try:
                # Convert the page to an image
                img = self.pdf_page_to_image(page_number)

                # Decode barcodes from the image
                barcodes = decode(img)
                if barcodes:
                    for barcode in barcodes:
                        barcode_value = barcode.data.decode("utf-8")
                        print(f"Page {page_number + 1}: Found barcode {barcode_value}")
                        return barcode_value
            except Exception as e:
                print(f"Error processing page {page_number + 1}: {e}")
        return None

    def rename_pdf(self):
        """
        Renames the PDF file based on the first detected barcode value.
        """
        print(f"Processing file: {self.pdf_path}")
        barcode_value = self.extract_barcodes()

        if barcode_value:
            # Create the new filename
            new_name = f"{barcode_value}.pdf"
            new_path = os.path.join(os.path.dirname(self.pdf_path), new_name)
            
            # Rename the file
            if not os.path.exists(new_path):
                os.rename(self.pdf_path, new_path)
                print(f"File renamed to: {new_name}")
            else:
                print(f"File with name {new_name} already exists. Skipping.")
        else:
            print("No barcode found in the file.")

if __name__ == "__main__":
    import sys
    import argparse

    # Detect if running in Jupyter/IPython
    if "ipykernel_launcher" in sys.argv[0]:
        # If running in Jupyter/IPython, set a default path
        pdf_path = "C:/Users/Lenovo/OneDrive/Documents/Desktop/barcode.pdf"
        processor = PDFBarcodeProcessor(pdf_path)
        processor.rename_pdf()
    else:
        # Standard argument parser for command-line usage
        parser = argparse.ArgumentParser(description="Scan a PDF for a barcode and rename the file accordingly.")
        parser.add_argument("pdf_path", type=str, help="Path to the PDF file to be processed.")
        
        args = parser.parse_args()

        if os.path.exists(args.pdf_path):
            processor = PDFBarcodeProcessor(args.pdf_path)
            processor.rename_pdf()
        else:
            print(f"File not found: {args.pdf_path}")
