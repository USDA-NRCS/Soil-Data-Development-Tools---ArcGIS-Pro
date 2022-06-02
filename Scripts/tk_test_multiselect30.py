# tk_test_multiselect30.py
#
# This is the first script where I try to incorporate balloon text

import os, sys
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import font
import tkinter.tix as tix

class Balloon(tix.Balloon):

    # A modified tix popup balloon (to change the default delay, bg and wraplength)

    init_after = 1250  # Milliseconds
    wraplength = 300  # Pixels

    def __init__(self, master):
        bg = window.cget("bg")
        # Call the parent
        super().__init__(master, initwait=self.init_after)
        # Change background colour
        for i in self.subwidgets_all():
            i.config(bg=bg)
        # Modify the balloon label
        self.message.config(wraplength=self.wraplength)


# Learning Tkinter GUI
# Simple listbox with multiple choices
# Version 1.0

# variable prefixes and object type
# ******************************************************************
# window : menu
# frm : frame
# cbx : checkbox
# ent : text entry
# lbl  : label text
# lbx : listbox
# txt  : text box entry allows multiple lines, etc.
# tab : tab
# ?
#

# ******************************************************************
def ShowSelected(event):
    surveyAreas = []
    totalCnt = lbxDownloads.size()   # total count
    selectedSet = lbxDownloads.curselection()
    selCnt = len(selectedSet)

    for i in selectedSet:
        subFolder = lbxDownloads.get(i)
        surveyAreas.append(subFolder)

    msgCount = str(selCnt) + " of " + str(totalCnt) + " survey areas selected for processing"
    print(msgCount)
    lblText.set(msgCount)

    return

# ******************************************************************
def ClearSelection(event):
    surveyAreas = []
    lbxDownloads.selection_clear(0, tk.END)
    totalCnt = lbxDownloads.size()
    selectedSet = lbxDownloads.curselection()
    selCnt = len(selectedSet)
    msgCount = "ClearSelection: " + str(selCnt) + " of " + str(totalCnt) + " survey areas selected for processing"
    lblText.set(msgCount)

    print(msgCount)
    
    return

# ******************************************************************
def SwitchSelection(event):
    surveyAreas = []
    totalCnt = lbxDownloads.size()
    selectedSet = lbxDownloads.curselection()
    selCnt = len(selectedSet)

    for idx in range(totalCnt):
        if not idx in selectedSet:
            lbxDownloads.select_set(idx)

        else:
            lbxDownloads.selection_clear(idx)
        
    selectedSet = lbxDownloads.curselection()
    selCnt = len(selectedSet)
    msgCount = "SwitchSelection: " + str(selCnt) + " of " + str(totalCnt) + " survey areas selected for processing"
    lblText.set(msgCount)

    print(msgCount)
    
    return

# ******************************************************************
def SelectAll(event):
    #lblText.set("Top of SelectAll function")
    #lbxDownloads.focus_set()
    totalCnt = lbxDownloads.size()

    if totalCnt > 0:
        lbxDownloads.select_set(0, tk.END)
        totalCnt = lbxDownloads.size()
        selectedSet = lbxDownloads.curselection()
        selCnt = len(selectedSet)
        msgCount = "SelectAll: " + str(selCnt) + " of " + str(totalCnt) + " survey areas selected for processing"
        lblText.set(msgCount)

        # This print statement is working, but not the lbl
        print("SelectAll: ", msgCount)

    else:
        lblText.set("SelectAll: No values in listbox, totalCnt")
        
    return

# ******************************************************************
def ValidateFilter(event):
    
    # Once the entFilter has been populated, make sure characters are valid
    # alpha-numeric or asterik. Do I need to add underscore or dash?
    wildCard = entFilter.get().upper()
    inputFolder = entFolder.get()
    
    newWildCard = ""

    for c in wildCard:
        num = ord(c)
        
        if num == 42 or num in range(48, 58) or num in range(65, 91) or num in range(97, 123):
            newWildCard += c
          
    entFilter.delete(0, tk.END)
    entFilter.insert(0, newWildCard)

    # Do I need to clear selected set or just the message?
    # msgCount = 
    lblText.set("No survey areas selected for processing (ValidateFilter)")
    
    if newWildCard and inputFolder:
        # Get a listing of SSURGO downloads using this new wildcard and folder
        GetDownloads()

    else:
        # Remove any previously existing items from the listbox
        lbxDownloads.delete(0, tk.END)

    return
  
