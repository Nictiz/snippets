using Hl7.Fhir.ElementModel;
using Hl7.Fhir.Model;
using Hl7.Fhir.Serialization;
using Hl7.Fhir.Specification.Source;

namespace CheckDisplayValues
{
    public class FileChecker
    {
        ITypedElement? element;
        NTS nts;
        List<DisplayValue>? displayValues;

        public FileChecker()
        {
            this.nts = new();
        }

        public void CheckFile(FileInfo file)
        {
            this.displayValues = new List<DisplayValue>();
            if (File.Exists(file.FullName))
            {
                string xmlString = System.IO.File.ReadAllText(file.FullName);

                Console.WriteLine($"{file.Name}: ");
                var parser = new FhirXmlParser();

                Resource resource = parser.Parse<Resource>(xmlString);

                this.element = resource.ToTypedElement();

                CheckElement(element);

                CheckValueSets(resource);

                Printer.PrintInconsistency(displayValues);
            }
        }

        private void CheckValueSets(Resource resource)
        {
            string profileUri = resource.Meta.Profile.FirstOrDefault("");
            // TODO CheckDisplayValues
            // 1. search package for StructureDefinition
            // 2. Search StructureDefintion if valueSets are being used
            // 3. If valueset is used, search valueset if it contains a code which is also in the List<DisplayValue>

            FhirPackageSource resolver = new(new string[] { "..\\..\\..\\Packages\\nictiz.fhir.nl.stu3.zib2017-2.2.8.tgz", "..\\..\\..\\Packages\\nictiz.fhir.nl.stu3.eafspraak-1.0.6.tgz" });

            StructureDefinition sd = resolver.FindStructureDefinition(profileUri);

            List<ElementDefinition> components = sd.Differential.Element;

            foreach(ElementDefinition component in components)
            {
                if(component.Binding != null)
                {
                    if(component.Binding.ValueSet != null)
                    {
                        string valueSetReference = component.Binding.ValueSet.First().Value.ToString();

                        if (component.Binding.ValueSet.Extension.Count == 0)
                        {
                            ValueSet vs = resolver.FindValueSet(valueSetReference);

                            ValueSet.ConceptSetComponent? snomedCodes = vs.Compose.Include.FirstOrDefault(x => x.System == "http://snomed.info/sct");
                            ValueSet.ConceptSetComponent? loincCodes = vs.Compose.Include.FirstOrDefault(x => x.System == "http://loinc.org");

                            if (snomedCodes != null)
                            {
                                CheckExternalCodes(snomedCodes);
                            } else if(loincCodes != null)
                            {
                                CheckExternalCodes(loincCodes);
                            }
                        }
                        else
                        {

                        }

                    }
                }
            }

        }

        private void CheckExternalCodes(ValueSet.ConceptSetComponent? externalCodes)
        {
            foreach (ValueSet.ConceptReferenceComponent code in externalCodes.Concept)
            {
                if (displayValues.Any(x => x.code == code.Code))
                {
                    if (displayValues.First(x => x.code == code.Code).displayCurrent != code.Designation.First().Value)
                    {
                        displayValues.First(x => x.code == code.Code).displayCorrect.Add(new Translation()
                        {
                            Language = "nl",
                            Use = "ZiB",
                            Display = code.Designation.First().Value
                        });
                    }
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
                    displayValues?.Add(new DisplayValue(code.System, code.Code, code.Display, nts.GetDisplayListValue(code.Code, code.System), ""));
                }
            }
            else if (element.InstanceType == "Coding")
            {
                Coding coding = (Coding)element.ToPoco();
                if (coding.System == "http://snomed.info/sct" || coding.System == "http://loinc.org")
                {
                    displayValues?.Add(new DisplayValue(coding.System, coding.Code, coding.Display, nts.GetDisplayListValue(coding.Code, coding.System), ""));
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
                        displayValues?.Add(new DisplayValue(subCode.System, subCode.Code, subCode.Display, nts.GetDisplayListValue(subCode.Code, subCode.System), ""));
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
    }
}
