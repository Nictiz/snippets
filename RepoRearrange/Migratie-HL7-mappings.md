# Migreren ADA-repository van Cloudforge naar Github

## Achtergrond

Nictiz wil in toenemende mate ADA (ART DECOR Applications) gebruiken. ADA specificeert een 'neutraal' XML-formaat voor berichten gebaseerd op datasets gespecificeerd in ART-DECOR, en genereert onder meer GUI's om dit soort berichten aan te maken en XML Schema's om dit soort berichten te controleren.
Twee directe toepassingen hiervan zijn:
- omzetten van berichten die op verschillende standaarden gebaseerd zijn (bv. HL7 v3 naar FHIR)
- invoeren van testscripts door IA's die omgezet kunnen worden naar technische kwalificatiescripts
- (genereren documentatie)

De adoptie van ADA speelt zich af tegen de achtergrond van een professionaliseringsslag die Nictiz moet maken vanwege de sterk toegenomen last voor kwalificatie (MedMij PGO's) en de bijbehorende groei van het team. Het gebruik van ADA kan hierin een bijdrage leveren door:
- de testscripts van de IA's direct te kunnen inzetten voor kwalificatie
- handwerk (foutgevoelig en tijdrovend) voor het aanmaken en mn. aanpassen van scripts overbodig te maken
- consistentere resultaten op te leveren
- documentatie te genereren
- een basis te bieden voor automatisering van de processen

Tegelijkertijd bestaat de wens om ontwikkeling en beheer van de ADA-applicaties te professionaliseren. De keus voor een versiebeheersysteem en hosting hiervan zijn hiervoor bepalend. De huidige situatie beperkt wat we hiermee kunnen doen.

### Wat er beheerd moet worden

ADA-applicaties [sic] zijn gebaseerd op XML. Ze bouwen berichtenformaten in XML op, op basis van de gegevens in een ART-DECOR-server. Hiervoor is het nodig om een project met verwijzing naar desbetreffende server te definiëren - in XML uiteraard.

Via een reeks XML-transformaties worden hieruit berichten-schema's, lege voorbeeldberichten en GUI's gegenereerd. Deze kunnen vervolgens naar een ART-DECOR-server ontsloten worden.

De projectdefinitie, schema's, voorbeeldberichten en gui's vormen het eerste deel van wat we in een versiebeheersysteem willen beheren.

Via de GUI's kunnen instances van ADA-berichten worden aangemaakt en in XML worden gedownload. De ADA-berichten kunnen via XSLT-transformaties worden omgezet in diverse andere formaten zoals CDA, HL7 v3, FHIR, Wiki, etc. De XSLT-shylesheets worden met de hand geschreven. De ADA-voorbeeldberichten en XSLT-bestanden zijn het tweede deel van wat we willen beheren in een versiebeheersysteem.

### Huidige situatie: Subversion/Cloudforge

Als versiebeheersysteem gebruiken we momenteel Subversion. Dit systeem kent een lange geschiedenis en werd tot enkele jaren terug breed ingezet, met name in de opensource-gemeenschap.

Er is wel wat vervuiling opgetreden. Zo is in een normaal Subversion-repo de map 'branches' bedoeld voor branches vanaf de 'trunk' ('master' in Git-termen). In ons repo is deze map gevuld met kwalificatiemateriaal voor V7 van de verschillende projecten.

Als repository gebruiken we Cloudforge. Het Nictiz-project  is afgeschermd voor niet-leden.

## Wensen en eisen

### Moderne mogelijkheden

De afgelopen jaren heeft Git pijlsnel terrein gewonnen als versiebeheersysteem, met goede redenen. Een fundamenteel verschil met Subversion en andere oudere VCS'en is Git *decentraal* is, wat wil zeggen dat elke werkkopie 'volwaardig' is ipv. dat alleen de server volwaardig is. Dit maakt het weer mogelijk om complexere dingen te doen op een lokale machine. Zo moedig Git het aan om 'topic branches' te maken voor elke bugfix of nieuwe feature.

Hand in hand met de opkomst van Git is het idee van de *pull request* in zwang geraakt: een verzoek van een ontwikkelaar aan een beheerder om zijn/haar topic branch te mergen. Dit mechanisme is ook weer zijn eigen leven gaan leiden waarbij hostingplatforms uitgebreide mogelijkheden bieden om reviews uit te voeren en dingen te wijzigen voordat een PR wordt goedgekeurd.

Tegelijkertijd is ook de praktijk van _continuous integration_ opgekomen, de mogelijkheid om automatisch allerhande unit- en integratietests en build-stappen af te trappen bij een commit of het aanmaken van een PR. Tegenwoordig is het goed gebruik om elke PR te onderwerpen aan een geautomatiseerde reeks testen. Dit komt de kwaliteit van de opgeleverde software ten goede en zorgt ervoor dat fouten eerder in het ontwikkelproces gevangen worden.

### Packages/releases

- Hoe kan je een release maken van bv. ketenzorg waar alleen het materiaal van ketenzorg zit?

## Plan van aanpak

### Opschonen en herindelen repo

De indeling van het repository is in de loop der tijd wat vervuild geraakt. Wanneer dit naar een publieke locatie gaat, moet dit netjes gemaakt worden:
- branches: deze map hoort eigenlijk de branches van de SVN-repo te bevatten, maar dit is misbruikt voor het onderbrengen van ART-DECOR-publicaties(?)
- publicaties: deze map bevat alleen een README over dat hier publicaties in zitten. Ws. was het de bedoeling dat de inhoud van 'branches' hierin terecht kwam. Dit is al vroeg in de geschiedenis van de repo zo opgezet, maar lijkt nooit gebruikt te zijn.
- tags: deze map hoort de tags van de SVN-repo te bevatten, hier is geen gebruik van gemaakt.
- trunk:
	- mappings: de XSLT's en bijbehorende infrastructuur om berichten te vertalen tussen formaten. Bevat nu ook enkele build-scripts
		- ada_2_fhir
			- _projectmappen_
			- fhir: bevat algemene functionaliteit voor ADA-naar-FHIR-transformaties
		- ada_2_hl7:
			- _projectmappen_
			- hl7: bevat algemene functionaliteit voor ADA-naar-HL7-transformaties
			- tools_internal
		- ada_2_test-xslt: iets testerigs van Arianne, onduidelijk gedocumenteerd
		- ada_2_wiki: conversie van ADA naar wiki-*tabellen*
		- ada_community: _is me nog niet helemaal duidelijk_
		- documentatie: nog een folder voor conversie van ADA naar wiki-*tabellen*
		- hl7_2_ada:
			- _projectmappen_
			- hl7: bevat algemene functionaliteit voor HL7-naar-ADA-transformaties
		- hl7_2_fhir
		- publicaties: bevat releases, gebundelde mappen met XSLT's die derden kunnen gebruiken
		- util: generieke XSLT-functies en -templates die in verschillende projecten gebruikt kunnen worden
	- projects: de ADA-projectdefinities met de bijbehorende gegeneerde artefacten. Deze hebben een directe link met de data in ART-DECOR.

In de projectmappen onder trunk/mappings zijn ook genereerde gegevens opgeslagen die vanuit de trunk/projects/... mappen worden gekopieerd. Verder worden instances gemaakt met de ADA-frontend daar opgeslagen.

De vraag is of de ADA-projectdefinities en de mappings eigenlijk wel in dezelfde repo horen. Het zijn conceptueel wel verschillende dingen. De projectdefinities zijn ook niet zo interessant voor de buitenwereld. Aan de andere kant zijn ze aan elkaar gerelateerd. De mappings gebruiken gegenereerde schema's en andere artefacten in de projects. Het is ook niet zo dat mappings los gezien kunnen worden van de ART-DECOR-server. Voorstel is om ze in ieder geval voor nu bij elkaar te houden.

- branches:*dit kunnen Github-releases worden, de map kan weg*
- publicaties: *verwijderen*
- tags: *verwijderen*
- trunk: *wordt de root van de Git-repo*
	- mappings
		- ada_2_fhir
			- fhir: inhoud verplaatsen naar util
		- ada_2_hl7
			- hl7: inhoud verplaatsen naar util
			- tools_internal: inhoud verplaatsen naar util
		- ada_2_test-xslt: *verplaatsen naar branch met die naam, verwijderen uit master*
		- ada_2_wiki
		- ada_community: *weet ik even niet*
		- documentatie: samenvoegen met ada_2_wiki?
		- hl7_2_ada
		- hl7_2_fhir
		- publicaties: dit kunnen Github-releases worden. *De map kan weg*
		- util: dit zou een map met algemene functionaliteit voor _alle_ mappings kunnen worden.
	- projects

Bij het verplaatsen van de bestanden naar de util-map, moeten bestaande XSLT's worden aangepast met de nieuwe verwijzing. Ik zou verdere refactoring van bestaande projectmappen achterwege laten, dit heeft weinig geen meerwaarde en zou alleen maar tijd vergen. Op het moment dat er weer gewerkt gaat worden met zo'n map, zou daar natuurlijk wel naar gekeken kunnen worden.

Vervolgens moeten alle ReadMe's worden nagelopen om te kijken of ze nog up-to-date zijn.
	
### Migratie naar Git

Git biedt een ingebouwd mechanisme om Subversion-repo's te lezen en er zelfs mee te interacteren. De initiële versie duurt wel even: een testrun nam ruim vijf uur in beslag (als 'trunk' gebruikt wordt als basis, is het ruim een uur).

Vanwege de afwijkende layout is het verstandig om de 'trunk' als basis te gebruiken voor de git-repo. Branches en tags hebben binnen ons SVN-repo geen betekenis, dus die kunnen we laten zitten. Willen we ook de auteurs mappen (en dat willen we), dan moeten we een mapping-bestandje meegeven (zie hieronder). Het commando wordt dan:

  git svn clone 'https://nictiz.svn.cloudforge.com/art_decor' -T trunk --no-metadata -A .authors-transform.txt

Let op! De `--no-metadata`-optie maakt het onmogelijk om nog terug te syncen naar de SVN-repo, het is dus eenrichtingsverkeer.

Vervolgens maken we de 'mappings'-map de basis voor ons nieuwe repo.
  
  git filter-branch --prune-empty --subdirectory-filter ada-data/mappings/ master
  
Hierna kunnen we de 'ada-data'-map weggooien.

### Samenvoegen met ada-2-fhir-noobs

De tijdelijke git-repo ada-2-fhir-noobs volgt dezelfde structuur als ons nieuwe repo en kan er gewoon mee samengevoegd worden. Helaas is er in de tussentijd het een en ander geklust aan de main repo:
- zibs2017 bevat een bestand zibs2017.xsl waarin verschillende zibs + omliggende infrastructuur is gestopt
- enkele core-profielen zijn terechtgekomen in 'fhir'
Dit moet eerst rechtgetrokken worden. Maar daarvoor moet eigenlijk eerst weer duidelijkheid komen over referenties en id's.

Hiervoor voegen we deze repo toe als (extra) remote:

  git remote add -f ada-2-fhir-noobs file:///<pad naar repo>
  
Vervolgens mergen we de master-branch naar de master van de nieuwe repo

  git merge ada-2-fhir-noobs/master --allow-unrelated-histories
  
Dit resulteert in enkele merge-conflicten die handmatig opgelost moeten worden.

Vervolgens doen we hetzelfde voor develop.

  git checkout -b develop
  git merge ada-2-fhir-noobs/develop --allow-unrelated-histories

Ook hiervoor moeten we weer enkele kleine merge-conflictent oplossen.

Als laatste moeten we de remote weer verwijderen:

  git remote remove ada-2-fhir-noobs
  
### README's

Nu alles compleet is, moeten de README's op orde gebracht worden. Heeft het veel zin om per folder een README aan te houden? Zeker omdat er heel vaak staat dat het om een 'preliminary version' gaat?

### Migratie naar Github

Eenmaal omgezet naar Git, is het eenvoudig om er een Git-repo mee te initialiseren.

### Auteurs-mapping

De inhoud van authors-transform.txt zou er als volgt uit kunnen zien. Eigenlijk zijn alleen Arianne, Alexander en Pieter van belang, de rest speelt geen rol in het mappings-gedeelte.

	henket = Alexander Henket <ahenket@xs4all.nl>
	ligtvoet = Maarten Ligtvoet <ligtvoet@nictiz.nl>
	pedelman = Pieter Edelman <edelman@nictiz.nl>
	vanstijn = Tessa van Stijn <stijn@nictiz.nl>
	wetering = Arianne van de Wetering <wetering@nictiz.nl>
	graauw = mgraauw <marcdegraauw@gmail.com>
	brouwer = Lilian Brouwer <brouwer@nictiz.nl>
	cberg = Unknown user <user@email>
	heitmann = Unknown user <user@email>
	system = System user <user@email>
	vandenBerg = Unknown user <user@email>
	vandenberg = Unknown user <user@email>

