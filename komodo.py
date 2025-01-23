import os
import time
import hashlib
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import fitz  # PyMuPDF
from PIL import Image
from pyzbar.pyzbar import decode
import time
import shutil

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
        if not event.is_directory:
            file_hash = self.calculate_file_hash(event.src_path)
            if file_hash:
                if organized_path:
                    self.hashes[organized_path] = file_hash
                    self.save_hash_store()
                    self.log_change(f"File created and organized: {organized_path} (Hash: {file_hash})")

    def on_created(self, event):
        """Handles file creation events."""
        if not event.is_directory and not self.should_ignore(event.src_path):
            self.pdf_path = event.src_path
    
            # Wait for the file to stabilize
            if not self.wait_for_file_stable(self.pdf_path):
                print(f"File is not ready: {self.pdf_path}")
                return
    
            if self.pdf_path.lower().endswith(".pdf"):
                try:
                    renamed_path = self.rename_pdf()
                    file_hash = self.calculate_file_hash(renamed_path)
                    organized_path = self.organize_file(renamed_path)

                    if file_hash:
                        self.hashes[renamed_path] = file_hash
                        self.save_hash_store()
                        self.log_change(f"File created and renamed: {renamed_path} (Hash: {file_hash})")
                except Exception as e:
                    print(f"Error processing file {self.pdf_path}: {e}")

    def open_pdf_with_retries(self, file_path, retries=5, delay=0.5):
        """Attempts to open a PDF file with retries."""
        for _ in range(retries):
            try:
                return fitz.open(file_path)
            except fitz.FileDataError:
                time.sleep(delay)
        raise Exception(f"Failed to open file after {retries} retries: {file_path}")
    

    def should_ignore(self, file_path):
        """Determines if the file should be ignored based on extension."""
        ignored_extensions = ['.tmp']
        return any(file_path.endswith(ext) for ext in ignored_extensions)

    def wait_for_file_stable(self, file_path, max_attempts=5, delay=0.5):
        """Waits for the file to stabilize (become available for reading)."""
        attempts = 0
        while attempts < max_attempts:
            try:
                with open(file_path, 'rb') as f:
                    return True
            except (PermissionError, IOError):
                time.sleep(delay)
                attempts += 1
        return False

    def organize_file(self, src_path):
        """Organizes the file into the appropriate directory."""
        file_name = os.path.basename(src_path)
        form_id, month = self.parse_barcode(file_name)

        if form_id and month:
            # Determine the destination directory
            dest_dir = os.path.join(".", form_id, month)
            os.makedirs(dest_dir, exist_ok=True)  # Create directory if it doesn't exist

            # Move the file
            dest_path = os.path.join(dest_dir, file_name)
            shutil.move(src_path, dest_path)
            self.log_change(f"File moved to: {dest_path}")
            return dest_path
        else:
            self.log_change(f"Failed to organize file: {src_path}")
            return None

    @staticmethod
    def parse_barcode(file_name):
        """Parses the barcode from the file name to extract Form ID and Month."""
        try:
            # Assuming barcode format is yymmdd[FormID][UserInitials]
            date_part = file_name[:6]
            form_id = file_name[6:10]  # Extract between date and user initials
            year = f"20{date_part[:2]}"
            month = date_part[2:4]
            return form_id, f"{year}-{month}"
        except Exception as e:
            print(f"Error parsing barcode: {e}")
            return None, None
  


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
    folder_to_monitor = "testing"  # Folder to monitor
    hash_store_file = "file_hashes.json"  # JSON file to store file hashes
    log_file = "file_changes.log"  # Log file to record changes

    monitor_folder(folder_to_monitor, hash_store_file, log_file)

