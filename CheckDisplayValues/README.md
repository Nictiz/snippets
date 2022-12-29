# CheckDisplayValues
This project runs through all files in the `Nictiz-testscripts` folder and checks if the .display values of SNOMED and LOINC codes are up-to-date. The program is running on .NET 6.0. 

In order to run the code, please do the following:
1. Create an `appsettings.json` file in the same folder as the `Program.cs` script, with the following content:
    ```
    {
      "AppSettings": {
        "grant_type": "password",
        "client_id": "cli_client",
        "username": <email>,
        "password": <password>
        "Nictiz-testscripts-dir": <local Nictiz-testscripts directory>
      }
    }
    ```
    This is where your NTS credentials are stored. The file is included in the `.gitignore` to avoid leaking.
2. In the `LOINC` folder include the latest `LOINC-nlnames-*.**-patch.xlsx` file. The program assumes the file has only two columns. The first column contains the LOINC codes and the second the Dutch translations.
3. Please put all `.tgz` package files that needs to be checked for valueSets in the `CheckDiplayValue\Packages` folder. If it does not yet exist, create one.


Please keep in mind that only the following information standards are currently supported:
* BgZ
* eAppointment
* GenPractData
* BgLZ