# ******************************************************************
def GetFolder(event):
    # Get local folder where SSURGO downloads are stored
    inputFolder = fd.askdirectory()
    sLen = max(30, int(round( (1.25 * len(inputFolder)), 0)))
    wildCard = entFilter.get().upper()
    
    #print("SSURGO Download Folder: '" + inputFolder + "'")
    entFolder.delete(0, tk.END)
    entFolder.configure(width=sLen)
    entFolder.insert(0, inputFolder)
    #print("entFolder state: '" + entFolder["state"])

    if inputFolder and wildCard:
        print("Getting download list")
        GetDownloads()
    
    return

# ******************************************************************
def GetDownloads():
    # Once the entFilter and entFolder have been populated,
    # try to get a listing of subfolders

    surveyList = list()  # list of download folder names
    matchedList = list() # list of 
    inputFolder = entFolder.get()

    if not inputFolder:
        return

    dirList = os.listdir(inputFolder)
    dupList = list()

    # Check each subfolder to make sure it is a valid SSURGO dataset
    # validation: has 'soil_' prefix and contains a spatial folder and a soilsmu_a shapefile
    # and matches one of the AREASYMBOL values in the legend table

    # To list all SSURGO downloads, the user can enter a single asterik.
    wildCard = entFilter.get().replace("*", "")

    # 
    if wildCard == "":
      # Return any folder that contains spatial and tabular subfolders
      for subFolder in dirList:
        areasym = subFolder[-5:].upper()
      
        if os.path.isdir( os.path.join( inputFolder, os.path.join( subFolder, "spatial" ) ) ) and  \
          os.path.isdir( os.path.join( inputFolder, os.path.join( subFolder, "tabular" ) ) ):
          # Found the first and hopefully the only matching SSURGO download folder

          if not areasym in matchedList:
            # Found the first and hopefully the only matching SSURGO download folder.
            # Add the foldername to the import list
            matchedList.append(areasym)
            surveyList.append(subFolder)

          else:
            # Found another matching SSURGO download folder. 
            # Must be a different folder naming convention?
            # Skip downloading this version, but let the user know there is more than one match.
            dupList.append(subFolder)
            
    else:
      # Using wildcard filter on subdirectory name
      for subFolder in dirList:
        areasym = subFolder[-5:].upper()
        
        # Found another matching SSURGO download folder. 
        # Must be a different folder naming convention?
        # Skip downloading this version, but let the user know there is more than one match.
          
        if areasym.startswith(wildCard) and \
          os.path.isdir( os.path.join( inputFolder, os.path.join( subFolder, "spatial" ) ) ) and  \
          os.path.isdir( os.path.join( inputFolder, os.path.join( subFolder, "tabular" ) ) ):
          # Found the first and hopefully the only matching SSURGO download folder

          if not areasym in matchedList:
            # Found the first and hopefully the only matching SSURGO download folder.
            # Add the foldername to the import list
            matchedList.append(areasym)
            surveyList.append(subFolder)

          else:
            # Found another matching SSURGO download folder. 
            # Must be a different folder naming convention?
            # Skip downloading this version, but let the user know there is more than one match.
            dupList.append(subFolder)

    if len(surveyList) > 0:

      lbxDownloads.delete(0, tk.END)

      # Add the list of values to the listbox
      for item in range(len(surveyList)): 
          lbxDownloads.insert(tk.END, surveyList[item]) 
          #lbxDownloads.itemconfig(item, bg=orange)

      totalCnt = lbxDownloads.size()
      msgCount = "0 of " + str(totalCnt) + " survey areas selected for processing"
      lblText.set(msgCount)

    else:
        lbxDownloads.insert(tk.END, "No Data")

    if len(dupList) > 0:
        msgDups = str(len(dupList)) + " apparent duplicate downloads found: " + ", ".join(dupList)
        dupWidth = len(msgDups)
        lblDups.config(text=msgDups, width=dupWidth)

    else:
        lblDups.config(text="")

    btnFolder.configure(relief=tk.RAISED, state=tk.ACTIVE)
    
    del surveyList, matchedList, dupList, subFolder

    return

