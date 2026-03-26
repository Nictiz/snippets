import json
import openpyxl
import pandas as pd
import pathlib
import requests

class BaseResourceToSpreadsheet:
    COLUMNS = ["Element", "Aliases", "Card", "Type", "Binding", "Additional binding", "Definition", "Requirements", "Dekking", "Aanvullende informatie", "Obligations: Registrerend systeem", "Obligations: Ontsluitend systeem", "Obligations: Verwerkend systeem"]

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
            df.loc[len(df)] = [path, "", card, types, "", "", definition, "", "", "", "", "", ""]

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

