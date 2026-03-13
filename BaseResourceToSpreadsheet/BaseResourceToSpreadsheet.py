import json
import pandas as pd
import pathlib
import requests
import shutil

class BaseResourceToSpreadsheet:
    COLUMNS = ["Element", "Aliases", "Card", "Type", "Binding", "Definition", "Requirements", "Dekking", "Aanvullende informatie"]

    def __init__(self, fhir_version, output_folder):
        self.fhir_version = fhir_version
        self.output_folder = pathlib.Path(output_folder)
    
    def convert(self, resource_name):
        sd = self.__downloadJSON__(resource_name)
        
        data = self.__sdToDataframe__(sd)
        
        out_file = self.output_folder / f"{resource_name}.xlsx"
        with pd.ExcelWriter(out_file) as writer:
            data.to_excel(writer, sheet_name = "Structure", index = False)

    def __downloadJSON__(self, resource_name):
        url = f"https://www.hl7.org/fhir/{self.fhir_version.upper()}/{resource_name.lower()}.profile.json"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Couldn't download from '{url}'")

        decoder = json.JSONDecoder()
        return decoder.decode(response.content.decode("utf-8"))

    def __sdToDataframe__(self, sd):
        df = pd.DataFrame(columns = self.COLUMNS)
        diff = sd["differential"]
        for el in diff["element"]:
            path = el["path"]
            card = f"{el["min"]}..{el["max"]}"
            types = self.__typeToTypeString__(el["type"]) if "type" in el else "Resource"
            definition = el["definition"]
            df.loc[len(df)] = [path, "", card, types, "", definition, "", "", ""]

        return df

    def __typeToTypeString__(self, type_array):
        types = []
        for t in type_array:
            if t["code"] == "Reference":
                type_string = "Reference"
                if "targetProfile" in t:
                    type_string += "(" + "|".join([p.replace("http://hl7.org/fhir/StructureDefinition/", "") for p in t["targetProfile"]]) + ")"
                types.append(type_string)
            else:
                types.append(t["code"])

        return ", ".join(types)

if __name__ == "__main__":
    R4_resources = [
        "Account",
        "ActivityDefinition",
        "AdverseEvent",
        "AllergyIntolerance",
        "Appointment",
        "AppointmentResponse",
        "AuditEvent",
        "Basic",
        "Binary",
        "BiologicallyDerivedProduct",
        "BodyStructure",
        "Bundle",
        "CapabilityStatement",
        "CarePlan",
        "CareTeam",
        "CatalogEntry",
        "ChargeItem",
        "ChargeItemDefinition",
        "Claim",
        "ClaimResponse",
        "ClinicalImpression",
        "CodeSystem",
        "Communication",
        "CommunicationRequest",
        "CompartmentDefinition",
        "Composition",
        "ConceptMap",
        "Condition",
        "Consent",
        "Contract",
        "Coverage",
        "CoverageEligibilityRequest",
        "CoverageEligibilityResponse",
        "DetectedIssue",
        "Device",
        "DeviceDefinition",
        "DeviceMetric",
        "DeviceRequest",
        "DeviceUseStatement",
        "DiagnosticReport",
        "DocumentManifest",
        "DocumentReference",
        "EffectEvidenceSynthesis",
        "Encounter",
        "Endpoint",
        "EnrollmentRequest",
        "EnrollmentResponse",
        "EpisodeOfCare",
        "EventDefinition",
        "Evidence",
        "EvidenceVariable",
        "ExampleScenario",
        "ExplanationOfBenefit",
        "FamilyMemberHistory",
        "Flag",
        "Goal",
        "GraphDefinition",
        "Group",
        "GuidanceResponse",
        "HealthcareService",
        "ImagingStudy",
        "Immunization",
        "ImmunizationEvaluation",
        "ImmunizationRecommendation",
        "ImplementationGuide",
        "InsurancePlan",
        "Invoice",
        "Library",
        "Linkage",
        "List",
        "Location",
        "Measure",
        "MeasureReport",
        "Media",
        "Medication",
        "MedicationAdministration",
        "MedicationDispense",
        "MedicationKnowledge",
        "MedicationRequest",
        "MedicationStatement",
        "MedicinalProduct",
        "MedicinalProductAuthorization",
        "MedicinalProductContraindication",
        "MedicinalProductIndication",
        "MedicinalProductIngredient",
        "MedicinalProductInteraction",
        "MedicinalProductManufactured",
        "MedicinalProductPackaged",
        "MedicinalProductPharmaceutical",
        "MedicinalProductUndesirableEffect",
        "MessageDefinition",
        "MessageHeader",
        "MolecularSequence",
        "NamingSystem",
        "NutritionOrder",
        "Observation",
        "ObservationDefinition",
        "OperationDefinition",
        "OperationOutcome",
        "Organization",
        "OrganizationAffiliation",
        "Parameters",
        "Patient",
        "PaymentNotice",
        "PaymentReconciliation",
        "Person",
        "PlanDefinition",
        "Practitioner",
        "PractitionerRole",
        "Procedure",
        "Provenance",
        "Questionnaire",
        "QuestionnaireResponse",
        "RelatedPerson",
        "RequestGroup",
        "ResearchDefinition",
        "ResearchElementDefinition",
        "ResearchStudy",
        "ResearchSubject",
        "RiskAssessment",
        "RiskEvidenceSynthesis",
        "Schedule",
        "SearchParameter",
        "ServiceRequest",
        "Slot",
        "Specimen",
        "SpecimenDefinition",
        "StructureDefinition",
        "StructureMap",
        "Subscription",
        "Substance",
        "SubstancePolymer",
        "SubstanceProtein",
        "SubstanceReferenceInformation",
        "SubstanceSpecification",
        "SubstanceSourceMaterial",
        "SupplyDelivery",
        "SupplyRequest",
        "Task",
        "TerminologyCapabilities",
        "TestReport",
        "TestScript",
        "ValueSet",
        "VerificationResult",
        "VisionPrescription",
    ]

    converter = BaseResourceToSpreadsheet("R4", ".")
    for resource in R4_resources:
        converter.convert(resource)