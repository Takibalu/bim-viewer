import zipfile

import requests
import argparse
import os

from converter import IFCConverter

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Directories for uploads and downloads
LOCAL_STORE_DIR = os.path.join(SCRIPT_DIR, "local store")

# Constants for the server URL
SERVER_URL = "http://127.0.0.1:8000"


def upload_files(ifc_file, img_file):
    ifc_file_path = ifc_file
    img_file_path = img_file

    if not os.path.exists(ifc_file_path):
        print(f"File '{ifc_file}' not found in '{LOCAL_STORE_DIR}'. Please check the filename.")
        return
    if not os.path.exists(img_file_path):
        print(f"File '{img_file}' not found in '{LOCAL_STORE_DIR}'. Please check the filename.")

    url = f"{SERVER_URL}/upload/"

    # Open the file in binary mode and prepare it for uploading
    with open(ifc_file_path, "rb") as f:
        files = {"ifc_file": (ifc_file, f)}
        with open(img_file_path, "rb") as im:
            files.update({"img_file": (img_file, im)})
            # Send POST request to the server
            response = requests.post(url, files=files)

    # Print the response from the server
    if response.status_code == 200:
        print("File uploaded successfully.")
    else:
        print("Failed to upload file.")


def download_folder(folder):
    url = f"{SERVER_URL}/download/{folder}"

    # Send GET request to the server to download the file
    response = requests.get(url)

    if response.status_code == 200:

        os.makedirs(LOCAL_STORE_DIR, exist_ok=True)
        extracted_folder_path = os.path.join(LOCAL_STORE_DIR, folder)
        zip_file_path = os.path.join(LOCAL_STORE_DIR, f"{folder}.zip")
        # Save the ZIP file locally
        with open(zip_file_path, "wb") as zip_file:
            for chunk in response.iter_content(chunk_size=8192):
                zip_file.write(chunk)
        print(f"ZIP file downloaded successfully: {zip_file_path}")

        # Extract the ZIP file into a folder
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_folder_path)
        print(f"Files extracted to: {extracted_folder_path}")

        # Optionally, delete the ZIP file after extraction
        os.remove(zip_file_path)
        print(f"ZIP file deleted: {zip_file_path}")

        return extracted_folder_path
    else:
        print(f"Failed to download folder. Status code: {response.status_code}")
        print("Response:", response.json())
        return None


def list_files():
    url = f"{SERVER_URL}/files/"

    # Send GET request to list the files from the server
    response = requests.get(url)

    if response.status_code == 200:
        files = response.json().get("files", [])
        if files:
            print("Files on the server:")
            for file in files:
                print(f"{file['filename']} - Size: {file['size']} bytes, Created: {file['created_at']}")
        else:
            print("No files found on the server.")
    else:
        print(f"Failed to retrieve file list. Status code: {response.status_code}")
        print("Response:", response.json())


def convert_file(filename):
    """
    Convert a downloaded IFC file to OBJ and XML formats
    """
    # Initialize the converter
    converter = IFCConverter(LOCAL_STORE_DIR, os.path.join(SCRIPT_DIR, "converted"))

    # Perform the conversion
    result = converter.convert_file(filename)

    if result["status"] == "success":
        print(f"File converted successfully!")
        print(f"OBJ file: {result['obj_path']}")
        print(f"XML file: {result['xml_path']}")
    else:
        print(f"Conversion failed: {result['message']}")

def delete_file(filename):
    """
    Delete a file from the server.
    """
    url = f"{SERVER_URL}/delete/{filename}"

    print(f"Sending DELETE request for '{filename}' to {url}...")

    # Send DELETE request to the server
    response = requests.delete(url)

    # Handle server responses
    if response.status_code == 200:
        print(f"File '{filename}' deleted successfully from the server.")
    elif response.status_code == 404:
        print(f"File '{filename}' not found on the server.")
    elif response.status_code == 400:
        print(f"Invalid request: {response.json().get('detail', 'Unknown error')}")
    else:
        print(f"Failed to delete file. Status code: {response.status_code}")
        print("Response:", response.text)


def bulk_download():
    """
    Download all files from the server.
    """
    # Get the list of files from the server
    url = f"{SERVER_URL}/files/"
    response = requests.get(url)

    if response.status_code == 200:
        files = response.json().get("files", [])
        if not files:
            print("No files available on the server to download.")
            return

        # Ensure the download directory exists
        os.makedirs(LOCAL_STORE_DIR, exist_ok=True)

        print(f"Found {len(files)} files on the server. Starting bulk download...")

        for file_info in files:
            filename = file_info["filename"]
            print(f"Downloading '{filename}'...")
            file_url = f"{SERVER_URL}/download/{filename}"
            file_response = requests.get(file_url)

            if file_response.status_code == 200:
                save_path = os.path.join(LOCAL_STORE_DIR, filename)
                with open(save_path, "wb") as f:
                    f.write(file_response.content)
                print(f"Downloaded '{filename}' to '{save_path}'.")
            else:
                print(f"Failed to download '{filename}'. Status code: {file_response.status_code}")

        print("Bulk download completed.")
    else:
        print("Failed to retrieve file list from the server.")
        print(f"Status code: {response.status_code}, Response: {response.json()}")


if __name__ == "__main__":
    # Ensure the upload directory exists
    os.makedirs(LOCAL_STORE_DIR, exist_ok=True)

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Upload, Download, or List IFC files")
    parser.add_argument("operation",
                        choices=["upload", "download", "list", "convert", "delete", "bulk_download"],
                        help="Choose 'upload', 'download', 'list', 'convert', 'delete', or 'bulk_download'")

    parser.add_argument("file_name", type=str,
                        help="File name to upload from uploads folder or download from the server. (For list operation, use 'list')",
                        nargs='?')
    parser.add_argument("img_file", type=str,
                        nargs='?',)

    # Parse arguments
    args = parser.parse_args()

    if args.operation == "upload":
        if args.file_name and args.img_file:
            # Upload file from the uploads directory
            upload_files(args.file_name, args.img_file)
        else:
            print("Please provide the filenames to upload.")

    elif args.operation == "download":
        if not args.file_name:
            print("Please provide the filename to download.")
        else:
            # Download the file from the server with the same name
            download_folder(args.file_name)

    elif args.operation == "list":
        # List the files available on the server
        list_files()

    elif args.operation == "convert":
        if not args.file_name:
            print("Please provide the filename to convert.")
        else:
            # Convert the downloaded file
            convert_file(args.file_name)

    elif args.operation == "delete":
        if not args.file_name:
            print("Please provide the filename to delete.")
        else:
            delete_file(args.file_name)

    elif args.operation == "bulk_download":
        bulk_download()
