# BaseResourceToSpreadsheet

Een simpel Python-scriptje om een FHIR base-resource te converteren naar een Excel-spreadsheet en daar de kolommen aan toe te voegen die nodig zijn voor het maken van het afsprakenmodel. Het formaat is gebaseerd op https://confluence.hl7.org/spaces/FHIR/pages/35718548/FHIR+Spreadsheet+Authoring, maar niet alles hiervan wordt meegenomen in de output.

De default actie van het script is om alle R4-resources als spreadsheet uit te spugen.

De output wordt weggeschreven op een tabblad genaamd "Content". Het scriptje kan data-validatie op bepaalde kolommen zetten:
* In het bestand template.xlsx moet een tabblad zijn opgenomen met de mogelijke waarden voor data-validatie. De eerste rij wordt als header-rij beschouwd.
* Dit tabblad moet de naam hebben "Legenda" + de kolomnaam waarop data-validatie moet worden toegepast, aan elkaar geschreven. Als er een ":" in de kolomnaam staat, wordt alleen het deel voor de dubbele punt meegenomen.
* Dit zorgt ervoor dat het tabblad wordt gekopieerd naar het gegenereerde bestand en dat de datavalidatie wordt toegepast op de desbetreffende kolom.