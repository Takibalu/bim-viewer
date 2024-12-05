import argparse
import requests
import os
import sys
from typing import Optional


def upload_file(file_path: str, server_url: str = "http://localhost:8000") -> None:
    """Upload and convert a Revit file."""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = requests.post(f"{server_url}/convert/", files=files)

        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['message']}")
            print(f"Output file: {result['output_file']}")
        else:
            print(f"Error: {response.json()['detail']}")

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {str(e)}")


def list_files(server_url: str = "http://localhost:8000") -> None:
    """List all converted files."""
    try:
        response = requests.get(f"{server_url}/files/")

        if response.status_code == 200:
            files = response.json()['files']
            if not files:
                print("No converted files found.")
                return

            print("\nConverted Files:")
            print("-" * 80)
            for file in files:
                size_mb = file['size'] / (1024 * 1024)
                print(f"Filename: {file['filename']}")
                print(f"Size: {size_mb:.2f} MB")
                print(f"Created: {file['created_at']}")
                print("-" * 80)
        else:
            print(f"Error: {response.json()['detail']}")

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {str(e)}")


def download_file(filename: str, output_path: Optional[str] = None,
                  server_url: str = "http://localhost:8000") -> None:
    """Download a converted file."""
    try:
        response = requests.get(f"{server_url}/download/{filename}", stream=True)

        if response.status_code == 200:
            output_path = output_path or filename
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Successfully downloaded file to: {output_path}")
        else:
            print(f"Error: {response.json()['detail']}")

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Revit to IFC Converter Client")
    parser.add_argument("--server", default="http://localhost:8000",
                        help="Server URL (default: http://localhost:8000)")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload and convert a Revit file")
    upload_parser.add_argument("file", help="Path to the Revit file")

    # List command
    subparsers.add_parser("list", help="List all converted files")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download a converted file")
    download_parser.add_argument("filename", help="Name of the file to download")
    download_parser.add_argument("--output", help="Output path for downloaded file")

    args = parser.parse_args()

    if args.command == "upload":
        upload_file(args.file, args.server)
    elif args.command == "list":
        list_files(args.server)
    elif args.command == "download":
        download_file(args.filename, args.output, args.server)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()