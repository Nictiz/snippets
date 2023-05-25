# Execution starter for Touchstone

This script can be used for the bulk creation of Touchstone test executions from folders in Touchstone. It was developed for the monthly patch release regression tests on test script materials, which requires a lot of clicking to manually and filling out parameters to start a test execution.

Prerequisites:
* TestScripts and fixtures have been uploaded to the proper folders, with the proper validation environment set.
* The folders paths _exactly_ match the paths defined in the scripts.
* Python 3 is installed.
* The [twill](https://twill-tools.github.io/twill/) Python module is present.
* The following environment variables are set (this method is chosen to prevent that the password is accidentally written down i nthe script and then committed):
    * TS_USER: The username of the Touchstone user
    * TS_PASS: The password of the Touchstone user

Using the `execute()` method of the Launcher class, the user can create and start new test executions based on the scripts in the folder with the origin, destination and parameters supplied. Loadscripts will be excluded. The script does not:
* Take care of uploading materials to Touchstone.
* Report back results of the execution. It merely provides the URL where the running test execution can be found.

Please note: this script is a web scraper, it uses the GUI frontend of Touchstone. Touchstone does actually provide an API, but it is not suited to our needs, as it can only be used to start _existing_ test executions. Since we're the ones developing test scenario's, our need is to _create_ new executions based on the TestScript and fixture files that we uploaded.