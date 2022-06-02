import os, sys
import tkinter as tk
from tkinter import filedialog as fd
#from tkinter import ttk

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

# tkinter.filedialog.askdirectory()

# ******************************************************************
def ShowSelected(event):
    surveyAreas = []
    totalCnt = lbxDownloads.size()   # total count
    selectedSet = lbxDownloads.curselection()
    selCnt = len(selectedSet)

    if selCnt > 0:
        print("")
    
    for i in selectedSet:
        subFolder = lbxDownloads.get(i)
        surveyAreas.append(subFolder)

    msgCount = str(selCnt) + " of " + str(totalCnt) + " survey areas selected for processing"
    print(msgCount)
    lblCount.config(text=msgCount)
    
    for val in surveyAreas:
        print("\t", val)

    return

# ******************************************************************
def SelectClear(event):
    surveyAreas = []
    lbxDownloads.selection_clear(0, tk.END)
    totalCnt = lbxDownloads.size()
    selectedSet = lbxDownloads.curselection()
    selCnt = len(selectedSet)
    msgCount = str(selCnt) + " of " + str(totalCnt) + " survey areas selected for processing"

    lblCount.config(text=msgCount)
    print(msgCount)
    
    return

# ******************************************************************
def SelectAll(event):

    lbxDownloads.focus_set()
    
    lbxDownloads.select_set(0, tk.END)

    totalCnt = lbxDownloads.size()
    
    selectedSet = lbxDownloads.curselection()
    
    selCnt = len(selectedSet)
    
    msgCount = str(selCnt) + " of " + str(totalCnt) + " survey areas selected for processing"
    #lblCount.focus_set()
    lblCount.config(text=msgCount)
    print(msgCount)


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
    msgCount = "No survey areas selected for processing (ValidateFilter)"
    lblCount.config(text=msgCount)
    
    if newWildCard and inputFolder:
        # Get listing of SSURGO downloads
        GetDownloads()

    else:
        # Should I remove all items from the current listbox?
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

##    color = "#ecedf3" # light gray
##    color = "#bdc1d6" # medium gray
##    color = "#ffa500" # orange
##    color = "#00daff" # cyan
##    color = "#00cc84" # medium green

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
      #self.params[2].filter.list = surveyList
      lbxDownloads.delete(0, tk.END)

      # Add the list of values to the listbox
      for item in range(len(surveyList)): 
          lbxDownloads.insert(tk.END, surveyList[item]) 
          lbxDownloads.itemconfig(item, bg=orange)

      if len(surveyList) == 1:
          #self.params[2].values = surveyList

          # Add the list of values to the listbox
          for item in range(len(surveyList)): 
              lbxDownloads.insert(tk.END, countryList[item]) 
              lbxDownloads.itemconfig(item, bg=orange)  # supposed to be gray

          lbxDownloads.focus_set()
          totalCnt = lbxDownloads.size()
          msgCount = "0 of " + str(totalCnt) + " survey areas selected for processing"
          lblCount.config(text=msgCount)

    else:
        lbxDownloads.insert(tk.END, "No Data")

    if len(dupList) > 0:
        msgDups = str(len(dupList)) + " apparent duplicate downloads found: " + ", ".join(dupList)
        #dupWidth = int(round((1.2 * len(msgDups)), 0))
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
    selCnt = len(selectedSet)
    
    for i in selectedSet:
        crs = lbxCRS.get(i)

    if crs == "":
        crs = "EPSG:4326"
        
    msgCRS = "Output coordinate system: " + crs
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

window = tk.Tk()                           # Menu frame
window.title('SSURGO Data Picker - By Areasymbol')          # Title bar for menu
window.geometry('600x825')                 # Menu size
var = tk.StringVar()                       # Not sure how this is being used, but doesn't work without it

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
frmBottom.grid(row=2, column=0, sticky="WSE", columnspan=4)
#frmBottom.grid(row=2, column=1)
#frmBottom.grid(row=0, column=2)

frmBottom.grid_rowconfigure(0, weight=2)
frmBottom.grid_rowconfigure(1, weight=2)
frmBottom.grid_rowconfigure(2, weight=2)
frmBottom.grid_rowconfigure(3, weight=2)
frmBottom.grid_rowconfigure(4, weight=2)
frmBottom.grid_rowconfigure(5, weight=2)
frmBottom.grid_columnconfigure(0, weight=1)
frmBottom.grid_columnconfigure(1, weight=1)
frmBottom.grid_columnconfigure(2, weight=1)
frmBottom.grid_columnconfigure(3, weight=1)
frmBottom.grid_columnconfigure(4, weight=1)
frmBottom.grid_columnconfigure(5, weight=1)
frmBottom.grid_columnconfigure(6, weight=1)
                   

# Starting coordinates for top row buttons in top frame
##row1X = 5
##btnX = 1
##row1Y = 1
##row2Y = 60
##row3Y = 150

# ******************************************************************
# Top Frame Widgets
# ******************************************************************
#
# font=("Helvetica", 12)
# font=("Courier New", 11)
# font=("Arial", 11)
# Entry for areasymbol filter

fnt = '("Courier New", 11)'
# Row 0
entFilter = tk.Entry(master=frmEntries, width=30, font=("Arial", 11))
entFilter.grid(row=0, column=0, rowspan=1, columnspan=2,  sticky=tk.W+tk.N+tk.S)
entFilter.bind("<FocusOut>", ValidateFilter)

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

