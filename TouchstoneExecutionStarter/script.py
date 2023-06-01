from twill import browser
from twill.commands import *
import os
import sys

class Launcher:
    TOUCHSTONE   = "AEGIS.net, Inc. - TouchstoneFHIR"
    WF_201901    = "Nictiz - Nictiz WildFHIR V201901 - FHIR 3.0.2"
    WF_202001    = "Nictiz - Nictiz WildFHIR V202001 - FHIR 3.0.2"
    WF_4         = "Nictiz - R4 MedMij - FHIR 4.0.1"
    WF_4_NO_AUTH = "Nictiz - R4 (NoAuth) - FHIR 4.0.1"
    WF_4_NO_AUTH_DEV = "Nictiz - R4 (NoAuth) (Dev) - FHIR 4.0.1"

    """ Initialize with the 'date T' variable that will be used. """
    def __init__(self, T):
        self.results = []
        self.T = T

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

    def execute(self, relPath, origin, dest, variables = None, ignore_loadscript = True):
        """
            Start a test execution based on the supplied parameters.
            * relPath: the relative path, Unix-style and compared to the root of the repo, of the folder with the
                       TestScripts
            * origin: the name of the test system that should be used as the origin. The name should be exactly how it
                      is in Touchstone.
            * dest: the name of the test system that should be used as the destination. The name should be exactly how
                    it is in Touchstone.
            * variables: An optional dict of TestScript variables that can be filled out during execution setup. The
                         "date T" variable will automaticall be included, unless it is explicitly defined in variables.
            * ignore_loadscript: Flag to indicate if loadscripts should be ignored.

            The function ouputs what's going on when navigating Touchstone. The result is cached in self.results, which
            can be shown using printResults().
        """

        print
        print(f"====================== Setting up {relPath} =========================")

        # Navigate to the relevant folder and select all testscripts that are not loadscripts
        go(f"https://touchstone.aegis.net/touchstone/testdefinitions?selectedTestGrp=/FHIRSandbox/Nictiz/{relPath}&activeOnly=true&contentEntry=TEST_SCRIPTS&ps=200")
        select_all = True
        for input in browser.forms[4].inputs:
            if input.name == "selectedTestScripts": # This explicit check is needed because inputs["selectedTestScripts"] will not always yield the right results
                if "load-resources-purgecreateupdate" in input.attrib["value"] and ignore_loadscript:
                    select_all = False
                else:                
                    input.value = input.attrib["value"]
        fv(5, "allSelected", "on" if select_all else "off")

        # Submit the form
        submit("setupSelected")
        
        # Select the origin based on its name
        for id in ["mainorigin1TsSelect", "singleOriginTsSelect"]: # If an origin is explicitly defined in the TestScript, the select box has a different id then when it is absent
            origSelects = browser.forms[0].xpath(f"//select[@id='{id}']")
            if len(origSelects) > 0:
                origOptions = origSelects[0].xpath(f"option[text()='{origin}']")
                if len(origOptions) == 1:
                    origValue = origOptions[0].attrib["value"]
                    fv(1, id, origValue)
                else:
                    print(f"Couldn't select origin '{origin}'")
                    return

        # Select the destination based on its name
        for id in ["maindest1TsSelect", "singleDestTsSelect"]: # If a destination is explicitly defined in the TestScript, the select box has a different id then when it is absent
            destSelects = browser.forms[0].xpath(f"//select[@id='{id}']")
            if len(destSelects) > 0:
                destOptions = destSelects[0].xpath(f"option[text()='{dest}']")
                if len(destOptions) == 1:
                    destValue = destOptions[0].attrib["value"]
                    fv(1, id, destValue)
                else:
                    print(f"Couldn't select destination '{dest}'")
                    return

        # Populate all variables
        if variables == None:
            variables = {"T": self.T}
        elif "T" not in variables:
            variables["T"] = self.T
        for variable in variables:
            for textarea in browser.forms[0].xpath("//textarea"):
                if textarea.name.endswith(f"variableSetups.variableSetupMap[{variable}]"):
                    fv(1, textarea.name, variables[variable])
                else: # Workaround: twill seems to add a linebreak before the content of a textarea, which confuses Touchstone. So we need to remove it.
                    textarea.value = textarea.value.strip()
        
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

    def launchLoadScripts(self):
        launcher.execute("FHIR3-0-2-MM201901-Test/_LoadResources", self.TOUCHSTONE, self.WF_201901, ignore_loadscript = False)
        launcher.execute("FHIR3-0-2-MM201901-Cert/_LoadResources", self.TOUCHSTONE, self.WF_201901, ignore_loadscript = False)
        launcher.execute("FHIR3-0-2-Geboortezorg/_LoadResources", self.TOUCHSTONE, self.WF_202001, ignore_loadscript = False)
        launcher.execute("FHIR3-0-2-MM202001-Test/_LoadResources", self.TOUCHSTONE, self.WF_202001, ignore_loadscript = False)
        launcher.execute("FHIR3-0-2-MM202001-Cert/_LoadResources", self.TOUCHSTONE, self.WF_202001, ignore_loadscript = False)
        launcher.execute("FHIR3-0-2-MM202002-Test/_LoadResources", self.TOUCHSTONE, self.WF_202001, ignore_loadscript = False)
        launcher.execute("FHIR3-0-2-MM202002-Cert/_LoadResources", self.TOUCHSTONE, self.WF_202001, ignore_loadscript = False)
        launcher.execute("FHIR3-0-2-eOverdracht4-0/_LoadResources", self.TOUCHSTONE, self.WF_202001, ignore_loadscript = False)
        launcher.execute("FHIR4-0-1-MedMij-Test/_LoadResources", self.TOUCHSTONE, self.WF_4, ignore_loadscript = False)
        launcher.execute("FHIR4-0-1-MedMij-Cert/_LoadResources", self.TOUCHSTONE, self.WF_4, ignore_loadscript = False)
        launcher.execute("FHIR4-0-1-Test/_LoadResources", self.TOUCHSTONE, self.WF_4_NO_AUTH, ignore_loadscript = False)

    def launchSample(self):
        #launcher.execute("FHIR3-0-2-MM201901-Test/Medication-9-0-7/XIS-Server", self.TOUCHSTONE, self.WF_201901)
        #launcher.execute("FHIR3-0-2-MM202001-Cert/GGZ-2-0", self.TOUCHSTONE, self.WF_202001)
        launcher.execute("FHIR3-0-2-MM202001-Test/SelfMeasurements-2-0", self.TOUCHSTONE, self.WF_202001)

if __name__ == "__main__":
    try:
        launcher = Launcher("2023-05-29")
        launcher.login()

        #launcher.launchLoadScripts()
        launcher.launchSample()

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
        # launcher.execute("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ReplyProposalVV/Send-Nictiz-intern", touchstone, wf4NoAuth, {"T": T})

        launcher.printResults()

    finally:
        # Always try to logout, otherwise we'll have too many open sessions.
        go("https://touchstone.aegis.net/touchstone/logout")