# ******************************************************************
def GetInputDB(event):
    # Get local folder where SSURGO downloads are stored
    dbFolder = os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])), "TemplateDatabases")

    inputDB = fd.askopenfilename(
        initialdir = dbFolder,
        title = "Select input database (.sqlite or .gpkg)",
        filetypes = (
            ("Spatialite", "*.sqlite"),
            ("Geopackage", "*.gpkg"))
        )
    
    entDBinput.delete(0, tk.END)
    entDBinput.insert(0, inputDB)

    return

# ******************************************************************
def SetOutputDB(event):
    # Get local folder where SSURGO downloads are stored
    #dbFolder = os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])), "TemplateDatabases")

    inputDB = entDBinput.get()
    dbName, dbExt = os.path.splitext(inputDB)

    if dbExt == ".sqlite":
        dbType = "Spatialite"

    elif dbExt == ".gpkg":
        dbType = "Geopackage"

    outputDB = fd.asksaveasfilename(
        initialdir = "/",
        title = "Set output database",
        filetypes = ((dbType, "*" + dbExt),)
    )

    dbName, ext = os.path.splitext(outputDB)
    outputDB = dbName + dbExt

    entDBoutput.delete(0, tk.END)
    entDBoutput.insert(0, outputDB)

    return

# ******************************************************************
def SetCRS(event):
    # Get output coordinate system from listbox and apply to associated text label
    selectedSet = lbxCRS.curselection()
    selCnt = len(selectedSet)  # should always be 1 (single_select mode)
    
    for i in selectedSet:
        crs = lbxCRS.get(i)

        if crs == "":
            crs = "EPSG:4326"
        
    msgCRS = crs + " output coordinate system"
    # msgCRS = "Output coordinate system: " + crs
    crsWidth = len(msgCRS)
    lblCRS.config(text=msgCRS, width=crsWidth)


    return
    
# ******************************************************************
def Close(event):
    window.destroy()
    
    return
  
# ******************************************************************
# ******************************************************************
# main
# ******************************************************************

ltGray = "#ecedf3" # light gray
medGray = "#bdc1d6" # medium gray
orange = "#ffa500" # orange
cyan = "#00daff" # cyan
medGreen = "#00cc84" # medium green
gray = "#C0C0C0"

window = tix.Tk()                           # Menu frame
#window = tk.Tk()                           # Menu frame

window.title('SSURGO Data Picker - By Areasymbol')          # Title bar for menu
window.geometry('600x900')                 # Menu size
var = tk.StringVar()                       # Not sure how this is being used, but doesn't work without it

#

scriptfile = sys.argv[0]
print("Script file", scriptfile)

# assortment of colors for backgrounds


window.grid_rowconfigure(0, weight=10)     # entries frame
window.grid_rowconfigure(1, weight=2)      # button frame
window.grid_rowconfigure(2, weight=20)     # listbox and status messages
#window.grid_rowconfigure(3, weight=20)     # listbox and status messages
window.grid_columnconfigure(0, weight=8)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)
window.grid_columnconfigure(3, weight=1)

# Create frame at the top (entry widgets go here)
# if not specified with rowconfigure, height of a row will match tallest grid cell
# if not specified with columnconfigure, width of a column will be max of widget widths
#
bgEntries = "cyan"
frmEntries = tk.Frame(master=window, width=150, height=175, relief=tk.RAISED, borderwidth=5, bg=gray)

# configure 6 rows (all wt=1), 3 columns (wt=1,6,1)
frmEntries.grid_rowconfigure(0, weight=2)
frmEntries.grid_rowconfigure(1, weight=1)
frmEntries.grid_rowconfigure(2, weight=1)
frmEntries.grid_rowconfigure(3, weight=1)
frmEntries.grid_rowconfigure(4, weight=1)
frmEntries.grid_rowconfigure(5, weight=1)
frmEntries.grid_rowconfigure(6, weight=1)
frmEntries.grid_rowconfigure(7, weight=1)
frmEntries.grid_rowconfigure(8, weight=1)
frmEntries.grid_rowconfigure(9, weight=1)
frmEntries.grid_rowconfigure(10, weight=1)
frmEntries.grid_rowconfigure(11, weight=1)

