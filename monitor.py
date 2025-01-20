import os
import time
import hashlib
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileChangeLogger(FileSystemEventHandler):
    """Handles file system events and logs changes."""
    
    def __init__(self, hash_store_path, log_file_path):
        self.hash_store_path = hash_store_path
        self.log_file_path = log_file_path
        self.hashes = self.load_hash_store()

    def load_hash_store(self):
        """Loads the stored file hashes from a JSON file."""
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
        print(log_message.strip())  # Optional: Print to console

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
            return None  # Return None if the file cannot be read

    def should_ignore(self, file_path):
        """Determines if the file should be ignored."""
        ignored_extensions = ['.tmp']  # List of ignored file extensions
        return any(file_path.endswith(ext) for ext in ignored_extensions)

    def on_created(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path):
            file_hash = self.calculate_file_hash(event.src_path)
            if file_hash:
                self.hashes[event.src_path] = file_hash
                self.save_hash_store()
                self.log_change(f"File created: {event.src_path} (Hash: {file_hash})")

    def on_modified(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path):
            file_hash = self.calculate_file_hash(event.src_path)
            if file_hash:
                if event.src_path in self.hashes:
                    if self.hashes[event.src_path] == file_hash:
                        self.log_change(f"File modified: {event.src_path} (No changes detected) (Hash: {file_hash})")
                    else:
                        self.log_change(f"File modified: {event.src_path} (Hash changed) (Old: {self.hashes[event.src_path]} New: {file_hash})")
                        self.hashes[event.src_path] = file_hash
                else:
                    self.log_change(f"File modified: {event.src_path} (Newly added hash: {file_hash})")
                    self.hashes[event.src_path] = file_hash
                self.save_hash_store()

    def on_deleted(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path):
            if event.src_path in self.hashes:
                self.log_change(f"File deleted: {event.src_path} (Hash: {self.hashes[event.src_path]})")
                del self.hashes[event.src_path]
                self.save_hash_store()

    def on_moved(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path) and not self.should_ignore(event.dest_path):
            if event.src_path in self.hashes:
                self.hashes[event.dest_path] = self.hashes.pop(event.src_path)
                self.save_hash_store()
                self.log_change(f"File moved: {event.src_path} -> {event.dest_path} (Hash retained: {self.hashes[event.dest_path]})")
            else:
                self.log_change(f"File moved (untracked): {event.src_path} -> {event.dest_path}")

                
def monitor_folder(folder_path, hash_store_path, log_file_path):
    """Monitors the folder and logs file changes."""
    event_handler = FileChangeLogger(hash_store_path, log_file_path)
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=True)  # Enable recursive monitoring

    print(f"Monitoring folder (and subfolders): {folder_path}")
    observer.start()

    try:
        while True:
            time.sleep(1)  # Keep the program running
    except KeyboardInterrupt:
        print("Stopping monitoring...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    folder_to_monitor = "Testing"  # Folder to monitor
    hash_store_file = "file_hashes.json"  # JSON file to store file hashes
    log_file = "file_changes.log"  # Log file to record changes

    monitor_folder(folder_to_monitor, hash_store_file, log_file)

