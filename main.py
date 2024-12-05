import shutil
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


@app.get("/files/")
async def list_files():
    """
    List all stored IFC files
    """
    files = []
    for filename in os.listdir(UPLOAD_DIR):
        if filename.endswith('.ifc'):
            file_path = os.path.join(UPLOAD_DIR, filename)
            files.append({
                "filename": filename,
                "size": os.path.getsize(file_path),
                "created_at": datetime.fromtimestamp(os.path.getctime(file_path))
            })

    return {"files": files}

@app.delete("/delete/{filename}")
async def delete_file(filename: str):
    """
    Delete a stored IFC file from the server.
    """
    print(f"Delete request received for: {filename}")
    print(f"Files in upload directory: {os.listdir(UPLOAD_DIR)}")

    # Iterate over files in the upload directory
    for stored_file in os.listdir(UPLOAD_DIR):
        print(f"Comparing '{filename}' with '{stored_file}'")
        if stored_file.lower() == filename.lower():  # Case-insensitive match
            file_path = os.path.join(UPLOAD_DIR, stored_file)
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
                return {"message": f"File '{stored_file}' deleted successfully."}
            except Exception as e:
                print(f"Error deleting file '{stored_file}': {str(e)}")
                raise HTTPException(status_code=500, detail="An error occurred while deleting the file.")

    # If no matching file was found
    print(f"File '{filename}' not found in the directory.")
    raise HTTPException(status_code=404, detail="File not found")


@app.post("/convert/")
async def convert_file(filename: str = Form(...), location: str = Form(...)):
    """
    Convert an IFC file to OBJ and XML formats.
    """
    # Check if the file exists in the uploads directory
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Initialize the IFCConverter
    converter = IFCConverter(location, CONVERTED_DIR)

    # Perform the conversion
    result = converter.convert_file(filename)

    if result["status"] == "success":
        return {
            "message": "File converted successfully!",
            "obj_path": result["obj_path"],
            "xml_path": result["xml_path"]
        }
    else:
        raise HTTPException(status_code=500, detail=result["message"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
