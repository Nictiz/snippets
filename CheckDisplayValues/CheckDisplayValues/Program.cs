using Hl7.Fhir.Serialization;
using Hl7.Fhir.Model;
using Hl7.Fhir.ElementModel;
//using Vonk.Core.Common;

namespace CheckDisplayValues
{
    public class Program
    {
        public static void Main()
        {
            DirectoryInfo d = new DirectoryInfo("..\\..\\..\\Source");
            DirectoryInfo packages = new DirectoryInfo("..\\..\\..\\Packages");

            FileChecker fileChecker = new FileChecker();

            List<string> packageNames = new();

            foreach(FileInfo package in packages.GetFiles("*.tgz"))
            {
                packageNames.Add(package.FullName);
            }

            foreach (FileInfo file in d.GetFiles("*.xml"))
            {
                fileChecker.CheckFile(file, packageNames);
            }
        }
    }
}