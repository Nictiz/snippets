# Conformancelab-testen
Door middel van [Playwright for Python](https://playwright.dev/python/) kunnen er testen worden ontwikkeld om de Nictiz inrichting van Conformancelab te testen.
Een bijkomend voordeel is dat men er ook Conformancelab mee kan aansturen.

Voor gebruik moet men dus de [installatiegids](https://playwright.dev/python/docs/intro) van Playwright doornemen.

## Inloggegevens
In de hoofdfolder staat een `.env.expample` bestand. Pas dit bestand aan door de `.example` weg te halen en je inloggegevens van het Interoplab platform in te vullen. De `.env` staat in de .gitignore en zal niet in de repo meegenomen worden. `CL_TOTP_SECRET` kan men vinden in je password manager.

## Configuratie
In `pytest.ini` kun je configureren hoeveel testen parallel worden uitgevoerd door parameter  `addopts` aan te passen.

## Testresultaten
Testresultaten en logging komen in de folder `test-result` die automatisch wordt aangemaakt zodra de eerste test wordt uitgevoerd. 

## Testen in bulk uitvoeren
Om server testen in bulk uit te voeren is er de test `tests/test_regressie.py` ontwikkeld. Het is niet mogelijk om client testen in bulk uit te voeren omdat er maar 1 client test per organisatie tegelijk uitgevoerd kan worden.

In het .py bestand kan men de volgende parameters configureren om de juiste versie van de testen uit te voeren: \
`BRANCH = "main"`\
`INFO_STANDARD = "R4\\MP9 3.0.0-rc.1"` (Pad is relatief met de INPUT_DIR variabele, hoe meer je specificeert hoe specifiekere set opgehaald wordt. Het kijkt namelijk naar alle onderliggende properties.json's)

LET OP! Voor dat men de test uitvoert moet men eerst de juiste branch van de Nictiz-testscripts repo uitchecken die je wilt testen.