frmEntries.grid_columnconfigure(0, weight=1)
frmEntries.grid_columnconfigure(1, weight=20)
frmEntries.grid_columnconfigure(2, weight=20)
frmEntries.grid_columnconfigure(3, weight=20)
frmEntries.grid_columnconfigure(4, weight=1)

frmEntries.grid(row=0, column=0, columnspan=4, sticky="ENW")



# Create single row frame across the middle (control buttons go here)
bgButtons = "gray1"
frmButtons = tk.Frame(master=window, width=150, height=40, relief=tk.RAISED, borderwidth=5, bg=gray)
frmButtons.grid_rowconfigure(0, weight=1)
frmButtons.grid_rowconfigure(1, weight=1)
frmButtons.grid_rowconfigure(2, weight=1)
frmButtons.grid_columnconfigure(0, weight=1)
frmButtons.grid_columnconfigure(1, weight=1)
frmButtons.grid_columnconfigure(2, weight=1)
frmButtons.grid_columnconfigure(3, weight=1)
frmButtons.grid_columnconfigure(4, weight=1)
#frmButtons.grid(row=1, column=0, rowspan=2, columnspan=4, sticky="ENW")
frmButtons.grid(row=1, column=0, rowspan=3, columnspan=4, sticky="ENW")




# Create frame at the bottom (listbox goes here)
# 2 rows (height=1, 8), 2 columns(width=1, 3)
bgBottom = "#C0C0C0"
frmBottom = tk.Frame(master=window, width=100, relief=tk.RAISED, borderwidth=5, bg=gray)
frmBottom.grid(row=2, column=0, sticky="WSE", columnspan=4, pady=2)

frmBottom.grid_rowconfigure(0, weight=1)
frmBottom.grid_rowconfigure(1, weight=1)
frmBottom.grid_rowconfigure(2, weight=1)
frmBottom.grid_rowconfigure(3, weight=1)
frmBottom.grid_rowconfigure(4, weight=1)
frmBottom.grid_rowconfigure(5, weight=1)
frmBottom.grid_columnconfigure(0, weight=1)
frmBottom.grid_columnconfigure(1, weight=1)
frmBottom.grid_columnconfigure(2, weight=1)
frmBottom.grid_columnconfigure(3, weight=1)
frmBottom.grid_columnconfigure(4, weight=1)
frmBottom.grid_columnconfigure(5, weight=1)
frmBottom.grid_columnconfigure(6, weight=1)
                   

# Starting coordinates for top row buttons in top frame
# ******************************************************************
# Top Frame Widgets
# ******************************************************************
#
# font=("Helvetica", 12)
# font=("Courier New", 11)
# font=("Arial", 11)
# Entry for areasymbol filter

# Row 0
entFilter = tk.Entry(master=frmEntries, width=30, font=("Arial", 11))
entFilter.grid(row=0, column=0, rowspan=1, columnspan=2,  sticky=tk.W+tk.N+tk.S)
entFilter.bind("<FocusOut>", ValidateFilter)
b0 = Balloon(window.winfo_toplevel())
b0.bind_widget(entFilter, balloonmsg="Enter wildcard for Areasymbol")

# Label for areasymbol filter
lblFilter = tk.Label(master=frmEntries, text=" Enter areasymbol filter or asterik (*) for no filter", pady=5, background=gray)
lblFilter.grid(row=0, column=1, rowspan=2, columnspan=3, sticky="W")  # strange, but the rowspan=2 also affected the entFilter entry box and made it taller.

# Row 2
# Label for input folder box
lblFolder = tk.Label(master=frmEntries, text="Folder containing SSURGO downloads", pady=10, background=gray)
lblFolder.grid(row=3, column=0, columnspan=3, pady=1, sticky="W")

# Row 3
# Entry box for input folder
entFolder = tk.Entry(master=frmEntries, width=40, font=("Arial", 11))
entFolder.grid(row=4, column=0, columnspan=4, sticky="EW")
b1 = Balloon(window.winfo_toplevel())
b1.bind_widget(entFolder, balloonmsg="Enter SSURGO Download Folder")

