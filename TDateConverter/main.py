import tkinter.dialog
import xml.etree.ElementTree as ET
import os
import re
import datetime
from tkinter import *
from tkinter import filedialog
from tkinter.messagebox import showerror, showwarning, showinfo

os.chdir("..")
workingDir = os.getcwd()

root = tkinter.Tk()
root.title("Convert file")
root.resizable(True, True)
root.geometry('700x300')

a = []
b = []

sourceMessage = tkinter.Label(root, text="source directory: None selected")
destinationMessage = tkinter.Label(root, text="destination directory: None selected")
doneMessage = tkinter.Label(root, text="Conversion successful")


def select_sourcedir():
    selected_sourceDir = filedialog.askdirectory(initialdir=workingDir, title="Select source")
    a.append(selected_sourceDir)
    sourceMessage.config(text=selected_sourceDir)


def select_destinationdir():
    selected_destinationDir = filedialog.askdirectory(initialdir=workingDir, title="Select source")
    b.append(selected_destinationDir)
    destinationMessage.config(text=selected_destinationDir)


def test_selection():
    if len(a) == 0 and len(b) == 0:
        print("select source first")
        tkinter.messagebox.showerror(message="Select source and destination first")
    elif len(b) == 0:
        print("select destination first")
        tkinter.messagebox.showerror(message="Select destination first")
    elif len(a) == 0:
        tkinter.messagebox.showerror(message="Select source first")
    else:
        fill_dates()


sourceButton = tkinter.Button(root, text='Open source directory', command=select_sourcedir)
destinationButton = tkinter.Button(root, text='Open destination directory', command=select_destinationdir)
runButton = tkinter.Button(root, text='Run', command=test_selection)

# Pack everything in right order
sourceButton.pack(ipadx=5, ipady=5, expand=True)
sourceMessage.pack()
destinationButton.pack(ipadx=5, ipady=5, expand=True)
destinationMessage.pack()
runButton.pack(ipadx=5, ipady=5, expand=True)


def fill_dates():
    sourceDir = workingDir + "\\fhir_instance_bundles"
    destinationDir = workingDir + "\\fhir_instance_bundles_datetime"
    if len(a) != 0:
        sourceDir = a[len(a) - 1]
    if len(b) != 0:
        destinationDir = b[len(b) - 1]

    try:
        ET.register_namespace('', "http://hl7.org/fhir")
        for filename in os.listdir(sourceDir):
            f = os.path.join(sourceDir, filename)
            # checking if it is a file
            if os.path.isfile(f):
                file = ET.parse(f)
                # loop over all values
                for elem in file.iter():
                    # if value contains an attribute
                    if 'value' in elem.attrib:
                        # Check if t-date
                        if '$' in elem.attrib['value']:
                            # print("old: " + elem.attrib['value'])
                            time = ""
                            # Check if time is present
                            if "}T" in elem.attrib['value']:
                                index = elem.attrib['value'].index("}T")
                                time = elem.attrib['value'][index + 1:]

                            # Is it a date addition or retraction
                            if "+" in elem.attrib['value']:
                                newDate = (datetime.date.today() + datetime.timedelta(
                                    days=int(re.search(r'\d+', elem.attrib['value']).group()))).strftime("%Y-%m-%d")
                            else:
                                newDate = (datetime.date.today() + datetime.timedelta(
                                    days=-int(re.search(r'\d+', elem.attrib['value']).group()))).strftime("%Y-%m-%d")

                            elem.attrib['value'] = newDate + time
                            # print("new: " + elem.attrib['value'])

                file.write(destinationDir + "\\" + filename)
                index = -1
        doneMessage.pack()
    except:
        tkinter.messagebox.showerror(message="An error occurred while converting")



root.mainloop()

