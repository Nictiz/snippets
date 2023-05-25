from twill import browser
from twill.commands import *
import os
import sys

class Launcher:
    def __init__(self):
        self.results = []

    def login(self):
        """ Login to the Touchstone website. It requires the environment variables TS_USER and TS_PASS to be set. """
        go('https://touchstone.aegis.net/touchstone/login')

        try:
            formvalue("1", "emailOrLoginID", os.environ["TS_USER"])
            formvalue("1", "password", os.environ["TS_PASS"])
        except KeyError:
            sys.exit("Set the environment variables 'TS_USER' and 'TS_PASS' to login to Touchstone")

        submit()
        if "Sign Out" not in browser.html:
            sys.exit("Couldn't login into Touchstone")

    def execute(self, relPath, origin, dest, variables):
        """
            Start a test execution based on the supplied parameters.
            * relPath: the relative path, Unix-style and compared to the root of the repo, of the folder with the
                       TestScripts
            * origin: the name of the test system that should be used as the origin. The name should be exactly how it
                      is in Touchstone.
            * dest: the name of the test system that should be used as the destination. The name should be exactly how
                    it is in Touchstone.
            * variables: a dict of TestScript variables that can be filled out during execution setup.

            The function ouputs what's going on when navigating Touchstone. The result is cached in self.results, which
            can be shown using printResults().
        """

        print
        print(f"====================== Setting up {relPath} =========================")

        # Navigate to the relevant folder and select all testscripts that are not loadscripts
        go(f"https://touchstone.aegis.net/touchstone/testdefinitions?selectedTestGrp=/FHIRSandbox/Nictiz/{relPath}&activeOnly=true&contentEntry=TEST_SCRIPTS&ps=200")
        select_all = True
        for input in browser.forms[4].inputs["selectedTestScripts"]:
            if "load-resources-purgecreateupdate" in input.attrib["value"]:
                select_all = False
            else:
                input.value = input.attrib["value"]
        fv(5, "allSelected", "on" if select_all else "off")

        # Submit the form
        submit("setupSelected")
        
        # Select the origin based on its name
        origOptions = browser.forms[0].xpath("//select[@name='testSystemSetups.originTestSystemSetupMap[1].testSystemTokens']")[0].xpath(f"option[text()='{origin}']")
        if len(origOptions) == 1:
            origValue = origOptions[0].attrib["value"]
            fv(1, "mainorigin1TsSelect", origValue)
        else:
            print(f"Couldn't select origin '{origin}'")
            return

        # Select the destination based on its name
        destOptions = browser.forms[0].xpath("//select[@name='testSystemSetups.destTestSystemSetupMap[1].testSystemTokens']")[0].xpath(f"option[text()='{dest}']")
        if len(destOptions) == 1:
            destValue = destOptions[0].attrib["value"]
            fv(1, "maindest1TsSelect", destValue)
        else:
            print(f"Couldn't select destination '{dest}'")
            return

        # Populate all variables
        for variable in variables:
            for textarea in browser.forms[0].xpath("//textarea"):
                if textarea.name.endswith(f"variableSetups.variableSetupMap[{variable}]"):
                    fv(1, textarea.name, variables[variable])
        
        submit("execute")
        if browser.code == 200:
            self.results.append(f"{relPath} execution started on {browser.url}")
        else:
            self.results.append(f"Couldn't start execution for {relpath}")

    def printResults(self):
        print()
        print(f"====================== Results =======================================")
        for result in self.results:
            print(result)
        print()
        print()

if __name__ == "__main__":
    try:
        launcher = Launcher()
        launcher.login()

        touchstone = "AEGIS.net, Inc. - TouchstoneFHIR"
        wf4NoAuth = "Nictiz - R4 (NoAuth) (Dev) - FHIR 4.0.1"
        T = "2023-05-22"

        # launcher.execute("dev/FHIR3-0-2-MM201901-Test/Medication-9-0-7-test", "AEGIS.net, Inc. - TouchstoneFHIR", "Nictiz - Nictiz WildFHIR V201901-2 Dev - FHIR 3.0.2", {"T": "2023-05-22"})
        # launcher.execute("FHIR3-0-2-MM202002-Test/BgLZ-3-0", "AEGIS.net, Inc. - TouchstoneFHIR", "Nictiz - Nictiz WildFHIR V202001-Dev - FHIR 3.0.2", {})
        # launcher.execute("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/PrescrProcessing/Receive", touchstone, wf4NoAuth, {"T": T})
        # launcher.execute("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/PrescrProcessing/Send-Nictiz-intern", touchstone, wf4NoAuth, {"T": T})
        # launcher.execute("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ProposalMA/Receive", touchstone, wf4NoAuth, {"T": T})
        # launcher.execute("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ProposalMA/Send-Nictiz-intern", touchstone, wf4NoAuth, {"T": T})
        # launcher.execute("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ProposalVV/Receive", touchstone, wf4NoAuth, {"T": T})
        # launcher.execute("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ProposalVV/Send-Nictiz-intern", touchstone, wf4NoAuth, {"T": T})
        # launcher.execute("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ReplyProposalMA/Receive", touchstone, wf4NoAuth, {"T": T})
        # launcher.execute("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ReplyProposalMA/Send-Nictiz-intern", touchstone, wf4NoAuth, {"T": T})
        # launcher.execute("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ReplyProposalVV/Receive", touchstone, wf4NoAuth, {"T": T})
        launcher.execute("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ReplyProposalVV/Send-Nictiz-intern", touchstone, wf4NoAuth, {"T": T})

        launcher.printResults()

    finally:
        # Always try to logout, otherwise we'll have too many open sessions.
        go("https://touchstone.aegis.net/touchstone/logout")