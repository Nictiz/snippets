# BaseResourceToSpreadsheet

Collectie van scriptjes om FHIR base-resources te converteren naar Excel en daar de kolommen aan toe te voegen die nodig zijn voor het maken van het afsprakenmodel. Het formaat is gebaseerd op https://confluence.hl7.org/spaces/FHIR/pages/35718548/FHIR+Spreadsheet+Authoring, maar niet alles hiervan wordt meegenomen in de output.

De folder bevat twee Python-classes:
* baseresourcetospreadsheet.BaseResourceToSpreadSheet: deze class haalt de StructureDefinition van een bepaalde resource op en converteert deze naar Excel.
* templatemixer.TemplateMixer: deze class kan een spreadsheet samenvoegen met een template:
    * Alle tabbladen genaamd "LegendaXXX" worden gekopieerd en gebruikt als data-validatie voor de kolom "XXX".
    * Alle tabbladen genaamd "MappingYYY" worden gebruikt om de teksten in kolom YYY te herschrijven. (Kolom 1 op dit tabblad is de verwachting, kolom 2 is wat het wordt. Er mogen meerdere waarden in de input staan, gescheiden door komma's. De input mag ook een specificatie hebben met haakjes, die wordt gekopieerd naar de output).

Het scriptje "R4ToSpreadsheet.py" converteert alle FHIR R4-resources naar spreadsheets en voegt ze samen met "template.xslx" in deze folder. Dit template bevat de dingen die nodig zijn voor het maken van het afsprakenmodel.