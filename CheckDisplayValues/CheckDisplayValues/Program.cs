using Hl7.Fhir.Serialization;
using Hl7.Fhir.Model;
using Hl7.Fhir.ElementModel;
using Vonk.Core.Common;

namespace CheckDisplayValues
{
    public class Program
    {
        private static NTS nts;

        public static void Main()
        {
            nts = new();

            DirectoryInfo d = new DirectoryInfo("..\\..\\..\\Source");
            foreach (FileInfo file in d.GetFiles("*.xml"))
            {
                CheckResources(file);
            }
        }

        /// <summary>
        /// Main method to check all resources
        /// </summary>
        /// <param name="file"></param>
        private static void CheckResources(FileInfo file)
        {
            if (File.Exists(file.FullName))
            {
                string xmlString = System.IO.File.ReadAllText(file.FullName);

                Console.WriteLine($"{file.Name}: ");
                var parser = new FhirXmlParser();
                
                Resource resource = parser.Parse<Resource>(xmlString);

                ITypedElement element = resource.ToTypedElement();

                checkElement(element);
            }
        }

        /// <summary>
        /// Recursive method to check every element and calls itself when ITypedElement has children
        /// </summary>
        /// <param name="element"></param>
        private static void checkElement(ITypedElement element)
        {
            var test = element.Children().Count();

            if(element.Children().Count() > 0)
            {
                if(element.Name == "category" || element.Name == "coding")
                {
                    CompareValues(element);
                }
                else
                {
                    foreach (ITypedElement subElement in element.Children())
                    {
                        checkElement(subElement);
                    }
                }
            }
            else
            {
                if (element.Name == "category" || element.Name == "coding")
                {
                    CompareValues(element);
                }
            }
        }

        /// <summary>
        /// Converts ITypedElement to the right FHIR resources and compares them to the display value in the NTS
        /// </summary>
        /// <param name="element"></param>
        private static void CompareValues(ITypedElement element)
        {
            if (element.InstanceType == "CodeableConcept")
            {
                CodeableConcept codeableconcept = (CodeableConcept)element.ToPoco();
                var code = codeableconcept.Coding.Find(c => c.System == "http://snomed.info/sct" || c.System == "http://loinc.org");
                if (code != null)
                {
                    PrintMessage(code.Display, nts.GetDisplayListValue(code.Code, code.System), code.Code);
                }
            }else if(element.InstanceType == "Coding")
            {
                Coding coding = (Coding)element.ToPoco();
                if(coding.System == "http://snomed.info/sct" || coding.System == "http://loinc.org")
                {
                    PrintMessage(coding.Display, nts.GetDisplayListValue(coding.Code, coding.System), coding.Code);
                }
            }else if(element.InstanceType == "code")
            {
                Code code = (Code)element.ToPoco();
                if(code.Extension.Where(e => e.Value.TypeName == "CodeableConcept").Count() > 0)
                {
                    CodeableConcept codeableconcept = (CodeableConcept)code.Extension.Find(e => e.Value.TypeName == "CodeableConcept")?.Value;
                    var subCode = codeableconcept.Coding.Find(c => c.System == "http://snomed.info/sct" || c.System == "http://loinc.org");
                    if (subCode != null)
                    {
                        PrintMessage(subCode.Display, nts.GetDisplayListValue(subCode.Code, subCode.System), subCode.Code);
                        // List<Translation> translations = nts?.GetDisplayListValue(code.Code, code.System);
                    }
                }
                else
                {
                    Console.WriteLine($"{element.InstanceType} not implemented yet");
                }
            }
            else
            {
                Console.WriteLine($"{element.InstanceType} not implemented yet");
            }
        }

        /// <summary>
        /// Checks if display is in one of the available NTS values
        /// </summary>
        /// <param name="original"></param>
        /// <param name="nts"></param>
        /// <param name="code"></param>
        private static void PrintMessage(string original, List<Translation> nts, string code)
        {
            if(nts.Where(t => t.Language.Contains("nl")).Count() > 0)
            {
                List<Translation> language = nts.FindAll(t => t.Language.Contains("nl"));

                if (language.Where(t => t.Display.ToLower() == original.ToLower()).Count() == 0)
                {
                    PrintMessage(original, (language.Find(t=>t.Use == "Fully specified name") ?? language.Find(t => t.Use == "display") ?? language.Find(t => t.Use == "Preferred For Language")).Display, code);
                }
            }
            else if (nts.Where(t => t.Language.Contains("en")).Count() > 0)
            {
                List<Translation> language = nts.FindAll(t => t.Language.Contains("en"));

                if (language.Where(t => t.Display.ToLower() == original.ToLower()).Count() == 0)
                {
                    PrintMessage(original, (language.Find(t => t.Use == "Preferred For Language") ?? language.Find(t => t.Use == "display") ?? language.Find(t => t.Use == "Fully specified name")).Display, code);
                }
            }
            else
            {
                PrintMessage(original, "", code);
            }
        }

        /// <summary>
        /// Print message if strings are not equal
        /// </summary>
        /// <param name="original"></param>
        /// <param name="nts"></param>
        /// <param name="code"></param>
        private static void PrintMessage(string original, string nts, string code)
        {
            if (original.ToLower() != nts.ToLower())
            {
                Console.Write($"        {code}:\"{original}\" Should be:\"{nts}\"");
                if (nts.Equals(""))
                {
                    Console.Write(" WARNING!: No translation available, please check manually");
                }
                Console.WriteLine("");
            }
        }
    }
}