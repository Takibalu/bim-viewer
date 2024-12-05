using Autodesk.Revit.DB;
using System;
using System.IO;

namespace RevitExporter
{
    public class Exporter
    {
        public string ExportIFC(Document doc)
        {
            try
            {
                // Create IFC export options
                IFCExportOptions ifcOptions = new IFCExportOptions()
                {
                    FileVersion = IFCVersion.IFC2x3,          // or IFC4 depending on requirements
                    SpaceBoundaryLevel = 2,                   // 0, 1, or 2
                    ExportBaseQuantities = true,              // Export base quantities for elements
                    WallAndColumnSplitting = true,            // Split walls and columns at story levels
                    FilterViewId = ElementId.InvalidElementId // Export entire model
                };

                // Set export folder path
                string exportPath = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.Desktop),
                    "RevitExport"
                );

                // Create directory if it doesn't exist
                Directory.CreateDirectory(exportPath);

                // Generate filename with timestamp
                string timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                string filename = $"{doc.Title}_{timestamp}.ifc";
                string fullPath = Path.Combine(exportPath, filename);

                // Export to IFC
                doc.Export(exportPath, filename, ifcOptions);

                // Return success message
                return $"IFC file exported successfully to:\n{fullPath}";
            }
            catch (Exception ex)
            {
                // Return failure message
                return $"Export Failed: {ex.Message}";
            }
        }
    }
}
