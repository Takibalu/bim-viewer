import shutil
import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
import os
from datetime import datetime
import logging
import asyncio
from converter import IFCConverter
from sensor_data import sensordata, update_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='unused/ifc_upload.log'
)
logger = logging.getLogger(__name__)
# Define the lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    task = asyncio.create_task(update_data())
    yield  # The app runs during this yield
    # Shutdown logic
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="IFC File Storage API",
    description="API for storing IFC files and their blueprints",
    lifespan=lifespan,
)

# Configuration
UPLOAD_DIR = "uploads"
CONVERTED_DIR = "converted"

ALLOWED_EXTENSIONS = {'.ifc'}
ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}

# Create necessary directories
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Endpoint to fetch the data
@app.get("/sensordata")
def get_sensordata():
    return sensordata


@app.post("/upload/")
async def upload(ifc_file: UploadFile = File(...), img_file: UploadFile = File(...)):
    # Check if the file has the correct extension
    if not ifc_file.filename.endswith(tuple(ALLOWED_EXTENSIONS)):
        return JSONResponse(status_code=400, content={"message": "Only .ifc files are allowed"})
    if not img_file.filename.endswith(tuple(ALLOWED_IMAGE_EXTENSIONS)):
        return JSONResponse(status_code=400, content={"message": "Only image files (.png, .jpg, .jpeg) are allowed"})

    # Create a subdirectory for this upload
    sub_dir = os.path.join(UPLOAD_DIR, os.path.splitext(ifc_file.filename)[0])
    os.makedirs(sub_dir, exist_ok=True)

    # Save IFC file
    ifc_path = os.path.join(sub_dir, ifc_file.filename)
    with open(ifc_path, "wb") as f:
        f.write(await ifc_file.read())

    # Save Image file
    img_path = os.path.join(sub_dir, img_file.filename)
    with open(img_path, "wb") as f:
        f.write(await img_file.read())

    return {
        "message": "Files uploaded successfully!",
        "ifc_file": ifc_path,
        "img_file": img_path
    }

@app.get("/download/{folder}")
async def download_folder(folder: str):
    """
    Download a stored IFC file
    """
    folder_path = os.path.join(UPLOAD_DIR, folder)

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail="Folder not found")
    # Create a temporary zip file
    zip_file_path = f"{folder_path}.zip"
    shutil.make_archive(folder_path, 'zip', folder_path)

    # Ensure the file exists before returning it
    if not os.path.exists(zip_file_path):
        raise HTTPException(status_code=500, detail="Could not create zip file")

    # Return the zip file as a response
    return FileResponse(
        zip_file_path,
        media_type="application/zip",
        filename=f"{folder}.zip",
    )


@app.get("/list")
async def list_uploaded_files():
    """
    List all uploaded folders and their contents
    """
    try:
        # Ensure the upload directory exists
        if not os.path.exists(UPLOAD_DIR):
            return {"folders": []}

        # List all subdirectories in the upload directory
        folders = [
            {
                "folder_name": folder,
                "files": os.listdir(os.path.join(UPLOAD_DIR, folder)),
                "uploaded_at": datetime.fromtimestamp(
                    os.path.getctime(os.path.join(UPLOAD_DIR, folder))
                ).isoformat()
            }
            for folder in os.listdir(UPLOAD_DIR)
            if os.path.isdir(os.path.join(UPLOAD_DIR, folder))
        ]

        return {
            "total_folders": len(folders),
            "folders": folders
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing files: {str(e)}"
        )

@app.delete("/delete/{folder}")
async def delete_folder(folder: str):
    """
    Delete a stored folder and its contents
    """
    folder_path = os.path.join(UPLOAD_DIR, folder)
    zip_file_path = f"{folder_path}.zip"

    # Check if folder exists
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail="Folder not found")

    try:
        # Remove the folder and its contents
        shutil.rmtree(folder_path)

        # Remove the zip file if it exists
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)

        return {
            "message": f"Folder {folder} and associated files deleted successfully",
            "deleted_folder": folder
        }
    except Exception as e:
        # Log the error (you might want to use a proper logging mechanism)
        print(f"Error deleting folder: {e}")
        raise HTTPException(status_code=500, detail="Could not delete folder")


@app.post("/convert/")
async def convert_file(
        filename: str = Form(...),
        destination_dir: str = Form("converted")
):
    """
    Convert an IFC file to OBJ and XML formats

    :param filename: Name of the IFC file to convert
    :param destination_dir: Optional destination directory for converted files
    """
    try:
        # Validate filename exists in upload directory
        input_file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(input_file_path):
            raise HTTPException(status_code=404, detail=f"File {filename} not found in uploads")

        # Create converter with input from upload directory
        converter = IFCConverter(
            input_dir=UPLOAD_DIR,
            output_dir=os.path.join(CONVERTED_DIR, destination_dir)
        )

        # Perform the conversion
        result = converter.convert_file(filename)

        # Check conversion status
        if result['status'] == 'success':
            return {
                "message": "Conversion successful",
                "obj_path": result['obj_path'],
                "xml_path": result['xml_path']
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])

    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    subprocess.run(["sudo","apt","update"])
    subprocess.run(["sudo","apt","install","wine"])

    # Use environment variable for port, with fallback
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