# Button-Browser for input folder
iconFolder = tk.PhotoImage(file="folder_icon.png")
btnFolder = tk.Button(master=frmEntries, image=iconFolder, relief=tk.RAISED)
btnFolder.grid(row=4, column=3, sticky="E")
btnFolder.bind("<ButtonRelease-1>", GetFolder)
b2 = Balloon(window.winfo_toplevel())
b2.bind_widget(btnFolder, balloonmsg="Button Browser for SSURGO Download Folder")

# Row 4
# Label for input database
lblDBinput = tk.Label(master=frmEntries, text=" Input database", pady=10, background=gray)
lblDBinput.grid(row=5, column=0, columnspan=3, sticky="W")

# Create balloon object
#b = Balloon(window.winfo_toplevel())
#b.bind_widget(lblDBinput, balloonmsg="Name of input database \nbound to this button widget")


# Row 5
# Entry box for input database
entDBinput = tk.Entry(master=frmEntries, width = 40, font=("Arial", 11))
entDBinput.grid(row=6, column=0, columnspan=4, sticky="EW")
b3 = Balloon(window.winfo_toplevel())
b3.bind_widget(entDBinput, balloonmsg="Name of input database \nbound to this button widget")

# Button-Browser for input database
btnDBinput = tk.Button(master=frmEntries, image=iconFolder, relief=tk.RAISED)
btnDBinput.bind("<ButtonRelease-1>", GetInputDB)
btnDBinput.grid(row=6, column=3, sticky="E")
b4 = Balloon(window.winfo_toplevel())
b4.bind_widget(btnDBinput, balloonmsg="Button Browser for Input Database")

# Row 6
# Label for output database
lblDBoutput = tk.Label(master=frmEntries, text=" Output database", pady=10, background=gray)
lblDBoutput.grid(row=7, column=0, columnspan=3, sticky="W")

# Row 7
# Entry box for output database
entDBoutput = tk.Entry(master=frmEntries, width = 40, font=("Arial", 11))
entDBoutput.grid(row=8, column=0, columnspan=4, sticky="EW")
b5 = Balloon(window.winfo_toplevel())
b5.bind_widget(entDBoutput, balloonmsg="Text Name of Output Database")

# Button-Browser for output database
btnDBoutput = tk.Button(master=frmEntries, image=iconFolder, relief=tk.RAISED)
btnDBoutput.bind("<ButtonRelease-1>", SetOutputDB)
btnDBoutput.grid(row=8, column=3, sticky="E")
b6 = Balloon(window.winfo_toplevel())
b6.bind_widget(btnDBoutput, balloonmsg="Button Browser for Output Database")


# Listbox for output coordinate system
# crsList = tk.StringVar()
crsList = ["EPSG:4326", "EPSG:5070", ""]
lbxCRS = tk.Listbox(master=frmEntries, listvariable=crsList, width=25, height=3, selectmode='single', background=ltGray, selectbackground="green", exportselection=False, fg="black", font=("Arial", 11))  #  highlightcolor="red",
lbxCRS.grid(row=10, column=0, columnspan=1, sticky="W")
lbxCRS.bind("<ButtonRelease-1>", SetCRS)
b7 = Balloon(window.winfo_toplevel())
b7.bind_widget(lbxCRS, balloonmsg="Listbox with Output Coordinate System Options")

lblCRS = tk.Label(master=frmEntries, text="Output coordinate system", pady=40, background=gray)
lblCRS.grid(row=10, column=1, columnspan=2, sticky="W")

for item in range(len(crsList)): 
    lbxCRS.insert(tk.END, crsList[item]) 
    #lbxCRS.itemconfig(item, bg=ltGray)

lbxCRS.select_set(0)
SetCRS(None)

# Checkbox for overwrite existing data
cbxOverwrite = tk.Checkbutton(master=frmEntries, text="Overwrite existing data?", pady=10, background=gray)
cbxOverwrite.grid(row=11, column=0, sticky="W")
b7 = Balloon(window.winfo_toplevel())
b7.bind_widget(cbxOverwrite, balloonmsg="Checkbox Overwrite Existing Data")


# ******************************************************************
# Middle Frame Widgets (control buttons)
# ******************************************************************

