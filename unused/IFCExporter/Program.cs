using Autodesk.Revit.UI;
using RevitExporter;
using Document = Autodesk.Revit.DB.Document;

namespace IFCExporter
{
    class Program
    {
        static void Main(string[] args)
        {
            // Check if the user provided the Revit file path
            if (args.Length != 1)
            {
                Console.WriteLine("Usage: Program <Revit Project File Path>");
                return;
            }

            string revitFilePath = args[0];

            // Check if the Revit file exists
            if (!File.Exists(revitFilePath))
            {
                Console.WriteLine("The specified Revit file does not exist.");
                return;
            }

            try
            {
                // Initialize Revit application and document
                UIApplication uiapp = new UIApplication(new UIApplication(null)); // Placeholder for Revit app instance
                Document doc = uiapp.Application.OpenDocumentFile(revitFilePath);

                // Create an instance of the Exporter
                Exporter exporter = new Exporter();

                // Run the export process
                string result = exporter.ExportIFC(doc);
                Console.WriteLine(result);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
            }
        }
    }
}
