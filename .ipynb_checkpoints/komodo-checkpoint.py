import os
import time
import hashlib
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import fitz  # PyMuPDF
from PIL import Image
from pyzbar.pyzbar import decode


class FileChangeLogger(FileSystemEventHandler):
    """Handles file system events, processes barcodes, renames files, and logs changes."""

    def __init__(self, hash_store_path, log_file_path, dpi=200):
        self.hash_store_path = hash_store_path
        self.log_file_path = log_file_path
        self.hashes = self.load_hash_store()
        self.pdf_path = None
        self.dpi = dpi

    def load_hash_store(self):
        """Loads stored file hashes from a JSON file."""
        if os.path.exists(self.hash_store_path):
            with open(self.hash_store_path, 'r') as file:
                return json.load(file)
        return {}

    def save_hash_store(self):
        """Saves the current hashes to a JSON file."""
        with open(self.hash_store_path, 'w') as file:
            json.dump(self.hashes, file, indent=4)

    def log_change(self, message):
        """Logs a change to the log file."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        with open(self.log_file_path, 'a') as log_file:
            log_file.write(log_message)
        print(log_message.strip())

    @staticmethod
    def calculate_file_hash(file_path):
        """Calculates and returns the SHA256 hash of a file."""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as file:
                while chunk := file.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"Error hashing file {file_path}: {e}")
            return None

    def pdf_page_to_image(self, page_number):
        """Converts a specific page of a PDF to an image."""
        doc = fitz.open(self.pdf_path)
        page = doc[page_number]
        pix = page.get_pixmap(dpi=self.dpi)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img

    def extract_barcodes(self):
        """Extracts barcode content from each page of a PDF."""
        doc = fitz.open(self.pdf_path)
        for page_number in range(len(doc)):
            try:
                img = self.pdf_page_to_image(page_number)
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
        """Renames the PDF based on its barcode."""
        barcode_value = self.extract_barcodes()
        if barcode_value:
            new_name = f"{barcode_value}.pdf"
            new_path = os.path.join(os.path.dirname(self.pdf_path), new_name)
            if not os.path.exists(new_path):
                os.rename(self.pdf_path, new_path)
                print(f"File renamed to: {new_name}")
                return new_path
            else:
                print(f"File with name {new_name} already exists. Skipping.")
        else:
            print("No barcode found in the file.")
        return self.pdf_path

    def on_created(self, event):
        """Handles file creation events."""
        if not event.is_directory and not self.should_ignore(event.src_path):
            self.pdf_path = event.src_path
            if self.pdf_path.lower().endswith(".pdf"):
                renamed_path = self.rename_pdf()
                file_hash = self.calculate_file_hash(renamed_path)
                if file_hash:
                    self.hashes[renamed_path] = file_hash
                    self.save_hash_store()
                    self.log_change(f"File created and renamed: {renamed_path} (Hash: {file_hash})")

    def should_ignore(self, file_path):
        """Determines if the file should be ignored based on extension."""
        ignored_extensions = ['.tmp']
        return any(file_path.endswith(ext) for ext in ignored_extensions)


def monitor_folder(folder_path, hash_store_path, log_file_path):
    """Monitors the folder and logs file changes."""
    event_handler = FileChangeLogger(hash_store_path, log_file_path)
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=True)

    print(f"Monitoring folder: {folder_path}")
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping monitoring...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    folder_to_monitor = "Testing"  # Folder to monitor
    hash_store_file = "file_hashes.json"  # JSON file to store file hashes
    log_file = "file_changes.log"  # Log file to record changes

    monitor_folder(folder_to_monitor, hash_store_file, log_file)

