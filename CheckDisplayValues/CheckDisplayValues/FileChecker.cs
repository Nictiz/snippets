using Hl7.Fhir.ElementModel;
using Hl7.Fhir.Language.Debugging;
using Hl7.Fhir.Model;
using Hl7.Fhir.Serialization;
using Hl7.Fhir.Specification.Source;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace CheckDisplayValues
{
    public class FileChecker
    {
        public NTS nts;
        public const string NOTFOUNDINPACKAGE = "NotFoundInPackage";
        public int warningCount = 0;
        public int errorCount = 0;

        private List<DisplayValue>? displayValues;
        private ITypedElement? element;

        public FileChecker(NTS nts)
        {
            this.nts = nts;
        }

        /// <summary>
        /// Searches all SNOMED/LOINC codes in a file and finds the correct .display value
        /// </summary>
        /// <param name="file"></param>
        public void CheckFile(FileInfo file, List<string> packageNames)
        {
            this.displayValues = new List<DisplayValue>();

            if (!File.Exists(file.FullName) || !file.Name.EndsWith(".xml"))
            {
                Console.WriteLine($"{file.FullName} was not found or is not an .xml file");
                throw new FileNotFoundException();
            }

            string xmlString = System.IO.File.ReadAllText(file.FullName);
            if (xmlString.Contains("${DATE"))
            {
                xmlString = this.ReplaceTDate(xmlString);
            }
            if (xmlString.Contains("${"))
            {
                xmlString = this.ReplaceEncodings(xmlString);
            }

            var parser = new FhirXmlParser();

            Resource resource = parser.Parse<Resource>(xmlString);

            if (resource.TypeName == "Bundle") 
            {
                Bundle bundle = (Bundle)resource;
                foreach(Bundle.EntryComponent entry in bundle.Entry)
                {
                    SearchEntry(entry.Resource, file, packageNames);
                }
            }
            else 
            {
                SearchEntry(resource, file, packageNames);
            }
        }

        private void SearchEntry(Resource resource, FileInfo file, List<string> packageNames)
        {
            this.element = resource.ToTypedElement();

            CheckElement(element);

            //Only search packages and print if the file contains any codes
            if (this.displayValues.Count > 0 && resource.TypeName != "Binary")
            {
                SearchPackages(resource, packageNames);
                Printer printer = new(file.Name);

                Tuple<int, int> results = printer.PrintInconsistency(displayValues);
                warningCount += results.Item1;
                errorCount += results.Item2;
            }
        }

        /// <summary>
        /// Searched the required packages on any StructureDefinitions. The StructureDefinition is then searched to see if there are any valueSets required.
        /// </summary>
        /// <param name="resource"></param>
        private void SearchPackages(Resource resource, List<string> packageNames)
        {
            string profileUri = resource.Meta.Profile.FirstOrDefault("");

            FhirPackageSource resolver = new(packageNames.ToArray());

            StructureDefinition sd = resolver.FindStructureDefinition(profileUri);

            List<ElementDefinition> components = sd.Differential.Element;

            //for each component in the StructureDefinition.Differential.Element
            foreach(ElementDefinition component in components)
            {
                //If the component contains a binding
                if(component.Binding != null)
                {
                    //If the binding contains a valueset
                    if(component.Binding.ValueSet != null)
                    {
                        // If de binding is a ValueSet
                        if(!component.Binding.ValueSet.HasExtensions())
                        {
                            ResourceReference reference = (ResourceReference)component.Binding.ValueSet;
                            ValueSet vs = resolver.FindValueSet(reference.Url.ToString());
                            ReadValueSet(vs);
                        }
                        // If de binding is a ConceptMap
                        else if (component.Binding.ValueSet.HasExtensions())
                        {
                            ReadConceptMapAsync(component.Binding.ValueSet.Extension.First(), resolver);
                        }
                    }
                }
            }
        }

        /// <summary>
        /// Searches the packages on a specific valueSet and checks if it contains any bindings.
        /// </summary>
        /// <param name="component"></param>
        /// <param name="resolver"></param>
        private void ReadConceptMapAsync(Extension component, FhirPackageSource resolver)
        {
            string valueSetReference = component.Value.First().Value.ToString();

            // TODO awaiting MM-4198 (https://bits.nictiz.nl/browse/MM-4198)
            if (valueSetReference == "http://nictiz.nl/fhir/ConceptMap/InterpretatieVlaggenCodelijst-To-Observation-Interpretation")
            {
                valueSetReference = "http://nictiz.nl/fhir/ConceptMap/InterpretatieVlaggenCodelijst-to-observation-interpretation";
            }

            ConceptMap cm = resolver.ResolveByCanonicalUri(valueSetReference) as ConceptMap;

            // If ConceptMap was not found
            if (cm == null)
            {
                this.displayValues.Add(new DisplayValue(FileChecker.NOTFOUNDINPACKAGE, valueSetReference, null, null));
            }
            else
            {
                // For every element in the ConceptMap group
                foreach (ConceptMap.SourceElementComponent element in cm.Group.First().Element)
                {
                    // Check if the SourceElementComponent contains any codes which are already in displayValues. We don't want to check codes which aren't used.
                    if (displayValues.Any(x => x.code == element.Target.First().Code))
                    {
                        // If a code is used in the file, we add the given translation to displayValues. 
                        displayValues.First(x => x.code == element.Target.First().Code).displayCorrect.Add(new Translation()
                        {
                            Language = "nl",
                            Use = "ZiB",
                            Display = element.Target.First().Display
                        });
                    }
                }
            }
        }

        /// <summary>
        /// Reads a valueset and checks if there are any alternative SNOMED/LOINC codes
        /// </summary>
        /// <param name="vs"></param>
        private void ReadValueSet(ValueSet vs)
        {
            // We only need to check if there is a SNOMED or LOINC code, as we are only checking those displayValues
            ValueSet.ConceptSetComponent? snomedCodes = vs.Compose.Include.FirstOrDefault(x => x.System == "http://snomed.info/sct");
            ValueSet.ConceptSetComponent? loincCodes = vs.Compose.Include.FirstOrDefault(x => x.System == "http://loinc.org");

            if (snomedCodes != null)
            {
                CheckExternalCodes(snomedCodes);
            }
            else if (loincCodes != null)
            {
                CheckExternalCodes(loincCodes);
            }
        }

        /// <summary>
        /// Goes through the externalCodes and adds a new Translation to displayValues if the code is used
        /// </summary>
        /// <param name="externalCodes"></param>
        private void CheckExternalCodes(ValueSet.ConceptSetComponent? externalCodes)
        {
            foreach (ValueSet.ConceptReferenceComponent code in externalCodes.Concept)
            {
                if (displayValues.Any(x => x.code == code.Code))
                {
                    displayValues.First(x => x.code == code.Code).displayCorrect.Add(new Translation()
                    {
                        Language = "nl",
                        Use = "ZiB",
                        Display = code.Display
                    });
                }
            }
        }

        /// <summary>
        /// Recursive method to check every element and calls itself when ITypedElement has children
        /// </summary>
        /// <param name="element"></param>
        private void CheckElement(ITypedElement element)
        {
            if (element.Children().Any())
            {
                if (element.Name == "category" || element.Name == "coding")
                {
                    CompareValues(element);
                }
                else
                {
                    foreach (ITypedElement subElement in element.Children())
                    {
                        CheckElement(subElement);
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
        private void CompareValues(ITypedElement element)
        {

            if (element.InstanceType == "CodeableConcept")
            {
                CodeableConcept codeableconcept = (CodeableConcept)element.ToPoco();
                var code = codeableconcept.Coding.Find(c => c.System == "http://snomed.info/sct" || c.System == "http://loinc.org");
                if (code != null)
                {
                    displayValues?.Add(new DisplayValue(code.System, code.Code, code.Display, nts.GetDisplayListValue(code.Code, code.System)));
                }
            }
            else if (element.InstanceType == "Coding")
            {
                Coding coding = (Coding)element.ToPoco();
                if (coding.System == "http://snomed.info/sct" || coding.System == "http://loinc.org")
                {
                    displayValues?.Add(new DisplayValue(coding.System, coding.Code, coding.Display, nts.GetDisplayListValue(coding.Code, coding.System)));
                }
            }
            else if (element.InstanceType == "code")
            {
                Code code = (Code)element.ToPoco();
                if (code.Extension.Where(e => e.Value.TypeName == "CodeableConcept").Count() > 0)
                {
                    CodeableConcept? codeableconcept = code.Extension.Find(e => e.Value.TypeName == "CodeableConcept")?.Value as CodeableConcept;
                    var subCode = codeableconcept?.Coding.Find(c => c.System == "http://snomed.info/sct" || c.System == "http://loinc.org");
                    if (subCode != null)
                    {
                        displayValues?.Add(new DisplayValue(subCode.System, subCode.Code, subCode.Display, nts.GetDisplayListValue(subCode.Code, subCode.System)));
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
        /// Replaces all T-Dates to make the string parseable
        /// </summary>
        /// <param name="xmlString"></param>
        /// <returns></returns>
        private string ReplaceTDate(string xmlString)
        {
            int firstIndex = xmlString.IndexOf("\"${DATE");
            int lastIndex = firstIndex + 1;

            while (true) 
            {
                char nextCrar = xmlString[lastIndex];

                if(nextCrar.ToString() == "\"")
                {
                    string substring = xmlString.Substring(firstIndex, lastIndex - firstIndex);
                    xmlString = xmlString.Replace(substring, "\"2022-01-01");

                    if (xmlString.Contains("\"${DATE"))
                    {
                        xmlString = ReplaceTDate(xmlString);
                    }
                    break;
                }
                else
                {
                    lastIndex++;
                }
            }
            return xmlString;
        }
        
        /// <summary>
        /// Replaces all encodings to make the string parseable
        /// </summary>
        /// <param name="xmlString"></param>
        /// <returns></returns>
        private string ReplaceEncodings(string xmlString)
        {
            int firstIndex = xmlString.IndexOf("\"${");
            int lastIndex = firstIndex + 1;

            if (firstIndex == -1)
            {
                return xmlString;
            }

            while (true) 
            {
                char nextCrar = xmlString[lastIndex];

                if(nextCrar.ToString() == "\"")
                {
                    string substring = xmlString.Substring(firstIndex, lastIndex - firstIndex);
                    xmlString = xmlString.Replace(substring, "\"Encoded");

                    if (xmlString.Contains("\"${"))
                    {
                        xmlString = ReplaceEncodings(xmlString);
                    }
                    break;
                }
                else
                {
                    lastIndex++;
                }
            }
            return xmlString;
        }
    }
}
