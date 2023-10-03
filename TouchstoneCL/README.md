# Command line interface for Touchstone

This script can be used for bulk uploading and bulk creation of Touchstone test executions from folders in Touchstone. It was developed for the monthly patch release regression tests on test script materials, which requires a lot of clicking to manually and filling out parameters to start a test execution.

Prerequisites:
* TestScripts and fixtures have been uploaded to the proper folders, with the proper validation environment set.
* The folders paths _exactly_ match the paths defined in the scripts.
* Python 3 is installed with the following modules (`pip install [module name]`)
    * [mechanicalsoup](https://pypi.org/project/MechanicalSoup/)
    * [colorama](https://pypi.org/project/colorama/)
    * [pyaml](https://pypi.org/project/pyaml/)
* The following environment variables are set (this method is chosen to prevent that the password is accidentally written down i nthe script and then committed):
    * TS_USER: The username of the Touchstone user
    * TS_PASS: The password of the Touchstone user

There are two scripts, one for uploading folders and one for launching folders. These scripts use the settings defined in the file `properties.yml` to determine what to use when uploading of launching executions. See below for more information.

Both scripts assume that this repo is checked out next to the Nictiz-testscripts repo. If not, use the `--repo-root` command line option to define the path to this repo.

Please note: for most parts, this script is mostly a web scraper, it uses the GUI frontend of Touchstone. Touchstone does actually provide an API which is used for getting the execution status, but for uploading or launching executions, no API is available.

## Uploading
Basic interface:
> python upload.py

This will list all folders that can be uploaded to Touchstone, associated with a number. You can then list one or more numbers of folders to upload.

The default is to upload to the "dev" folder in Touchstone, unless the `--production` flag has been set.

Important: the script will figure out the settings from `properties.yml` as described below, but only for the specified folder. If there are deviating settings for a specific subfolder, these will be ignored. Only when this specific subfolder is defined as an explicit target, its settings will be used.

## Launching executions
Basic interface:
> python launcher.py

This will list all folders that can be used to launch an execution, associated with a number. You can then list one or more numbers of folders to execute.

The default is to launch the "dev" version in Touchstone, unless the `--production` flag has been set.

The script will default to "this monday" as the "date T" variable. This can be overridden using the `-T` option.

After starting all executions, the script will poll the Touchstone API for the result until all executions are completed (unless the `--start-only` flag is given). When launching loadscripts (or targets where it's explicitly defined for), the script will stall until this Touchstone execution has finished.

Specifically for patch release work the `--jira-table` flag can be used to output the results in Jira table format.

## Specifying upload/launch properties
The file `properties.yml` can be used to set, per folder, what properties should be used for uploading and launching. A setting specified for a folder applies to all its subfolders, unless another setting for a subfolder is explicitly defined.

Since we differentiate the development from the production environment, on the root level there should be an entry named "dev" and an entry named "production".

The following settings are recognized. All values should be the literal names as found on the upload/execution screens in Touchstone:
- "access": The "Can be viewed by" group(s) to be set when uploading.  Combinations that are not possible in Touchstone are also not possible in the script, but no check will be done.
- "validator": The validation environment to use for uploading. (Multiple validators are not supported at the moment).
- "origins": One or more origins to use for the execution. 
- "destinations": One or more destinations to use for the execution.
- "params": Parameters to set on execution. This is the only cumulative setting, so the settings for subfolders and folders will be combined. T is automatically included if not specified.
