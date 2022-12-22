# CheckDisplayValues
This project runs through all files in the `Source` folder and checks if the.display values of SNOMED and LOINC codes are up-to-date. The program is running on .NET 6.0. 

In order to run the code, please do the following:
1. Create an `appsettings.json` file in the same folder as the `Program.cs` script, with the following content:
    ```
    {
      "AppSettings": {
        "grant_type": "password",
        "client_id": "cli_client",
        "username": <email>,
        "password": <password>
      }
    }
    ```
    This is where your NTS credentials are stored. The file is included in the `.gitignore` to avoid leaking.
2. In the `LOINC` folder include the latest `LOINC-nlnames-*.**-patch.xlsx` file. The program assumes the file has only two columns. The first column contains the LOINC codes and the second the Dutch translations.
3. Put all the `.xml` which you want to check in the `Source` folder. **WARNING**, please note that the program assumes that there are no T-Dates in the `.xml` files. If they are present, please use the `TDateConverter` tool to convert them.
4. Please put all `.tgz` package files that needs to be checked for valueSets in the `CheckDiplayValue\Packages` folder. If it does not yet exist, create one.


