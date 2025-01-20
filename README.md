
# Komodo: The Folder Monitoring Monitor Lizard

**Komodo** is a Python-based monitor lizard that detects new files, extracts barcodes from PDFs, renames the files, and logs their hashes and changes. It's an automated solution to keep files organized.

---

## Features

- 🦎 **Folder Monitoring**: Continuously watches a specified folder for file events (creation, modification, deletion, and movement).
- 📄 **Barcode Extraction**: Processes newly added PDFs to extract barcode values.
- 🏷️ **File Renaming**: Automatically renames PDF files based on their barcode values.
- 🔒 **Hash Logging**: Computes SHA256 hashes of files and maintains a history in a JSON file.
- 📝 **Change Logging**: Logs all file changes (creation, modification, deletion, movement) in a separate log file.

---

## Requirements

Ensure you have the following dependencies installed:

- Python 3.8+
- **Required Libraries**:
  - `watchdog`
  - `PyMuPDF` (`fitz`)
  - `Pillow`
  - `pyzbar`

Install all dependencies using pip:

```bash
pip install watchdog pymupdf pillow pyzbar
```

---

## Setup and Usage

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/jeffrey-plume/komodo.git
   cd komodo
   ```

2. **Configure Monitoring**:
   - Open the script and update the following variables:
     ```python
     folder_to_monitor = "Testing"  # Folder to monitor
     hash_store_file = "file_hashes.json"  # JSON file to store file hashes
     log_file = "file_changes.log"  # Log file to record changes
     ```

3. **Run Komodo**:
   ```bash
   python komodo.py
   ```

4. **Monitor the Output**:
   - Komodo logs all operations to the console and the `file_changes.log` file.
   - Processed file hashes are saved in `file_hashes.json`.

---

## Workflow

1. **Folder Monitoring**:
   - Watches the specified folder (and subfolders) for file events in real-time.

2. **PDF Barcode Processing**:
   - On detecting a new PDF file:
     - Extracts the barcode value from the PDF.
     - Renames the file using the barcode value.

3. **Hash and Change Logging**:
   - Computes the SHA256 hash of the file before and after renaming.
   - Logs all operations in `file_changes.log`.

---

## File Structure

```plaintext
.
├── file_hashes.json     # JSON file for storing file hashes
├── file_changes.log     # Log file for recording file operations
├── komodo.py            # Main Python script
└── README.md            # Project documentation
```


---

## Known Limitations

- Only processes PDFs with image-based barcodes (e.g., QR codes, EAN, Code128).
- Requires **Poppler** for PDF rendering (install via system package manager if missing).
- Ignores files with `.tmp` extensions.

---

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request.

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

---
