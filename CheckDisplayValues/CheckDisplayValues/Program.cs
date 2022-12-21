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

            FileChecker fileChecker = new FileChecker();

            foreach (FileInfo file in d.GetFiles("*.xml"))
            {
                fileChecker.CheckFile(file);
            }
        }
    }
}