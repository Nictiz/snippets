using Hl7.Fhir.ElementModel;
using Hl7.Fhir.Model;
using Hl7.Fhir.Serialization;
using Hl7.Fhir.Specification.Source;
using Code = Hl7.Fhir.Model.Code;

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

        /// <summary>
        /// Searches all SNOMED/LOINC codes in a file and finds the correct .display value
        /// </summary>
        /// <param name="file"></param>
        public void CheckFile(FileInfo file, List<string> packageNames)
        {
            this.displayValues = new List<DisplayValue>();
            if (File.Exists(file.FullName))
            {
                string xmlString = System.IO.File.ReadAllText(file.FullName);

                var parser = new FhirXmlParser();

                Resource resource = parser.Parse<Resource>(xmlString);

                this.element = resource.ToTypedElement();

                CheckElement(element);

                SearchPackages(resource, packageNames);
                Printer printer = new(file.Name);

                printer.PrintInconsistency(displayValues);
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
                        string valueSetReference = component.Binding.ValueSet.First().Value.ToString();

                        //
                        if (component.Binding.ValueSet.Extension.Count == 0)
                        {
                            ValueSet vs = resolver.FindValueSet(valueSetReference);
                            ReadValueSet(vs);
                            
                        }
                        else
                        {
                            CheckValueSet(component, resolver);
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
        private void CheckValueSet(ElementDefinition component, FhirPackageSource resolver)
        {
            string valueSetReference = component.Binding.ValueSet.Extension.First().Value.First().Value.ToString();
            ConceptMap cm = (ConceptMap)resolver.ResolveByCanonicalUri(valueSetReference);
            if (cm == null)
            {
                this.displayValues.Add(new DisplayValue("Validation", valueSetReference, null, null, null));
                //Console.WriteLine($"Could not find {valueSetReference}");
            }
            else
            {
                ValueSet vs = resolver.FindValueSet(cm.Source.First().Value.ToString());
                if (vs != null)
                    ReadValueSet(vs);
                else
                {
                    foreach (ConceptMap.SourceElementComponent element in cm.Group.First().Element)
                    {
                        if (displayValues.Any(x => x.code == element.Target.First().Code))
                        {
                            if (displayValues.First(x => x.code == element.Target.First().Code).displayCurrent != element.Target.First().Display)
                            {
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
            }
        }

        /// <summary>
        /// Reads a valueset and checks if there are any alternative SNOMED/LOINC codes
        /// </summary>
        /// <param name="vs"></param>
        private void ReadValueSet(ValueSet vs)
        {
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
