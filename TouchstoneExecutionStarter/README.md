# Execution starter for Touchstone

This script can be used for the bulk creation of Touchstone test executions from folders in Touchstone. It was developed for the monthly patch release regression tests on test script materials, which requires a lot of clicking to manually and filling out parameters to start a test execution.

Prerequisites:
* TestScripts and fixtures have been uploaded to the proper folders, with the proper validation environment set.
* The folders paths _exactly_ match the paths defined in the scripts.
* Python 3 is installed.
* The [mechanicalsoup](https://pypi.org/project/MechanicalSoup/) Python module is present.
* The following environment variables are set (this method is chosen to prevent that the password is accidentally written down i nthe script and then committed):
    * TS_USER: The username of the Touchstone user
    * TS_PASS: The password of the Touchstone user

To launch a particular folder, it has to be defined as an instance of the `Target` class, which encapsulates all necessary metadata (origin, destination, parameters). Several folders are already defined in the script. If a folder is absent, you can add them to the `TARGETS` dict of the `Launcher` class with a mnemonic key that makes it easy recognizable (and typeable)/

Once defined, you can list all known targets using:
> python script.py --list

And you can execute one or more targets by listing them on the command line, either using their mnemonic names or their numbers as shown in the `--list` output, e.g.:
> python script.py 3 6 dev.eOverdracht4.Cert
> 
will launch the targets defined by index number 3, index number 6, and mnemonic "dev.eOvderdrach4.Cert".

The script does not:
* Take care of uploading materials to Touchstone.
* Report back results of the execution. It merely provides the URL where the running test execution can be found.

Please note: this script is a web scraper, it uses the GUI frontend of Touchstone. Touchstone does actually provide an API, but it is not suited to our needs, as it can only be used to start _existing_ test executions. Since we're the ones developing test scenario's, our need is to _create_ new executions based on the TestScript and fixture files that we uploaded.
