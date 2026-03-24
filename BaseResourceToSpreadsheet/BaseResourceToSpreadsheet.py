import copy
import json
import openpyxl
import pandas as pd
import pathlib
import requests
import shutil

from openpyxl.worksheet.datavalidation import DataValidation

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

        # Make header row bold
        workbook = openpyxl.load_workbook(out_file)
        sheet = workbook["Structure"]
        for cell in sheet[1]:
            cell.font = openpyxl.styles.Font(bold=True)
        workbook.save(out_file)

        return out_file

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

class DataValidationAdder:
    def __init__(self, template_path):
        self.template = openpyxl.load_workbook(pathlib.Path(template_path))

    def addValidation(self, workbook_path):
        workbook = openpyxl.load_workbook(workbook_path)
        headers = {cell.value: cell.column_letter for cell in workbook["Structure"][1]}
        for header in headers:
            legend_name = "Legenda" + header.capitalize()
            if legend_name in self.template:
                self.__copySheet__(workbook, legend_name)
                self.__addDataValidation__(workbook, legend_name, headers[header])

        workbook.save(workbook_path)

    def __copySheet__(self, workbook, sheet_name):
        new_sheet = workbook.create_sheet(sheet_name)
        for row in self.template[sheet_name].iter_rows():
            for cell in row:
                new_cell = new_sheet[cell.coordinate]
                new_cell.value = cell.value

                if cell.has_style:
                    new_cell.font = copy.copy(cell.font)
                    new_cell.border = copy.copy(cell.border)
                    new_cell.fill = copy.copy(cell.fill)
                    new_cell.number_format = cell.number_format
                    new_cell.protection = copy.copy(cell.protection)
                    new_cell.alignment = copy.copy(cell.alignment)

    def __addDataValidation__(self, workbook, legend_name, column):
        max_row = len(list(workbook[legend_name].rows))

        # Assume the first row is the header row, and data is in the first col
        formula = f"={legend_name}!$A$2:$A${max_row + 1}"
        dv = DataValidation(
            type="list",
            formula1=formula,
            allow_blank=True
        )
        workbook["Structure"].add_data_validation(dv)
        dv.add(f"{column}2:{column}1000")

        # Also add conditional formatting based on the colors in the source sheet
        default_style = workbook[legend_name].cell(1, 3).fill
        for row in range(2, max_row + 3):
            cell = workbook[legend_name].cell(row, 1)
            if (cell.fill.fgColor.rgb != "00000000"):
                rule = openpyxl.formatting.rule.CellIsRule(
                    operator="equal",
                    formula=[f'{legend_name}!${cell.column_letter}${cell.row}'],
                    fill=openpyxl.styles.PatternFill(start_color=cell.fill.fgColor.rgb, end_color=cell.fill.fgColor.rgb, fill_type="solid")
                )
                workbook["Structure"].conditional_formatting.add(f"{column}2:{column}1000", rule)

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
    dv_adder = DataValidationAdder("template.xlsx")
    out_path = converter.convert("Observation")
    dv_adder.addValidation(out_path)
    # for resource in R4_resources:
        # converter.convert(resource)