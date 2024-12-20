
import logging
import os
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='ifc_conversion.log'
)
logger = logging.getLogger(__name__)


class IFCConverter:
    def __init__(self, input_dir="local store", output_dir="converted"):
        """
        Initialize the converter with input and output directories
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.obj_dir = os.path.join(output_dir, "obj")
        self.xml_dir = os.path.join(output_dir, "xml")

        # Create necessary directories
        for directory in [self.output_dir, self.obj_dir, self.xml_dir]:
            os.makedirs(directory, exist_ok=True)

    def convert_file(self,filename):
        """
        Convert an IFC file to OBJ and XML formats using an external IFC converter.
        """
        # Paths
        ifc_converter_path = os.path.join(SCRIPT_DIR, "IfcConvert.exe")  # Path to the converter executable
        input_file_path = os.path.join(self.input_dir, filename)  # Path to the IFC file to be converted
        logger.info(f"Converting {filename} to OBJ and XML")
        logger.info(f"IFC coverter path: {ifc_converter_path}")
        logger.info(f"Input file path: {input_file_path}")
        obj_output = os.path.join(self.obj_dir, f"{os.path.splitext(filename)[0]}.obj")
        xml_output = os.path.join(self.xml_dir, f"{os.path.splitext(filename)[0]}.xml")
        logger.info(f"OBJ output file path: {obj_output}")
        logger.info(f"XML output file path: {xml_output}")
        try:
            # Run the converter for OBJ format
            subprocess.run(
                ["docker", "run", "aecgeeks/ifcopenshell", "IfcConvert", input_file_path, obj_output,
                 "--use-element-guids"],
                check=True
            )# Run the converter for XML format (if applicable)
            logger.info("ASD")
            subprocess.run(
                ["docker", "run", "aecgeeks/ifcopenshell", "IfcConvert", input_file_path, xml_output],
                check=True
            )
            return {
                "status": "success",
                "obj_path": obj_output,
                "xml_path": xml_output
            }

        except subprocess.CalledProcessError as e:
            return {
                "status": "failure",
                "message": f"Conversion failed: {e}"
            }
        except FileNotFoundError:
            logger.info(FileNotFoundError, subprocess.CompletedProcess)
            return {
                "status": "failure",
                "message": "IFC converter executable not found."
            }