#!/usr/bin/env python3

import argparse
import collections
import datetime
import enum
import mechanicalsoup
import os
import pathlib
import re
import requests
import shutil
import sys
import tempfile
import time
import yaml

from colorama import just_fix_windows_console
from dataclasses import dataclass

class ExecutionTarget:
    """
    Container for test execution settings. It contains the following data:
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
    def __init__(self, rel_path):
        self.rel_path             = rel_path
        self.origins              = None
        self.destinations         = None
        self.params               = {}
        self.block_until_complete = None
        self.is_loadscript_folder = False
    
    def setLoadScriptFolder(self, is_loadscript_folder):
        self.is_loadscript_folder = is_loadscript_folder
        if is_loadscript_folder:
            self.block_until_complete = True

    def hasOrigins(self):
        return self.origins != None

    def hasDestinations(self):
        return self.destinations != None

    def setOrigins(self, origins):
        self.origins = [origins] if type(origins) == str else origins

    def setDestinations(self, destinations):
        self.destinations = [destinations] if type(destinations) == str else destinations

class UploadTarget:
    """
    Container for folder upload settings. It contains the following data:
    * path: the path to the folder as a Pathlib.path object.
    * rel_path: the relative path, Unix-style and compared to the root of the repo, of the folder with the
                TestScripts.
    * kind: either "dev" or "production".
    * access: a list of all "Viewable by" access groups.
    * validator: the name of the validation environment for the folder.
    """

    def __init__(self, path: pathlib.Path, rel_path, kind):
        self.path = path
        self.rel_path = rel_path
        self.kind = kind
        self.access = None
        self.validator = None

    def hasAccess(self):
        return self.access != None
   
    def setAccess(self, access):
        self.access = [access] if type(access) == str else access

@dataclass
class Execution:
    target: ExecutionTarget
    execution_id: str
    status: str = ""
    total: int = 0
    passes: int = 0
    warns: int =  0
    fails: int =  0
    duration: str = ""
    
class KnownTargets:
    """ Class to translate the file tree in the testscripts repo to Upload/ExecutionTarget's, based on the properties
        defined in a properties yaml file. """
    def __init__(self, root, properties_file):
        self.root = pathlib.Path(root) / "dev"
        self.dirs = self.__getRecursiveDirs([], self.root)
        self.properties_dev, self.properties_prod = self.loadProperties(properties_file)

    def list(self, exclude_reference = False):
        """ List all directories with a number. If exclude_reference is set to True, _reference folders are not shown,
            although they are included in the numbering to keep the numbering consistent accross uses. """
        i = 1
        for dir in self.dirs:
            if not (exclude_reference and dir.name == "_reference"):
                print(f"{i}. {dir.relative_to(self.root)}")
            i += 1

    def __getRecursiveDirs(self, curr_list, curr_dir):
        """ Helper method to scan the target folder recursively. """
        for dir in curr_dir.iterdir():
            if dir.is_dir():
                if dir.name == "_reference": # Don't descend into _reference
                    curr_list.append(dir)
                elif not dir.name.startswith("."):
                    curr_list.append(dir)
                    curr_list = self.__getRecursiveDirs(curr_list, dir)

        return curr_list

    def get(self, arg):
        """ Return the path corresponding to the number shown by list(). """
        try:
            index = int(arg)
            return self.dirs[index - 1]
        except ValueError:
            raise Exception(f"No such target: {arg}")

    def loadProperties(self, properties_file):
        """ Load the properties file and return the result in two dictionaries: one for the dev environment, and one
            for the production environment. The dicts are actually OrderedDicts where the keys are base folders
            containing a particular set of settings. These keys are sorted from fine to course, so that the first match
            can be used as the most precise specification for that folder. """
        with open(properties_file, "r") as f:
            raw = yaml.safe_load(f)
        
        _dev_properties = self.__walkProperties({}, self.root, raw["dev"])
        _prod_properties = self.__walkProperties({}, self.root, raw["production"])

        _dev_keys = sorted(_dev_properties.keys(), reverse=True)
        _prod_keys = sorted(_prod_properties.keys(), reverse=True)
        dev_properties = collections.OrderedDict()
        prod_properties = collections.OrderedDict()
        for key in _dev_keys:
            dev_properties[key] = _dev_properties[key]
        for key in _prod_keys:
            prod_properties[key] = _prod_properties[key]
        
        return dev_properties, prod_properties

    def __walkProperties(self, properties, curr_path, obj):
        """ Helper method to recursively walk the paths defined in the properties file. """
        for key in obj:
            if key in ["params", "origins", "destinations", "block until complete"] or type(obj[key]) == str or type(obj[key]) == list:
                if curr_path not in properties:
                    properties[curr_path] = {}
                properties[curr_path][key] = obj[key]
            elif type(obj[key]) == dict:
                self.__walkProperties(properties, curr_path/key, obj[key])
        
        return properties

    def getUploadTarget(self, target, kind):
        """ Return the parameters needed for uploading the target, where target is the index number of
            KnownTargets. """
        dir = self.get(target)

        rel_path = dir.relative_to(self.root).as_posix()
        if kind == "dev":
            rel_path = "dev/" + rel_path
        target = UploadTarget(dir, rel_path, kind)

        properties = self.properties_dev if kind == "dev" else self.properties_prod
        for root in properties.keys():
            if dir == root or root in dir.parents:
                if not target.hasAccess() and "access" in properties[root]:
                    target.setAccess(properties[root]["access"])
                if not target.validator and "validator" in properties[root]:
                    target.validator = properties[root]["validator"]
            if target.hasAccess() and target.validator:
                return target
        
        if not target.hasAccess():
            raise Exception(f"Couldn't get the access rights from the properties file for {target.rel_path}")
        if target.validator == None:
            raise Exception(f"Couldn't find a validator in the properties file for {target.rel_path}")

    def getExecutionTarget(self, target, kind):
        """ Return the parameters needed for executing the target, where target is the index number of
            KnownTargets. """
        dir = self.get(target)

        rel_path = dir.relative_to(self.root).as_posix()
        if kind == "dev":
            rel_path = "dev/" + rel_path
        target = ExecutionTarget(rel_path)
        target.setLoadScriptFolder(dir.name == "_LoadResources")

        properties = self.properties_dev if kind == "dev" else self.properties_prod
        for root in properties.keys():
            if dir == root or root in dir.parents:
                if not target.hasOrigins() and "origins" in properties[root]:
                    target.setOrigins(properties[root]["origins"])
                if not target.hasDestinations() and "destinations" in properties[root]:
                    target.setDestinations(properties[root]["destinations"])
                if "params" in properties[root]:
                    target.params = target.params | properties[root]["params"]
                if target.block_until_complete == None and "block until complete" in properties[root]:
                    target.block_until_complete = properties[root]["block until complete"]
        
        if not target.hasOrigins():
            raise Exception(f"Couldn't get the origin(s) from the properties file for {target.rel_path}")
        if not target.hasDestinations():
            raise Exception(f"Couldn't get the destination(s) from the properties file for {target.rel_path}")
        return target

class Touchstone(mechanicalsoup.StatefulBrowser):
    MAX_PARALLEL_EXECUTIONS = 4

    """ Enum for the different things we can wait for. """
    class AwaitMode(enum.Enum):
        ALL      = 0   # Await until all executions have finished
        BLOCKING = 1   # Await only until all executions marked "blocking" have finished
        MAX      = 2   # Await until the number of parallel executions is below MAX_PARLLEL_EXECUTIONS

    def __init__(self):
        super().__init__()

        just_fix_windows_console()

        # Default to this monday
        monday = datetime.date.today() - datetime.timedelta(days = datetime.date.today().weekday())
        self.date_T = monday.strftime("%Y-%m-%d")

        if not ("TS_USER"  in os.environ and "TS_PASS" in os.environ):
            sys.exit("Set the environment variables 'TS_USER' and 'TS_PASS' to login to Touchstone")

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
        """ Return the API-Key value needed for using the Touchstone API. If this key is not yet known, a new API
            session will be started. """

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

    def executeTargets(self, targets, start_only):
        """ Execute one the provided list of ExecutionTargets. If start_only is set to True, don't waint for the
            execution to finish. """
        
        for target in targets:
            self.executeTarget(target)

            if target.block_until_complete and (start_only == False or targets.index(target) != len(unwrapped) - 1):
                # We need to wait until completion if this has been defined. This is also true if the --start-only flag
                # has been set, UNLESS we need to execute more scripts.
                self.awaitExecutions(Touchstone.AwaitMode.BLOCKING)

        if not start_only:
            self.awaitExecutions(Touchstone.AwaitMode.ALL)

    def uploadTarget(self, target: UploadTarget):
        """ Upload a target to Touchstone. """

        print
        print(f"- Uploading {target.rel_path}")

        # We're uploading the folder in its parent folder, so let's figure that one out first.
        parts = target.rel_path.split("/")
        parent_folder = "/".join(parts[:-1])
        leaf_folder = parts[-1]
        parent_group_path = "/FHIRSandbox/Nictiz"
        if parent_folder != "":
            parent_group_path += "/" + parent_folder
        
        response = self.open(f"https://touchstone.aegis.net/touchstone/testdefinitions?selectedTestGrp={parent_group_path}")
        if response.status_code != 200 or any(t.text.strip() == "Please select a node under Test Definitions." for t in self.page.find_all("span", class_="alertContent")):
            print(f"Parent folder '{parent_folder}' for target {target.rel_path} doesn't exist or cannot be accessed, cannot upload")
            sys.exit(1)

        # Create a zip file to upload
        tmp_dir = pathlib.Path(tempfile.mkdtemp())
        if target.kind == "dev": # Filter out groupProps.json on dev uploads.
            filtered_dir = pathlib.Path(tempfile.mkdtemp()) / leaf_folder
            shutil.copytree(target.path, filtered_dir, ignore = shutil.ignore_patterns("groupProps.json"))
            shutil.make_archive(tmp_dir / leaf_folder, "zip", filtered_dir)
            shutil.rmtree(filtered_dir)
        else:
            shutil.make_archive(tmp_dir / leaf_folder, "zip", target.path)
        
        # Upload the file
        self.select_form('form[id="testGroupUploadForm"]')
        self["uploadFile"] = open(tmp_dir / f"{leaf_folder}.zip", "rb")
        self["parentGroupPath"] = parent_group_path
        self["canBeModifiedBy"] = "BY_MY_ORG"

        self["canBeViewedBy"] = "BY_MY_ORG_GROUP" # Default to this in case the actual access is one or more org groups. It will be overridden in the other situations.
        for access in target.access:
            el = self.page.find(lambda tag: tag.name == "label" and tag.text.strip().lower() == access.lower())
            if el:
                el = el.find("input")
                self[el.attrs["name"]] = el.attrs["value"]
            else:
                print(f"Access level {access} not found")
                return False
        self.form.set_select({"validator": target.validator})

        ok_msg = f"The zip file '{leaf_folder}.zip' containing .* has been uploaded successfully"
        response = self.submit_selected()

        shutil.rmtree(tmp_dir)

        if response.status_code == 200 and any(re.search(ok_msg, t.text) for t in self.page.find_all("span", class_="alertContent")):
            print("Success")
            return True
        else:
            print("Upload failed")
            for alert in self.page.find_all("span", class_="alertContent"):
                print(f"- {alert.text.strip()}")
            return False

    def _request(self, form, url=None, **kwargs):
        """ Overriden method of mechanicalsoup.Browser to add the content type to zip file uploads.
            MechanicalSoup doesn't pass the content type of file uploads to Requests when making the POST request, but
            Touchstone demands this to be set. """

        request_kwargs = mechanicalsoup.Browser.get_request_kwargs(form, url, **kwargs)

        if "files" in request_kwargs and "uploadFile":
            for identifier in request_kwargs["files"].keys():
                file_tuple = request_kwargs["files"][identifier]
                if file_tuple[0].endswith(".zip"):
                    request_kwargs["files"][identifier] = (file_tuple[0], file_tuple[1], "application/zip")
        
        return self.session.request(**request_kwargs)

    def executeTarget(self, target: ExecutionTarget):
        """ Execute one specific target, defined by a ExecutionTarget object """
        
        # First, wait until there are execution slots available
        self.awaitExecutions(Touchstone.AwaitMode.MAX)

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

    def awaitExecutions(self, await_mode):
        """ Await the started executions by polling the Touchstone API, and report back the results. """
        
        if await_mode == Touchstone.AwaitMode.BLOCKING:
            executions = [e for e in self.executions if e.target.block_until_complete and (e.status == "Running" or e.status == "")]
        else:
            executions = self.executions

        # Figure out if we actually do need to start waiting
        if await_mode == Touchstone.AwaitMode.MAX:
            need_to_wait = sum([1 for execution in executions if execution.status in ["Running", ""]]) >= self.MAX_PARALLEL_EXECUTIONS
        else:
            need_to_wait = any([True for execution in executions if execution.status in ["Running", ""]])
        
        if need_to_wait:
            if await_mode == Touchstone.AwaitMode.MAX:
                print("  maximum number of parallel executions started, so we need to wait a bit before we can continue")
            elif await_mode == Touchstone.AwaitMode.BLOCKING:
                print("  execution needs to finish before we can continue")
            else:
                print("  waiting for all executions to finish")
            print("\n### Status ###")

        last_polled_at = datetime.datetime(1970, 1, 1)

        waiting = need_to_wait
        while waiting:          
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
                else:
                    line = "  "
                    line += "✅" if execution.status == "Passed" else "❌"
                    line += f" {execution.passes} passed, {execution.warns} passed with warnings, {execution.fails} failed"
                    if execution.total > (total_completed):
                        line += f" ({execution.total - total_completed} never started)"
                
                print("\033[2K- " + execution.target.rel_path)
                print("\033[2K" + line)
            
            if await_mode == Touchstone.AwaitMode.MAX:
                waiting = sum([1 for execution in executions if execution.status == "Running"]) >= self.MAX_PARALLEL_EXECUTIONS
            else:
                waiting = any([True for execution in executions if execution.status == "Running"])

            if waiting:
                # Move the cursor to the beginning of the status report block
                print(f"\033[{len(executions) * 2 + 1}A")
        
        if need_to_wait:
            if await_mode == Touchstone.AwaitMode.ALL:
                print("### End status ###\n")
            else:
                # If we were awaiting MAX or BLOCKING, the process flow continues so we need to erase everything
                print(f"\033[{len(executions) * 2 + 2}A\033[J\033[A")

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

