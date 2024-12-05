from ifcopenshell import geom, open
import os
from xml.etree import ElementTree as ET
from datetime import datetime
import logging
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='ifc_conversion.log'
)
logger = logging.getLogger(__name__)


class IFCConverter:
    def __init__(self, download_dir="downloads", output_dir="converted"):
        """
        Initialize the converter with input and output directories
        """
        self.download_dir = download_dir
        self.output_dir = output_dir
        self.obj_dir = os.path.join(output_dir, "obj")
        self.xml_dir = os.path.join(output_dir, "xml")

        # Create necessary directories
        for directory in [self.output_dir, self.obj_dir, self.xml_dir]:
            os.makedirs(directory, exist_ok=True)

    def convert_file(self, ifc_filename):
        """
        Convert an IFC file to OBJ and XML formats
        """
        try:
            ifc_path = os.path.join(self.download_dir, ifc_filename)
            if not os.path.exists(ifc_path):
                raise FileNotFoundError(f"IFC file not found: {ifc_path}")

            # Load the IFC file
            ifc_file = open(ifc_path)
            logger.info(f"Successfully opened IFC file: {ifc_path}")

            # Generate base filename without extension
            base_filename = os.path.splitext(ifc_filename)[0]

            # Convert to OBJ using temporary directory
            obj_path = self._convert_to_obj(ifc_file, base_filename)
            logger.info(f"Successfully converted to OBJ: {obj_path}")

            # Generate XML metadata
            xml_path = self._generate_xml(ifc_file, base_filename, obj_path)
            logger.info(f"Successfully generated XML: {xml_path}")

            return {
                "obj_path": obj_path,
                "xml_path": xml_path,
                "status": "success",
                "message": "Conversion completed successfully"
            }

        except Exception as e:
            error_msg = f"Error converting file {ifc_filename}: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }

    def _convert_to_obj(self, ifc_file, base_filename):
        """
        Convert IFC to OBJ format using IfcOpenShell
        """
        try:
            # Create temporary directory for conversion
            with tempfile.TemporaryDirectory() as temp_dir:
                # Set up the settings for conversion
                settings = geom.settings()
                settings.set(settings.USE_WORLD_COORDS, True)
                settings.set(settings.USE_BREP_DATA, True)
                settings.set(settings.SEW_SHELLS, True)
                settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)

                # Initialize the iterator
                iterator = geom.iterator(settings, ifc_file, include=['IfcBuildingElement'])

                # Prepare OBJ file path
                obj_path = os.path.join(self.obj_dir, f"{base_filename}.obj")
                mtl_path = os.path.join(self.obj_dir, f"{base_filename}.mtl")

                # Open OBJ and MTL files for writing
                with open(obj_path, 'w') as obj_file, open(mtl_path, 'w') as mtl_file:
                    obj_file.write(f"mtllib {os.path.basename(mtl_path)}\n")

                    vertex_offset = 1
                    normal_offset = 1

                    # Process each shape
                    if iterator.initialize():
                        while True:
                            shape = iterator.get()

                            # Write vertices
                            verts = shape.verts
                            for i in range(0, len(verts), 3):
                                obj_file.write(f"v {verts[i]} {verts[i + 1]} {verts[i + 2]}\n")

                            # Write normals if available
                            normals = shape.normals
                            if normals:
                                for i in range(0, len(normals), 3):
                                    obj_file.write(f"vn {normals[i]} {normals[i + 1]} {normals[i + 2]}\n")

                            # Write faces
                            faces = shape.faces
                            for i in range(0, len(faces), 3):
                                if normals:
                                    v1, v2, v3 = faces[i:i + 3]
                                    obj_file.write(f"f {v1 + vertex_offset}/{v1 + normal_offset} "
                                                   f"{v2 + vertex_offset}/{v2 + normal_offset} "
                                                   f"{v3 + vertex_offset}/{v3 + normal_offset}\n")
                                else:
                                    v1, v2, v3 = faces[i:i + 3]
                                    obj_file.write(
                                        f"f {v1 + vertex_offset} {v2 + vertex_offset} {v3 + vertex_offset}\n")

                            vertex_offset += len(verts) // 3
                            if normals:
                                normal_offset += len(normals) // 3

                            if not iterator.next():
                                break

                return obj_path

        except Exception as e:
            logger.error(f"Error during OBJ conversion: {str(e)}")
            raise

    def _generate_xml(self, ifc_file, base_filename, obj_path):
        """
        Generate XML metadata for Unity
        """
        try:
            xml_path = os.path.join(self.xml_dir, f"{base_filename}.xml")

            # Create root element
            root = ET.Element("IFCModel")

            # Add basic metadata
            metadata = ET.SubElement(root, "Metadata")
            ET.SubElement(metadata, "FileName").text = base_filename
            ET.SubElement(metadata, "ConversionDate").text = datetime.now().isoformat()
            ET.SubElement(metadata, "OBJPath").text = os.path.relpath(obj_path, self.output_dir)

            # Add project information
            projects = ifc_file.by_type("IfcProject")
            if projects:
                project = projects[0]
                project_info = ET.SubElement(root, "ProjectInformation")
                ET.SubElement(project_info, "Name").text = project.Name or "Unnamed Project"
                ET.SubElement(project_info, "Description").text = project.Description or ""

            # Add building elements information
            elements = ET.SubElement(root, "BuildingElements")
            for element in ifc_file.by_type("IfcBuildingElement"):
                elem = ET.SubElement(elements, "Element")
                ET.SubElement(elem, "GlobalId").text = element.GlobalId
                ET.SubElement(elem, "Type").text = element.is_a()
                ET.SubElement(elem, "Name").text = element.Name or ""

                # Add properties if available
                if hasattr(element, "IsDefinedBy"):
                    props = ET.SubElement(elem, "Properties")
                    for definition in element.IsDefinedBy:
                        if hasattr(definition, "RelatingPropertyDefinition"):
                            prop_def = definition.RelatingPropertyDefinition
                            if hasattr(prop_def, "HasProperties"):
                                for prop in prop_def.HasProperties:
                                    if hasattr(prop, "NominalValue"):
                                        prop_elem = ET.SubElement(props, "Property")
                                        ET.SubElement(prop_elem, "Name").text = prop.Name
                                        ET.SubElement(prop_elem, "Value").text = str(prop.NominalValue.wrappedValue)

            # Write XML file
            tree = ET.ElementTree(root)
            tree.write(xml_path, encoding="utf-8", xml_declaration=True)

            return xml_path

        except Exception as e:
            logger.error(f"Error during XML generation: {str(e)}")
            raise