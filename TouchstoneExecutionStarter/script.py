#!/usr/bin/env python3

import argparse
import collections
import datetime
import requests
import mechanicalsoup
import os
import pathlib
import re
import shutil
import sys
import tempfile
import time

from colorama import just_fix_windows_console
from dataclasses import dataclass

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

class Header:
    pass

@dataclass
class Execution:
    target: Target
    execution_id: str
    status: str = ""
    total: int = 0
    passes: int = 0
    warns: int =  0
    fails: int =  0
    duration: str = ""

class Launcher(mechanicalsoup.StatefulBrowser):
    TOUCHSTONE       = "AEGIS.net, Inc. - TouchstoneFHIR"
    WF_201901        = "Nictiz - Nictiz WildFHIR V201901 - FHIR 3.0.2"
    WF_202001        = "Nictiz - Nictiz WildFHIR V202001 - FHIR 3.0.2"
    WF_201901_DEV    = "Nictiz - Nictiz WildFHIR V201901-2 Dev - FHIR 3.0.2"
    WF_202001_DEV    = "Nictiz - Nictiz WildFHIR V202001-Dev - FHIR 3.0.2"
    WF_4             = "Nictiz - R4 MedMij - FHIR 4.0.1"
    WF_4_NO_AUTH     = "Nictiz - R4 (NoAuth) - FHIR 4.0.1"
    WF_4_DEV         = "Nictiz - R4 MedMij (Dev) - FHIR 4.0.1"
    WF_4_NO_AUTH_DEV = "Nictiz - R4 (NoAuth) (Dev) - FHIR 4.0.1"

    # --- Define all targets that we know. ---
    TARGETS = collections.OrderedDict()

    TARGETS["BgZ MSZ 1 -- dev"] = Header()
    TARGETS["dev.BgZ-MSZ-1.Cert.LoadResources"] = Target("dev/FHIR3-0-2-BgZ-MSZ-1-0/Cert/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.BgZ-MSZ-1.Cert"] = Target("dev/FHIR3-0-2-BgZ-MSZ-1-0/Cert", TOUCHSTONE, WF_202001_DEV)

    TARGETS["MedMij 2019.01 -- dev"] = Header()
    TARGETS["dev.Medication-907.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM201901-Test/_LoadResources", TOUCHSTONE, WF_201901_DEV, is_loadscript_folder = True)
    TARGETS["dev.Medication-907.Test.PHR-Client-Nictiz-intern"] = Target("dev/FHIR3-0-2-MM201901-Test/Medication-9-0-7/PHR-Client-Nictiz-intern", TOUCHSTONE, WF_201901_DEV)
    TARGETS["dev.Medication-907.Test.XIS"] = Target("dev/FHIR3-0-2-MM201901-Test/Medication-9-0-7/XIS-Server", TOUCHSTONE, WF_201901_DEV)
    TARGETS["dev.Medication-907.Test-test"] = Target("dev/FHIR3-0-2-MM201901-Test/Medication-9-0-7-test", TOUCHSTONE, WF_201901_DEV)

    TARGETS["MedMij 2020.01 -- dev"] = Header()
    TARGETS["dev.AllergyIntolerance3.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Test/AllergyIntolerance-3-0/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.AllergyIntolerance3.Test"] = Target("dev/FHIR3-0-2-MM202001-Test/AllergyIntolerance-3-0", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.BgZ3.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Test/BgZ-3-0/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.BgZ3.Test"] = Target("dev/FHIR3-0-2-MM202001-Test/BgZ-3-0", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.BgZ3.Cert.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Cert/BgZ-3-0/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.BgZ3.Cert"] = Target("dev/FHIR3-0-2-MM202001-Cert/BgZ-3-0", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.GGZ2.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Test/GGZ-2-0/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.GGZ2.Test"] = Target("dev/FHIR3-0-2-MM202001-Test/GGZ-2-0", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.GPData2.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Test/GenPractData-2-0/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.GPData2.Test"] = Target("dev/FHIR3-0-2-MM202001-Test/GenPractData-2-0", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.Images2.Test"] = Target("dev/FHIR3-0-2-MM202001-Test/Images-2-0", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.Lab2.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Test//LaboratoryResults-2-0/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.Lab2.Test"] = Target("dev/FHIR3-0-2-MM202001-Test/LaboratoryResults-2-0", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.PDFA3.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Test/PDFA-3-0/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.PDFA3.Test.PHR"] = Target("dev/FHIR3-0-2-MM202001-Test/PDFA-3-0/PHR-Client", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.PDFA3.Test.XIS-Server-Nictiz-intern"] = Target("dev/FHIR3-0-2-MM202001-Test/PDFA-3-0/XIS-Server-Nictiz-intern", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.Questionnaires2.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Test/Questionnaires-2-0/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.Questionnaires2.Test.PHR"] = Target("dev/FHIR3-0-2-MM202001-Test/Questionnaires-2-0/PHR-Client", TOUCHSTONE, WF_202001_DEV, block_until_complete=True)
    TARGETS["dev.Questionnaires2.Test.XIS-Server-Nictiz-intern"] = Target("dev/FHIR3-0-2-MM202001-Test/Questionnaires-2-0/XIS-Server-Nictiz-intern", TOUCHSTONE, WF_202001_DEV, block_until_complete=True)
    TARGETS["dev.SelfMeasurements2.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Test/SelfMeasurements-2-0/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.SelfMeasurements2.Test.XIS"] = Target("dev/FHIR3-0-2-MM202001-Test/SelfMeasurements-2-0/XIS-Server", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.SelfMeasurements2.Cert.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Cert/SelfMeasurements-2-0/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.SelfMeasurements2.Cert"] = Target("dev/FHIR3-0-2-MM202001-Cert/SelfMeasurements-2-0", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.eAppointment2.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Test/eAppointment-2-0/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.eAppointment2.Test"] = Target("dev/FHIR3-0-2-MM202001-Test/eAppointment-2-0", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.MM2020.01.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202001-Test/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.MM2020.01.Test"] = [
        "dev.AllergyIntolerance3.Test",
        "dev.BgZ3.Test",
        "dev.GGZ2.Test",
        "dev.GPData2.Test",
        "dev.Images2.Test",
        "dev.Lab2.Test",
        "dev.PDFA3.Test.PHR",
        "dev.PDFA3.Test.XIS-Server-Nictiz-intern",
        "dev.Questionnaires2.Test.PHR",
        "dev.Questionnaires2.Test.XIS-Server-Nictiz-intern",
        "dev.SelfMeasurements2.Test.XIS",
        "dev.eAppointment2.Test"
    ]

    TARGETS["MedMij 2020.02 -- dev"] = Header()
    TARGETS["dev.BgLZ3.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202002-Test/BgLZ-3-0", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.BgLZ3.Test.PHR"] = Target("dev/FHIR3-0-2-MM202002-Test/BgLZ-3-0/PHR-Client", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.BgLZ3.Test.XIS-Server-Nictiz-intern"] = Target("dev/FHIR3-0-2-MM202002-Test/BgLZ-3-0/XIS-Server-Nictiz-intern", TOUCHSTONE, WF_202001_DEV)
    TARGETS["dev.MM2020.02.Test.LoadResources"] = Target("dev/FHIR3-0-2-MM202002-Test/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.MM2020.02.Test"] = [
        "dev.BgLZ3.Test.PHR",
        "dev.BgLZ3.Test.XIS-Server-Nictiz-intern"
    ]

    TARGETS["eOverdracht 4 -- dev"] = Header()
    TARGETS["dev.eOverdracht4.Test.LoadResources"] = Target("dev/FHIR3-0-2-eOverdracht4-0/Test/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.eOverdracht4.Cert.LoadResources"] = Target("dev/FHIR3-0-2-eOverdracht4-0/Cert/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.eOverdracht4.LoadResources"] = ["dev.eOverdracht4.Test.LoadResources", "dev.eOverdracht4.Cert.LoadResources"]
    TARGETS["dev.eOverdracht4.Test.Receiving-XIS"] = Target("dev/FHIR3-0-2-eOverdracht4-0/Test/Receiving-XIS", TOUCHSTONE, WF_202001_DEV, {"authorization-token-id": "1234", "notificationEndpoint": "http://example.com/eOverdracht"})
    TARGETS["dev.eOverdracht4.Test.Sending-XIS-Nictiz-only"] = Target("dev/FHIR3-0-2-eOverdracht4-0/Test/Sending-XIS-Nictiz-only", [TOUCHSTONE, TOUCHSTONE], [WF_202001_DEV, WF_202001_DEV])
    TARGETS["dev.eOverdracht4.Cert.Receiving-XIS"] = Target("dev/FHIR3-0-2-eOverdracht4-0/Cert/Receiving-XIS", TOUCHSTONE, WF_202001_DEV, {"authorization-token-id": "1234", "notificationEndpoint": "http://example.com/eOverdracht"})
    TARGETS["dev.eOverdracht4.Cert.Sending-XIS-Nictiz-only"] = Target("dev/FHIR3-0-2-eOverdracht4-0/Cert/Sending-XIS-Nictiz-only", [TOUCHSTONE, TOUCHSTONE], [WF_202001_DEV, WF_202001_DEV])
    TARGETS["dev.eOverdracht4.Test"] = ["dev.eOverdracht4.Test.Receiving-XIS", "dev.eOverdracht4.Test.Sending-XIS-Nictiz-only"]
    TARGETS["dev.eOverdracht4.Cert"] = ["dev.eOverdracht4.Cert.Receiving-XIS", "dev.eOverdracht4.Cert.Sending-XIS-Nictiz-only"]
    TARGETS["dev.eOverdracht4"] = ["dev.eOverdracht4.Test", "dev.eOverdracht4.Cert"]

    TARGETS["Geboortezorg -- dev"] = Header()
    TARGETS["dev.Geboortezorg.LoadResources"] = Target("dev/FHIR3-0-2-Geboortezorg/_LoadResources", TOUCHSTONE, WF_202001_DEV, is_loadscript_folder = True)
    TARGETS["dev.Geboortezorg"] = Target("dev/FHIR3-0-2-Geboortezorg/Zwangerschapskaart", TOUCHSTONE, WF_202001_DEV)
    
    TARGETS["MedMij 6 -- dev"] = Header()
    TARGETS["dev.MM6.Test.LoadResources"] = Target("FHIR4-0-1-MedMij-Test/_LoadResources", TOUCHSTONE, WF_4_DEV, is_loadscript_folder = True)
    TARGETS["dev.MM6.Cert.LoadResources"] = Target("FHIR4-0-1-MedMij-Cert/_LoadResources", TOUCHSTONE, WF_4_DEV, is_loadscript_folder = True)
    TARGETS["dev.Immunization.1.Test.PHR"] = Target("FHIR4-0-1-MedMij-Test/Immunization-1-0/PHR-Client", TOUCHSTONE, WF_4_DEV)
    TARGETS["dev.Immunization.1.Test.XIS-Server-GetMedication"] = Target("FHIR4-0-1-MedMij-Test/Immunization-1-0/XIS-Server-GetMedication", TOUCHSTONE, WF_4_DEV)
    TARGETS["dev.Immunization.1.Cert.PHR"] = Target("FHIR4-0-1-MedMij-Test/Immunization-1-0/PHR-Client", TOUCHSTONE, WF_4_DEV)
    TARGETS["dev.Immunization.1.Cert.XIS-Server-GetMedication"] = Target("FHIR4-0-1-MedMij-Test/Immunization-1-0/XIS-Server-GetMedication", TOUCHSTONE, WF_4_DEV)
    TARGETS["dev.MP9.3.Test.MedicationData.Retrieve-MedMij"] = Target("FHIR4-0-1-MedMij-Test/MP9-3-0-0-beta/MedicationData/Retrieve-MedMij", TOUCHSTONE, WF_4_DEV)
    TARGETS["dev.MP9.3.Test.MedicationData.Serve-MedMij"] = Target("FHIR4-0-1-MedMij-Test/MP9-3-0-0-beta/MedicationData/Serve-MedMij", TOUCHSTONE, WF_4_DEV)
    TARGETS["dev.PatientCorrections.1.Test"] = Target("FHIR4-0-1-MedMij-Test/PatientCorrections-1-0", TOUCHSTONE, WF_4_DEV)

    TARGETS["FHIR 4 -- dev"] = Header()
    TARGETS["dev.FHIR4.Test.LoadResources"] = Target("FHIR4-0-1-Test/_LoadResources", TOUCHSTONE, WF_4_NO_AUTH_DEV, is_loadscript_folder = True)
    TARGETS["dev.FHIR4.Lab.3.Test"] = Target("FHIR4-0-1-Test/LaboratoryResults-3-0", TOUCHSTONE, WF_4_NO_AUTH_DEV)
    TARGETS["dev.MP9.3.Test"] = [
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/MedicationData/Receive", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/MedicationData/Retrieve", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/MedicationData/Send-Nictiz-intern", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/MedicationData/Serve", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/MedicationPrescription/Receive", TOUCHSTONE, WF_4_NO_AUTH_DEV),
        Target("dev/FHIR4-0-1-Test/MP9-3-0-0-beta/MedicationPrescription/Send-Nictiz-intern", TOUCHSTONE, WF_4_NO_AUTH_DEV),
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

    TARGETS["BgZ MSZ 1"] = Header()
    TARGETS["BgZ-MSZ-1.LoadResources"] = Target("FHIR3-0-2-BgZ-MSZ-1-0/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)

    TARGETS["MedMij 2019.01"] = Header()
    TARGETS["MM2019.01.Test.LoadResources"] = Target("FHIR3-0-2-MM201901-Test/_LoadResources", TOUCHSTONE, WF_201901, is_loadscript_folder = True)
    TARGETS["Medication-907.Test.XIS"] = Target("FHIR3-0-2-MM201901-Test/Medication-9-0-7/XIS-Server", TOUCHSTONE, WF_201901)
    TARGETS["Medication-907.Test-test"] = Target("FHIR3-0-2-MM201901-Test/Medication-9-0-7-test", TOUCHSTONE, WF_201901)

    TARGETS["MM2019.01.Cert.LoadResources"] = Target("FHIR3-0-2-MM201901-Cert/_LoadResources", TOUCHSTONE, WF_201901, is_loadscript_folder = True)

    TARGETS["MedMij 2020.01"] = Header()
    TARGETS["MM2020.01.Test.LoadResources"] = Target("FHIR3-0-2-MM202001-Test/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)
    TARGETS["MM2020.01.Cert.LoadResources"] = Target("FHIR3-0-2-MM202001-Cert/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)

    TARGETS["MedMij 2020.02"] = Header()
    TARGETS["MM2020.02.Test.LoadResources"] = Target("FHIR3-0-2-MM202002-Test/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)
    TARGETS["MM2020.02.Cert.LoadResources"] = Target("FHIR3-0-2-MM202002-Cert/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)

    TARGETS["eOverdracht 4"] = Header()
    TARGETS["eOverdracht.LoadResources"] = Target("FHIR3-0-2-eOverdracht4-0/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)
    TARGETS["eOverdracht4.Test.Receiving-XIS"] = Target("FHIR3-0-2-eOverdracht4-0/Test/Receiving-XIS", TOUCHSTONE, WF_202001, {"authorization-token-id": "1234", "notificationEndpoint": "http://example.com/eOverdracht"})
    TARGETS["eOverdracht4.Cert.Receiving-XIS"] = Target("FHIR3-0-2-eOverdracht4-0/Cert/Receiving-XIS", TOUCHSTONE, WF_202001, {"authorization-token-id": "1234", "notificationEndpoint": "http://example.com/eOverdracht"})

    TARGETS["Geboortezorg"] = Header()
    TARGETS["Geboortezorg.LoadResources"] = Target("FHIR3-0-2-Geboortezorg/_LoadResources", TOUCHSTONE, WF_202001, is_loadscript_folder = True)

    TARGETS["MedMij 6"] = Header()
    TARGETS["MedMij6.Test.LoadResources"] = Target("FHIR4-0-1-MedMij-Test/_LoadResources", TOUCHSTONE, WF_4, is_loadscript_folder = True)
    TARGETS["MedMij6.Cert.LoadResources"] = Target("FHIR4-0-1-MedMij-Cert/_LoadResources", TOUCHSTONE, WF_4, is_loadscript_folder = True)

    TARGETS["FHIR 4"] = Header()
    TARGETS["FHIR4.Test.LoadResources"] = Target("FHIR4-0-1-Test/_LoadResources", TOUCHSTONE, WF_4_NO_AUTH, is_loadscript_folder = True)

    # If set to true, wait for each test execution until it's complete before continuing.
    start_only = False

    def __init__(self):
        super().__init__()

        # Default to this monday
        monday = datetime.date.today() - datetime.timedelta(days = datetime.date.today().weekday())
        self.date_T = monday.strftime("%Y-%m-%d")

        if not ("TS_USER"  in os.environ and "TS_PASS" in os.environ):
            sys.exit("Set the environment variables 'TS_USER' and 'TS_PASS' to login to Touchstone")

        self.jira_table_summary = False
        self.executions = []
        self.__api_key = None

    def loginFrontend(self):
        """ Login to the Touchstone website. It requires the environment variables TS_USER and TS_PASS to be set. """
        self.open("https://touchstone.aegis.net/touchstone/login")

        self.select_form('form[id="loginForm"]')
        self["emailOrLoginID"] = os.environ["TS_USER"]
        self["password"] = os.environ["TS_PASS"]
        response = self.submit_selected()
        if "Sign Out" not in response.text:
            sys.exit("Couldn't login into Touchstone")

    def logoutFrontend(self):
        self.open("https://touchstone.aegis.net/touchstone/logout")

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
        i = 0
        for name in self.TARGETS.keys():
            if isinstance(self.TARGETS[name], Header):
                print (f"\n======== {name} ========")
            else:
                line = "%2d" % (i + 1)
                line += ".  " + name

                if type(self.TARGETS[name]) == list:
                    subtargets = [t for t in self.TARGETS[name] if type(t) == str]
                    if len(subtargets) > 0:
                        line += " (" + ", ".join(subtargets) + ")"
                print(line)
                i += 1

    def execute(self, *targets):
        """ Execute one or more targets, defined as number, mnemonic or list of these. """
        
        unwrapped = self.__unwrapTargets([], *targets)
        for target in unwrapped:
            self.executeTarget(target)

            if target.block_until_complete and (self.start_only == False or unwrapped.index(target) != len(unwrapped) - 1):
                # We need to wait until completion if this has been defined. This is also true if the --start-only flag
                # has been set, UNLESS we need to execute more scripts.
                print("  execution needs to finish before we can continue, switching to status reporting")
                self.awaitExecutions(True)

        if not self.start_only:
            self.awaitExecutions()
            if self.jira_table_summary:
                self.printJiraTable()

    def __unwrapTargets(self, unwrapped, *targets):
        """ Targets may be defined using numbers, mnemonics, and lists of these. This method recursively unwraps these
            inputs to a linear list of Targets. """
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
                    self.__unwrapTargets(unwrapped, self.TARGETS[target])
            elif type(target) == list:
                self.__unwrapTargets(unwrapped, *target)
            elif isinstance(target, Target):
                unwrapped.append(target)
        
        return unwrapped

    def uploadTarget(self, target: Target):
        print
        print(f"- Uploading {target.rel_path}")

        parts = target.rel_path.split("/")
        parent_folder = "/".join(parts[:-1])
        leaf_folder = parts[-1]
        response = self.open(f"https://touchstone.aegis.net/touchstone/testdefinitions?selectedTestGrp=/FHIRSandbox/Nictiz/{parent_folder}")
        if response.status_code != 200 or any(t.text.strip() == "Please select a node under Test Definitions." for t in self.page.find_all("span", class_="alertContent")):
            print(f"Parent folder '{parent_folder} for target {target.rel_path} doesn't exist or cannot be accessed, cannot upload")
            sys.exit(1)

        # Create a zip file to upload
        testscript_dir = pathlib.Path("../../Nictiz-testscripts")
        tmp_dir = pathlib.Path(tempfile.mkdtemp())
        shutil.make_archive(tmp_dir / leaf_folder, "zip", testscript_dir / target.rel_path)
        
        # Upload the file
        self.select_form('form[id="testGroupUploadForm"]')
        self["uploadFile"] = open(tmp_dir / f"{leaf_folder}.zip", "rb")
        self["parentGroupPath"] = "/FHIRSandbox/Nictiz/" + parent_folder
        self["canBeViewedBy"] = "BY_MY_ORG"
        self["canBeModifiedBy"] = "BY_MY_ORG"
        self["validator"] = "FHIR3-0-2-Nictiz-03"

        # Here comes the nasty part. MechanicalSoup doesn't set pass the content type of file uploads to Requests when
        # making the request, but Touchstone demands this to be set. So we need to intercept the MechanicalSoup
        # machinery here and modify what's passed to Requests.
        # First let MechanicalSoup construct the arguments to submit the form.
        request_kwargs = mechanicalsoup.Browser.get_request_kwargs(self.form.form,
            self.url,
            headers = {"Referer": self.url})
        # Now modify the "uploadFile entry" so that it includes the content type
        uploadFile = request_kwargs["files"]["uploadFile"]
        request_kwargs["files"]['uploadFile'] = (uploadFile[0], uploadFile[1], "application/zip")

        # Now we can make the acutual request, using the Requests Session in the MechanicalSoup StatefulBrowser.
        response = self.session.request(**request_kwargs)
        mechanicalsoup.Browser.add_soup(response, self.soup_config)

        #print(response)
        #print(response.soup)
        #print(response.soup.find_all("span", class_="alertContent"))
        if response.status_code == 200 and any(t.text.strip().startswith(f"The zip file '{leaf_folder}.zip' containing the test group '{leaf_folder}' has been uploaded successfully") for t in response.soup.find_all("span", class_="alertContent")):
            print("Success")
        else:
            print("No banana")

        shutil.rmtree(tmp_dir)

    def executeTarget(self, target: Target):
        """ Execute one specific target, defined by a Target object """
        print
        print(f"- Setting up {target.rel_path}")

        # Navigate to the relevant target and select all testscripts that are not loadscripts
        self.open(f"https://touchstone.aegis.net/touchstone/testdefinitions?selectedTestGrp=/FHIRSandbox/Nictiz/{target.rel_path}&activeOnly=true&contentEntry=TEST_SCRIPTS&ps=200")
        select_all = True
        self.select_form('form[id="testDefSearch"]')
        selected_testscripts = []
        for input in self.page.find_all("input", "selectedId"):
            if "load-resources-purgecreateupdate" in input.attrs["value"] and not target.is_loadscript_folder:
                select_all = False
            else:                
                selected_testscripts.append(input.attrs["value"])
        self["selectedTestScripts"] = selected_testscripts
        self["allSelected"] = True if select_all else False

        # Submit the form
        self.submit_selected()
        
        # Select the origin based on its name
        self._selectOrigDest("origin", target.origins)

        # Select the destination based on its name
        self._selectOrigDest("dest", target.destinations)

        # Populate all variables
        self.select_form('form[id="testSetupForm"]')
        if target.params == None:
            target.params = {"T": self.date_T}
        elif "T" not in target.params:
            target.params["T"] = self.date_T
        for param in target.params:
            for textarea in self.page.find_all("textarea"): # The name attribute of the targetted textarea is very long and I'm not sure if the beginning is guaranteed to be stable, so we're using a search on all textarea's here and filter out based on the latter part of the name
                if textarea.attrs["name"].endswith(f"variableSetups.variableSetupMap[{param}]"):
                    self[textarea.attrs["name"]] = target.params[param].strip()

        # There's a subtle bug between Touchstone and scripting (happened also with the Twill library) where a newline
        # is added to textareas on load (which is then used repeated back in the default value on a new execution, and
        # a newline is added to it, and so forth). So we need to go over all textareas and strip the whitespace.
        for textarea in self.page.find_all("textarea"):
            self[textarea.attrs["name"]] = textarea.text.strip()

        # The submission expects a field called "execute", which is normally sent when clicking the "execute" button.
        # However, for some reason this field is not included when programmatically doing this.
        self.form.set("execute", "", True)
        
        # The submission also expects that all hidden fields containing the default values for variables are _not_ sent
        # along. Or rather, if they are present the actual input value is ignored or so it seems. So we have to remove
        # these fields.
        for input in self.page.find_all("input", class_="ud_defaults"):
            input.extract()

        response = self.submit_selected()
        if response.status_code == 200:
            print(f"  execution started on {self.url}")
            execution_id = self.url.replace("https://touchstone.aegis.net/touchstone/execution?exec=", "")
            self.executions.append(Execution(target, execution_id))
        else:
            print(f"  couldn't start execution for {target.rel_path}")

    def awaitExecutions(self, blocking_only = False):
        """ Await the started executions by polling the Touchstone API, and report back the results. """
        print("\n### Status ###")

        if blocking_only:
            executions = [e for e in self.executions if e.target.block_until_complete and (e.status == "Running" or e.status == "")]
        else:
            executions = self.executions

        last_polled_at = datetime.datetime(1970, 1, 1)
        
        waiting = len(executions) > 0
        while waiting:
            
            waiting = False
            for execution in executions:
                if execution.status == "" or execution.status == "Running":
                    sleep_time = 4 - (datetime.datetime.now() - last_polled_at).seconds
                    if sleep_time > 0: time.sleep(sleep_time)
                    response = requests.get("https://touchstone.aegis.net/touchstone/api/testExecution/" + execution.execution_id, headers = {
                        "API-Key": self.apiKey(),
                        "Accept": "application/json"
                    })
                    last_polled_at = datetime.datetime.now()

                    if response.status_code != 200 or "status" not in response.json():
                        execution.status = "Unknown"
                        print(response)
                    else:
                        execution.status = response.json()["status"]
                        execution.duration = response.json()["duration"]

                        stats = response.json()["statusCounts"]
                        execution.total = stats["numberOfTests"]
                        execution.passes = 0 if "numberOfTestPasses" not in stats else stats["numberOfTestPasses"]
                        execution.warns =  0 if "numberOfTestPassesWarn" not in stats else stats["numberOfTestPassesWarn"]
                        execution.fails =  0 if "numberOfTestFailures" not in stats else stats["numberOfTestFailures"]
                
                total_completed = execution.passes + execution.warns + execution.fails
                if execution.status == "Unknown":
                    line = "  Status couldn't be retrieved"
                elif execution.status == "Running":
                    line = f"  {total_completed}/{execution.total} tests completed with {execution.passes} passes, {execution.warns} warnings and {execution.fails} failures (running for {execution.duration})"
                    waiting = True
                else:
                    line = "  "
                    line += "✅" if execution.status == "Passed" else "❌"
                    line += f" {execution.passes} passed, {execution.warns} passed with warnings, {execution.fails} failed"
                    if execution.total > (total_completed):
                        line += f" ({execution.total - total_completed} never started)"
                
                print("\033[2K- " + execution.target.rel_path)
                print("\033[2K" + line)
            
            if waiting:
                print(f"\033[{len(executions) * 2 + 1}A")
        
        print("### End status ###\n")

    def printJiraTable(self):
        print("### Jira table ###")
        for execution in self.executions:
            line =  f"|{execution.target.rel_path}|"
            line += "(/)" if execution.status == "Passed" else "(x)"
            if execution.fails > 0:
                line += f"\n{execution.fails} x failures"
            if execution.warns > 0:
                line += f"\n{execution.warns} x warning"
            line += f"| | |[https://touchstone.aegis.net/touchstone/execution?exec={execution.execution_id}]|"
            print(line)

    def _selectOrigDest(self, type, values):
        """ Select origin or destination dropdowns on the Touchstone UI during execution setup.
            * type: "origin" or "dest"
            * values: A list of origins or destinations to select.
        """
        self.select_form('form[id="testSetupForm"]')

        for i in range(len(values)):
            if i == 0:
                dropdown_ids = [f"main{type.lower()}1TsSelect", f"single{type.capitalize()}TsSelect"] # If a origin/destination is explicitly defined in the TestScript, the select box has a different id then when it is absent
            else:
                dropdown_ids = [f"main{type.lower()}{i + 1}TsSelect"]

            for id in dropdown_ids:
                dropdowns = self.page.find_all("select", id=id)
                if len(dropdowns) > 0:
                    self[dropdowns[0].attrs["name"]] = values[i]

if __name__ == "__main__":
    just_fix_windows_console()

    launcher = Launcher()

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", help = "List all available targets", action = "store_true")
    parser.add_argument("-T", help = f"Date T to use (default is '{launcher.date_T}')")
    parser.add_argument("--start-only", action = "store_true", help = "Just launch the executions, don't wait for them to finish and don't report the results, unless it's explicitly defined that an execution should finish before continuing")
    parser.add_argument("--jira-table", action = "store_true", help = "Print a summary in Jira table format after completion (ignored if --start-only is provided)")
    parser.add_argument("target", nargs = "*", help = "The targets to execute (both numbers and mnemonics are supported)")
    args = parser.parse_args()

    if args.T != None:
        launcher.date_T = args.T
    launcher.start_only = args.start_only
    launcher.jira_table_summary = args.jira_table

    if args.list:
        launcher.printTargets()
        exit(0)

    elif len(args.target) == 0:
        print("You need to specify at least one target (use --list to show the available targets)")
        exit(1)
    try:
        launcher.loginFrontend()
        launcher.execute(*args.target)
        #launcher.uploadTarget(launcher.TARGETS["dev.eAppointment2.Test"])

    finally:
        # Always try to logout, otherwise we'll have too many open sessions.
        launcher.logoutFrontend()