# Button-Print. Prints selected values to console.
# frmButtons has 1 row, 5 columns
btnWidth = 13
btnOK = tk.Button(master=frmButtons, text="  Print", height=1, width=btnWidth, pady=5, bg=orange)
btnOK.grid(row=0, column=0)
btnOK.bind("<Button-1>", ShowSelected)
b10 = Balloon(window.winfo_toplevel())
b10.bind_widget(btnOK, balloonmsg="Button Print")

# Button-Select All. Select everything in listbox
btnWidth = 13
btnSelectAll = tk.Button(master=frmButtons, text="Select All", height=1, width=btnWidth, bg=orange)
btnSelectAll.grid(row=0, column=1)
btnSelectAll.bind("<Button-1>", SelectAll)
b11 = Balloon(window.winfo_toplevel())
b11.bind_widget(btnSelectAll, balloonmsg="Button Select All Survey Areas")

# Button-Clear Selection. Deselect everything in listbox.
btnWidth = 13
btnClearSelection = tk.Button(master=frmButtons, text="Clear Selection", height=1, width=btnWidth, bg=orange)
btnClearSelection.grid(row=0, column=2)
btnClearSelection.bind("<Button-1>", ClearSelection)
b12 = Balloon(window.winfo_toplevel())
b12.bind_widget(btnClearSelection, balloonmsg="Button Clear Selected Survey Areas")

# Button-Switch Selection. Switch selection in listbox.
btnWidth = 13
btnSwitchSelection = tk.Button(master=frmButtons, text="Switch Selection", height=1, width=btnWidth, bg=orange)
btnSwitchSelection.grid(row=0, column=3)
btnSwitchSelection.bind("<Button-1>", SwitchSelection)
b13 = Balloon(window.winfo_toplevel())
b13.bind_widget(btnSwitchSelection, balloonmsg="Button Switch Selected Survey Areas")

# Button-Quit. Closes menu.
btnWidth = 13
btnExit = tk.Button(master=frmButtons, text="   Quit", height=1, width=btnWidth, pady=5, bg=orange)
btnExit.grid(row=0, column=4)
btnExit.bind("<Button-1>", Close)
b14 = Balloon(window.winfo_toplevel())
b14.bind_widget(btnExit, balloonmsg="Button Quit")


# ******************************************************************
# Bottom Frame Widgets
# ******************************************************************
# 2 rows (height=1, 8), 2 columns(width=1, 3)
# Create the text label at the top of the second frame
# , font=("Helvetica", 12)
lblDownloads = tk.Label(master=frmBottom, text = "Select SSURGO Datasets to Import", padx=2, pady=2, background=gray)
lblDownloads.grid(row=0, column=0, columnspan=2, sticky="W")

# Create listbox in the bottom frame
downloadList = tk.StringVar()
lbxDownloads = tk.Listbox(master=frmBottom, listvariable=downloadList, width=15, height=20, selectmode='multiple', background=ltGray, selectbackground="green", exportselection=False,  fg="black", font=("Arial", 11))
lbxDownloads.grid(row=1, column=0, rowspan=4, columnspan=1, sticky="SW", pady=8)
lbxDownloads.bind("<ButtonRelease-1>", ShowSelected)
b15 = Balloon(window.winfo_toplevel())
b15.bind_widget(lbxDownloads, balloonmsg="ListBox SSURGO Downloads to Import")

# Label for selection count
lblText = tk.StringVar()
lblText.set("Set areasymbol filter and download folder to populate SSURGO dataset list")
lblCount = tk.Label(master=frmBottom, textvariable=lblText, anchor="w", width=60,padx=10, pady=0, background=gray)
lblCount.grid(row=1, column=1, columnspan=3, sticky="W")
b16 = Balloon(window.winfo_toplevel())
b16.bind_widget(lblCount, balloonmsg=lblText.get())


# Label for duplicate downloads (different folder names, same areasymbol)
lblDups = tk.Label(master=frmBottom, text="Init", anchor="w", width=40, padx=10, pady=0, background=gray)
lblDups.grid(row=2, column=1, columnspan=3, sticky="W")

# Label for diagnostic messages)
##lblMsg = tk.Label(master=frmBottom, text="No messages yet", anchor="w", width=40, padx=10, pady=10, background=gray)
##lblMsg.grid(row=4, column=1, columnspan=3, sticky="W")


window.mainloop() 
