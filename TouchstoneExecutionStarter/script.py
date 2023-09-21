#!/usr/bin/env python3

import argparse
import datetime
import requests
import mechanicalsoup
import os
import sys
import time

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
    * block_until_complete: Flag to indicate that the script should block until exectution has completed for this
                            target (this is the default behaviour for loadscript targets).
    """
    def __init__(self, rel_path, origins, destinations, params = None, is_loadscript_folder = False, block_until_complete = None):
        self.rel_path             = rel_path
        self.origins              = origins if type(origins) == list else [origins]
        self.destinations         = destinations if type(destinations) == list else [destinations]
        self.params               = params
        self.is_loadscript_folder = is_loadscript_folder
        self.block_until_complete = True if is_loadscript_folder else block_until_complete

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
    TARGETS["dev.Questionnaires2.Test.PHR"] = Target("dev/FHIR3-0-2-MM202001-Test/Questionnaires-2-0/PHR-Client", TOUCHSTONE, WF_202001_DEV, block_until_complete=True)
    TARGETS["dev.Questionnaires2.Test.XIS"] = Target("dev/FHIR3-0-2-MM202001-Test/Questionnaires-2-0/XIS-Server-Nictiz-intern", TOUCHSTONE, WF_202001_DEV, block_until_complete=True)
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
    TARGETS["eOverdracht.LoadResources"] = Target("FHIR3-0-2-eOverdracht4-0/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)
    
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
        # Default to this monday
        monday = datetime.date.today() - datetime.timedelta(days = datetime.date.today().weekday())
        self.date_T = monday.strftime("%Y-%m-%d")

        if not ("TS_USER"  in os.environ and "TS_PASS" in os.environ):
            sys.exit("Set the environment variables 'TS_USER' and 'TS_PASS' to login to Touchstone")

        self.browser = mechanicalsoup.StatefulBrowser()
        self.__api_key = None

    def loginFrontend(self):
        """ Login to the Touchstone website. It requires the environment variables TS_USER and TS_PASS to be set. """
        self.browser.open("https://touchstone.aegis.net/touchstone/login")

        self.browser.select_form('form[id="loginForm"]')
        self.browser["emailOrLoginID"] = os.environ["TS_USER"]
        self.browser["password"] = os.environ["TS_PASS"]
        response = self.browser.submit_selected()
        if "Sign Out" not in response.text:
            sys.exit("Couldn't login into Touchstone")

    def logoutFrontend(self):
        self.browser.open("https://touchstone.aegis.net/touchstone/logout")

    def apiKey(self):
        if self.__api_key == None:
            body = {
                "email": os.environ["TS_USER"],
                "password": os.environ["TS_PASS"]
            }
            response = requests.post("https://touchstone.aegis.net/touchstone/api/authenticate", json=body)
            if response.status_code != 201 or "API-Key" not in response.json():
                sys.exit("Couldn't login into the Touchstone API")
            self.__api_key = response.json()["API-Key"]
        return self.__api_key

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
                    target = [t for t in self.TARGETS.keys() if not isinstance(self.TARGETS[t], Header)][index - 1]
                except ValueError:
                    # Target wasn't a number
                    pass
                except IndexError:
                    print(f"Unknown target number '{index}")
                if not target in self.TARGETS:
                    print(f"Unknown target '{target}'")
                else:
                    self.execute(self.TARGETS[target])
            elif type(target) == list:
                self.execute(*target)
            elif isinstance(target, Target):
                self.executeTarget(target)
    
    def executeTarget(self, target: Target):
        """ Execute one specific target, defined by a Target object """
        print
        print(f"- Setting up {target.rel_path}")

        # Navigate to the relevant target and select all testscripts that are not loadscripts
        self.browser.open(f"https://touchstone.aegis.net/touchstone/testdefinitions?selectedTestGrp=/FHIRSandbox/Nictiz/{target.rel_path}&activeOnly=true&contentEntry=TEST_SCRIPTS&ps=200")
        select_all = True
        self.browser.select_form('form[id="testDefSearch"]')
        selected_testscripts = []
        for input in self.browser.page.find_all("input", "selectedId"):
            if "load-resources-purgecreateupdate" in input.attrs["value"] and not target.is_loadscript_folder:
                select_all = False
            else:                
                selected_testscripts.append(input.attrs["value"])
        self.browser["selectedTestScripts"] = selected_testscripts
        self.browser["allSelected"] = True if select_all else False

        # Submit the form
        self.browser.submit_selected()
        
        # Select the origin based on its name
        self._selectOrigDest("origin", target.origins)

        # Select the destination based on its name
        self._selectOrigDest("dest", target.destinations)

        # Populate all variables
        self.browser.select_form('form[id="testSetupForm"]')
        if target.params == None:
            target.params = {"T": self.date_T}
        elif "T" not in target.params:
            target.params["T"] = self.date_T
        for param in target.params:
            for textarea in self.browser.page.find_all("textarea"): # The name attribute of the targetted textarea is very long and I'm not sure if the beginning is guaranteed to be stable, so we're using a search on all textarea's here and filter out based on the latter part of the name
                if textarea.attrs["name"].endswith(f"variableSetups.variableSetupMap[{param}]"):
                    self.browser[textarea.attrs["name"]] = target.params[param].strip()

        # The submission expects a field called "execute", which is normally sent when clicking the "execute" button.
        # However, for some reason this field is not included when programmatically doing this.
        self.browser.form.set("execute", "", True)
        
        response = self.browser.submit_selected()
        if response.status_code == 200:
            print(f"{target.rel_path} execution started on {self.browser.url}")
        else:
            print(f"Couldn't start execution for {target.rel_path}")

        if target.block_until_complete:
            self._blockUntilComplete()

    def _blockUntilComplete(self):
        """ Stall until the test execution has completed. """

        sys.stdout.write("Waiting until completion ")
    
        execution_id = self.browser.url.replace("https://touchstone.aegis.net/touchstone/execution?exec=", "")
        running = True
        while running:
            response = requests.get("https://touchstone.aegis.net/touchstone/api/testExecution/" + execution_id, headers = {
                "API-Key": self.apiKey(),
                "Accept": "application/json"
            })
            if response.status_code != 200 or "status" not in response.json():
                print("Couldn't retrieve execution status, continuing")
                running = False
            elif response.json()["status"] == "Running":
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(5)
            else:
                print(" done")
                running = False

    def _selectOrigDest(self, type, values):
        """ Select origin or destination dropdowns on the Touchstone UI during execution setup.
            * type: "origin" or "dest"
            * values: A list of origins or destinations to select.
        """
        self.browser.select_form('form[id="testSetupForm"]')

        for i in range(len(values)):
            if i == 0:
                dropdown_ids = [f"main{type.lower()}1TsSelect", f"single{type.capitalize()}TsSelect"] # If a origin/destination is explicitly defined in the TestScript, the select box has a different id then when it is absent
            else:
                dropdown_ids = [f"main{type.lower()}{i + 1}TsSelect"]

            for id in dropdown_ids:
                dropdowns = self.browser.page.find_all("select", id=id)
                if len(dropdowns) > 0:
                    self.browser[dropdowns[0].attrs["name"]] = values[i]

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
        launcher.loginFrontend()
        launcher.execute(*args.target)

    finally:
        # Always try to logout, otherwise we'll have too many open sessions.
        launcher.logoutFrontend()