# Button-Browser for input folder
iconFolder = tk.PhotoImage(file="folder_icon.png")
btnFolder = tk.Button(master=frmEntries, image=iconFolder, relief=tk.RAISED)
btnFolder.grid(row=4, column=3, sticky="E")
btnFolder.bind("<ButtonRelease-1>", GetFolder)

# Row 4
# Label for input database
lblDBinput = tk.Label(master=frmEntries, text=" Input database", pady=10, background=gray)
lblDBinput.grid(row=5, column=0, columnspan=3, sticky="W")

# Row 5
# Entry box for input database
entDBinput = tk.Entry(master=frmEntries, width = 40, font=("Arial", 11))
entDBinput.grid(row=6, column=0, columnspan=4, sticky="EW")

# Button-Browser for input database
btnDBinput = tk.Button(master=frmEntries, image=iconFolder, relief=tk.RAISED)
btnDBinput.bind("<ButtonRelease-1>", GetInputDB)
btnDBinput.grid(row=6, column=3, sticky="E")

# Row 6
# Label for output database
lblDBoutput = tk.Label(master=frmEntries, text=" Output database", pady=10, background=gray)
lblDBoutput.grid(row=7, column=0, columnspan=3, sticky="W")

# Row 7
# Entry box for output database
entDBoutput = tk.Entry(master=frmEntries, width = 40, font=("Arial", 11))
entDBoutput.grid(row=8, column=0, columnspan=4, sticky="EW")

# Button-Browser for output database
btnDBoutput = tk.Button(master=frmEntries, image=iconFolder, relief=tk.RAISED)
btnDBoutput.bind("<ButtonRelease-1>", SetOutputDB)
btnDBoutput.grid(row=8, column=3, sticky="E")


# Listbox for output coordinate system
crsList = tk.StringVar()
lbxCRS = tk.Listbox(master=frmEntries, listvariable=crsList, width=25, height=3, selectmode='single', background="yellow", foreground="white", font=("Arial", 11))
lbxCRS.grid(row=10, column=0, columnspan=1, sticky="W")
lbxCRS.bind("<ButtonRelease-1>", SetCRS)

# Label for output coordinate system
lblCRS = tk.Label(master=frmEntries, text="Output coordinate system", pady=40, background=gray)
lblCRS.grid(row=10, column=1, columnspan=2, sticky="W")

# Populate listbox for output coordinate system
# Add the list of values to the listbox
crsList = ["EPSG:4326", "EPSG:5070", ""]

for item in range(len(crsList)): 
    lbxCRS.insert(tk.END, crsList[item]) 
    lbxCRS.itemconfig(item, bg=ltGray)

lbxCRS.select_set(0)
SetCRS(None)

# Checkbox for overwrite existing data
cbxOverwrite = tk.Checkbutton(master=frmEntries, text="Overwrite existing data?", pady=10, background=gray)
cbxOverwrite.grid(row=11, column=0, sticky="W")



# ******************************************************************
# Middle Frame Widgets (control buttons)
# ******************************************************************

# Button-Print. Prints selected values to console.
# frmButtons has 1 row, 5 columns
btnWidth = 12
btnOK = tk.Button(master=frmButtons, text="  Print", height=1, width=btnWidth, pady=5)
btnOK.grid(row=0, column=0)
btnOK.bind("<Button-1>", ShowSelected)

# Button-Select All. Select everything in listbox
btnWidth = 12
btnSelectAll = tk.Button(master=frmButtons, text="Select All", height=1, width=btnWidth)
btnSelectAll.grid(row=0, column=1)
btnSelectAll.bind("<Button-1>", SelectAll)

# Button-Clear Selection. Deselect everything in listbox.
btnWidth = 12
btnClearSelection = tk.Button(master=frmButtons, text="Clear Selection", height=1, width=btnWidth)
btnClearSelection.grid(row=0, column=2)
btnClearSelection.bind("<Button-1>", SelectClear)

# Button-Quit. Closes menu.
btnWidth = 12
btnExit = tk.Button(master=frmButtons, text="   Quit", height=1, width=btnWidth, pady=5)
btnExit.grid(row=0, column=3)
btnExit.bind("<Button-1>", Close)



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
lbxDownloads = tk.Listbox(master=frmBottom, listvariable=downloadList, width=15, height=20, selectmode='multiple', background=ltGray, fg="black", selectbackground="red", highlightcolor="red", font=("Arial", 11))
lbxDownloads.grid(row=1, column=0, rowspan=4, columnspan=1, sticky="SW")
#lbxDownloads.configure(background="yellow", foreground="red", font=("Arial", 11))
lbxDownloads.bind("<ButtonRelease-1>", ShowSelected)

# Label for selection count
lblCount = tk.Label(master=frmBottom, text="Init", anchor="w", width=40,padx=10, pady=10, background=gray)
lblCount.grid(row=2, column=1, columnspan=3, sticky="W")

# Label for duplicate downloads (different folder names, same areasymbol)
lblDups = tk.Label(master=frmBottom, text="Init", anchor="w", width=40, padx=10, pady=10, background=gray)
lblDups.grid(row=3, column=1, columnspan=3, sticky="W")

window.mainloop() 
