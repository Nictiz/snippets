#!/usr/bin/env python3

from twill import browser
from twill.commands import *
import argparse
import datetime
import os
import sys

class Target:
    """
    Define a test execution based on the supplied parameters.
    * rel_path: the relative path, Unix-style and compared to the root of the repo, of the folder with the
                TestScripts
    * origin: the name(s) of the test system(s) that should be used as the origin. The names should be exactly how it
              is in Touchstone.
    * dest: the name(s) of the test system(s) that should be used as the destination. The names should be exactly how
            it is in Touchstone.
    * params: An optional dict of TestScript variables that can be filled out during execution setup. The
              "date T" variable will automatically be included, unless it is explicitly defined in variables.
    * is_loadscript_folder: Flag to indicate if loadscripts should be included in the test setup.
    """
    def __init__(self, rel_path, origins, destinations, params = None, is_loadscript_folder = False):
        self.rel_path             = rel_path
        self.origins              = origins if type(origins) == list else [origins]
        self.destinations         = destinations if type(destinations) == list else [destinations]
        self.params               = params
        self.is_loadscript_folder = is_loadscript_folder

class Launcher:
    TOUCHSTONE       = "AEGIS.net, Inc. - TouchstoneFHIR"
    WF_201901        = "Nictiz - Nictiz WildFHIR V201901 - FHIR 3.0.2"
    WF_202001        = "Nictiz - Nictiz WildFHIR V202001 - FHIR 3.0.2"
    WF_201901_DEV    = "Nictiz - Nictiz WildFHIR V201901-Dev - FHIR 3.0.2"
    WF_202001_DEV    = "Nictiz - Nictiz WildFHIR V202001-Dev - FHIR 3.0.2"
    WF_4             = "Nictiz - R4 MedMij - FHIR 4.0.1"
    WF_4_NO_AUTH     = "Nictiz - R4 (NoAuth) - FHIR 4.0.1"
    WF_4_NO_AUTH_DEV = "Nictiz - R4 (NoAuth) (Dev) - FHIR 4.0.1"

    # --- Define all targets that we know. ---
    TARGETS = {}

    TARGETS["dev.Questionnaires2.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Test/Questionnaires-2-0/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.Questionnaires2.Test.PHR"] = Target("dev/FHIR3-0-2-MM202001-Test/Questionnaires-2-0/PHR-Client", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.Questionnaires2.Test.XIS"] = Target("dev/FHIR3-0-2-MM202001-Test/Questionnaires-2-0/XIS-Server-Nictiz-intern", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.BgLZ3.Test"] = Target("dev/FHIR3-0-2-MM202002-Test/BgLZ-3-0", TOUCHSTONE, WF_202001_DEV)

    TARGETS["dev.MM2020.01.Test.LoadResources"] = [
        "dev.Questionnaires2.Test.LoadResources",
    ]

    TARGETS["dev.Medication-907.Test"] = Target("dev/FHIR3-0-2-MM201901-Test/Medication-9-0-7-test", TOUCHSTONE, WF_201901_DEV)
    TARGETS["dev.MP9.3.Test"] = [
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/PrescrProcessing/Receive", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/PrescrProcessing/Send-Nictiz-intern", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ProposalMA/Receive", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ProposalMA/Send-Nictiz-intern", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ProposalVV/Receive", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ProposalVV/Send-Nictiz-intern", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ReplyProposalMA/Receive", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ReplyProposalMA/Send-Nictiz-intern", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ReplyProposalVV/Receive", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/ReplyProposalVV/Send-Nictiz-intern", TOUCHSTONE, WF_4_NO_AUTH_DEV),
    ]

    TARGETS["dev.eOverdracht4.Test.LoadResources"] = Target("dev/FHIR3-0-2-eOverdracht4-0/Test/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.eOverdracht4.Cert.LoadResources"] = Target("dev/FHIR3-0-2-eOverdracht4-0/Cert/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.eOverdracht4.LoadResources"] = ["dev.eOverdracht4.Test.LoadResources", "dev.eOverdracht4.Cert.LoadResources"]
    TARGETS["dev.eOverdracht4.Test.Receiving-XIS"] = Target("FHIR3-0-2-eOverdracht4-0/Test/Receiving-XIS", TOUCHSTONE, WF_202001_DEV, {"authorization-token-id": "1234", "notificationEndpoint": "http://example.com/eOverdracht"})
    TARGETS["dev.eOverdracht4.Test.Sending-XIS-Nictiz-only"] = Target("FHIR3-0-2-eOverdracht4-0/Test/Sending-XIS-Nictiz-only", [TOUCHSTONE, TOUCHSTONE], [WF_202001_DEV, WF_202001_DEV])
    TARGETS["dev.eOverdracht4.Cert.Receiving-XIS"] = Target("FHIR3-0-2-eOverdracht4-0/Cert/Receiving-XIS", TOUCHSTONE, WF_202001_DEV, {"authorization-token-id": "1234", "notificationEndpoint": "http://example.com/eOverdracht"})
    TARGETS["dev.eOverdracht4.Cert.Sending-XIS-Nictiz-only"] = Target("FHIR3-0-2-eOverdracht4-0/Cert/Sending-XIS-Nictiz-only", [TOUCHSTONE, TOUCHSTONE], [WF_202001_DEV, WF_202001_DEV])
    TARGETS["dev.eOverdracht4.Test"] = ["dev.eOverdracht4.Test.Receiving-XIS", "dev.eOverdracht4.Test.Sending-XIS-Nictiz-only"]
    TARGETS["dev.eOverdracht4.Cert"] = ["dev.eOverdracht4.Cert.Receiving-XIS", "dev.eOverdracht4.Cert.Sending-XIS-Nictiz-only"]
    TARGETS["dev.eOverdracht4"] = ["dev.eOverdracht4.Test", "dev.eOverdracht4.Cert"]
    
    TARGETS["MM2019.01.Test.LoadResources"] = Target("FHIR3-0-2-MM201901-Test/_LoadResources", TOUCHSTONE, WF_201901, is_loadscript_folder = True)
    TARGETS["MM2019.01.Cert.LoadResources"] = Target("FHIR3-0-2-MM201901-Cert/_LoadResources", TOUCHSTONE, WF_201901, is_loadscript_folder = True)
    TARGETS["Geboortezorg.LoadResources"] = Target("FHIR3-0-2-Geboortezorg/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)
    TARGETS["MM2020.01.Test.LoadResources"] = Target("FHIR3-0-2-MM202001-Test/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)
    TARGETS["MM2020.01.Cert.LoadResources"] = Target("FHIR3-0-2-MM202001-Cert/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)
    TARGETS["MM2020.02.Test.LoadResources"] = Target("FHIR3-0-2-MM202002-Test/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)
    TARGETS["MM2020.02.Cert.LoadResources"] = Target("FHIR3-0-2-MM202002-Cert/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)
    
    TARGETS["MedMij6.Test.LoadResources"] = Target("FHIR4-0-1-MedMij-Test/_LoadResources", TOUCHSTONE, WF_4, is_loadscript_folder = True)
    TARGETS["MedMij6.Cert.LoadResources"] = Target("FHIR4-0-1-MedMij-Cert/_LoadResources", TOUCHSTONE, WF_4, is_loadscript_folder = True)
    TARGETS["FHIR4.Test.LoadResources"] = Target("FHIR4-0-1-Test/_LoadResources", TOUCHSTONE, WF_4_NO_AUTH, is_loadscript_folder = True)

    TARGETS["LoadResources"] = [
        "MM2019.01.Test.LoadResources",
        "MM2019.01.Cert.LoadResources",
        "MM2020.01.Test.LoadResources",
        "MM2020.01.Cert.LoadResources",
        "MM2020.02.Test.LoadResources",
        "MM2020.02.Cert.LoadResources",
        "Geboortezorg.LoadResources",
        "MedMij6.Test.LoadResources",
        "MedMij6.Cert.LoadResources",
        "FHIR4.Test.LoadResources",
    ]

    def __init__(self):
        self.results = []

        # Default to this monday
        monday = datetime.date.today() - datetime.timedelta(days = datetime.date.today().weekday())
        self.date_T = monday.strftime("%Y-%m-%d")

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

    def printTargets(self):
        """ Print out all defined targets with their index number. If a target is a collection of other targets, they will be printed in parentheses. """
        names = list(self.TARGETS.keys())
        for i in range(len(names)):
            line = "%2d" % (i + 1)
            name = names[i]
            line += ".  " + name

            if type(self.TARGETS[name]) == list:
                subtargets = [t for t in self.TARGETS[name] if type(t) == str]
                if len(subtargets) > 0:
                    line += " (" + ", ".join(subtargets) + ")"
            print(line)

    def execute(self, *targets):
        """ Execute one or more targets. """
        for target in targets:
            if type(target) == str:
                try:
                    # See if we have an index rather than a mnemonic
                    index = int(target)
                    target = list(self.TARGETS.keys())[index - 1]
                except ValueError:
                    # Target wasn't a number
                    pass
                except IndexError:
                    self.results.append(f"Unknown target number '{index}")
                if not target in self.TARGETS:
                    self.results.append(f"Unknown target '{target}'")
                else:
                    self.execute(self.TARGETS[target])
            elif type(target) == list:
                self.execute(*target)
            elif isinstance(target, Target):
                self.executeTarget(target)
    
    def executeTarget(self, target: Target):
        """ Execute one specific target, defined by a Target object """
        print
        print(f"====================== Setting up {target.rel_path} =========================")

        # Navigate to the relevant target and select all testscripts that are not loadscripts
        go(f"https://touchstone.aegis.net/touchstone/testdefinitions?selectedTestGrp=/FHIRSandbox/Nictiz/{target.rel_path}&activeOnly=true&contentEntry=TEST_SCRIPTS&ps=200")
        select_all = True
        for input in browser.forms[4].inputs:
            if input.name == "selectedTestScripts": # This explicit check is needed because inputs["selectedTestScripts"] will not always yield the right results
                if "load-resources-purgecreateupdate" in input.attrib["value"] and not target.is_loadscript_folder:
                    select_all = False
                else:                
                    input.value = input.attrib["value"]
        fv(5, "allSelected", "on" if select_all else "off")

        # Submit the form
        submit("setupSelected")
        
        # Select the origin based on its name
        self._selectOrigDest("origin", target.origins)

        # Select the destination based on its name
        self._selectOrigDest("dest", target.destinations)

        # Populate all variables
        if target.params == None:
            target.params = {"T": self.date_T}
        elif "T" not in target.params:
            target.params["T"] = self.date_T
        for param in target.params:
            for textarea in browser.forms[0].xpath("//textarea"):
                if textarea.name.endswith(f"variableSetups.variableSetupMap[{param}]"):
                    fv(1, textarea.name, target.params[param])
                else: # Workaround: twill seems to add a linebreak before the content of a textarea, which confuses Touchstone. So we need to remove it.
                    textarea.value = textarea.value.strip()
        
        submit("execute")
        if browser.code == 200:
            self.results.append(f"{target.rel_path} execution started on {browser.url}")
        else:
            self.results.append(f"Couldn't start execution for {target.rel_path}")

    def _selectOrigDest(self, type, values):
        """ Select origin or destination dropdowns on the Touchstone UI during execution setup.
            * type: "origin" or "dest"
            * values: A list of origins or destinations to select.
        """
        for i in range(len(values)):
            if i == 0:
                dropdown_ids = [f"main{type.lower()}1TsSelect", f"single{type.capitalize()}TsSelect"] # If a origin/destination is explicitly defined in the TestScript, the select box has a different id then when it is absent
            else:
                dropdown_ids = [f"main{type.lower()}{i + 1}TsSelect"]
            for id in dropdown_ids:
                dropdowns = browser.forms[0].xpath(f"//select[@id='{id}']")
                if len(dropdowns) > 0:
                    options = dropdowns[0].xpath(f"option[text()='{values[i]}']")
                    if len(options) == 1:
                        fv(1, id, options[0].attrib["value"])
                    else:
                        print(f"Couldn't select {type.lower()} '{values[i]}'")
                        return

    def printResults(self):
        print()
        print(f"====================== Results =======================================")
        for result in self.results:
            print(result)
        print()
        print()

if __name__ == "__main__":
    launcher = Launcher()
    targets = []

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", help = "List all available targets", action = "store_true")
    parser.add_argument("-T", help = f"Date T to use (default is '{launcher.date_T}')")
    parser.add_argument("target", nargs = "*", help = "The targets to execute (both numbers and mnemonics are supported)")
    args = parser.parse_args()

    if args.T != None:
        launcher.date_T = args.T

    if args.list:
        launcher.printTargets()
        exit(0)

    elif len(args.target) == 0:
        print("You need to specify at least one target (use --list to show the available targets)")
        exit(1)
    try:
        launcher.login()
        launcher.execute(*args.target)

        launcher.printResults()

    finally:
        # Always try to logout, otherwise we'll have too many open sessions.
        go("https://touchstone.aegis.net/touchstone/logout")