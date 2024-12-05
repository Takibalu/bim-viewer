
import clr
import sys
import os
import traceback
import json
from datetime import datetime

# Setup logging in the script
import logging
logging.basicConfig(
    filename='revit_script_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    # Log startup information
    logging.info(f"Script started at {datetime.now()}")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Arguments received: {sys.argv}")

    # Add references
    clr.AddReference('RevitAPI')
    clr.AddReference('RevitAPIUI')
    from Autodesk.Revit.DB import *

    logging.info("Successfully loaded Revit API references")

    def convert_to_ifc(input_path, output_path):
        logging.info(f"Starting conversion: {input_path} -> {output_path}")

        try:
            # Verify input file exists
            if not os.path.exists(input_path):
                raise Exception(f"Input file not found: {input_path}")

            logging.info("Opening document...")
            app = __revit__
            doc = app.OpenDocumentFile(input_path)
            logging.info("Document opened successfully")

            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Set up IFC export options
            logging.info("Setting up IFC export options...")
            options = IFCExportOptions()
            options.FileVersion = IFCVersion.IFC2x3
            options.SpaceBoundaries = 1
            options.ExportBaseQuantities = True

            # Export to IFC
            logging.info("Starting IFC export...")
            result = doc.Export(os.path.dirname(output_path), 
                              os.path.basename(output_path), 
                              options)

            # Check if export was successful
            if not os.path.exists(output_path):
                raise Exception("Export completed but output file not found")

            logging.info(f"Export completed successfully. File size: {os.path.getsize(output_path)} bytes")

            # Close the document
            doc.Close(False)
            logging.info("Document closed successfully")

            return {"status": "success", "message": "Conversion completed successfully"}

        except Exception as e:
            logging.error(f"Error in convert_to_ifc: {str(e)}")
            logging.error(traceback.format_exc())
            return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

    # Get arguments
    input_path = os.path.abspath(sys.argv[1])
    output_path = os.path.abspath(sys.argv[2])
    result_file = os.path.abspath(sys.argv[3])

    logging.info(f"Input path: {input_path}")
    logging.info(f"Output path: {output_path}")
    logging.info(f"Result file: {result_file}")

    # Perform conversion
    result = convert_to_ifc(input_path, output_path)

    # Write result to file
    logging.info(f"Writing result to {result_file}")
    with open(result_file, 'w') as f:
        json.dump(result, f)
    logging.info("Script completed successfully")

except Exception as e:
    logging.error(f"Top-level exception: {str(e)}")
    logging.error(traceback.format_exc())
    # Ensure we write something to the result file even if we crash
    with open(sys.argv[3], 'w') as f:
        json.dump({
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }, f)
