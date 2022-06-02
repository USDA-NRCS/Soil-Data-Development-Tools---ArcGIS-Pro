import os
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
    selectedSet = lbxDownloads.curselection()

    if len(selectedSet) > 0:
        print("")
    
    for i in selectedSet:
        subFolder = lbxDownloads.get(i)
        surveyAreas.append(subFolder)
        
    for val in surveyAreas:
        print("\t", val)

    msgCount = str(len(surveyAreas)) + " survey areas selected for processing"
    print("\n", str(len(surveyAreas)), "survey areas selected for processing")
    lblCount.config(text=msgCount)

    return

# ******************************************************************
def SelectClear(event):
    surveyAreas = []
    lbxDownloads.selection_clear(0, tk.END)
    selectedSet = lbxDownloads.curselection()

    if len(selectedSet) == 0:
        msgCount = "No survey areas selected for processing"

    else:
        msgCount = str(len(selectedSet)) + " survey areas selected for processing"
      
    lblCount.config(text=msgCount)
    #print("Cleared set count: ", str(len(surveyAreas)))
    
    return

# ******************************************************************
def SelectAll(event):
    States = []
    lbxDownloads.focus_set()
    cnt = lbxDownloads.size()
    lbxDownloads.select_set(0, tk.END)
    selectedSet = lbxDownloads.curselection()
    print("Selected set count: ", str(len(selectedSet)))
    msgCount = str(len(selectedSet)) + " survey areas selected for processing"
    lblCount.config(text=msgCount)

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
    msgCount = "No survey areas selected for processing"
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

    color = "#ecedf3" # light gray
    color = "#bdc1d6" # medium gray
    color = "#ffa500" # orange
    color = "#00daff" # cyan
    color = "#00cc84" # medium green

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
          lbxDownloads.itemconfig(item, bg=color)

      if len(surveyList) == 1:
          #self.params[2].values = surveyList

          # Add the list of values to the listbox
          for item in range(len(surveyList)): 
              lbxDownloads.insert(tk.END, countryList[item]) 
              lbxDownloads.itemconfig(item, bg=color)  # supposed to be gray

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
def Close(event):
    window.destroy()
    
    return
  
# ******************************************************************
# ******************************************************************
# main
# ******************************************************************

window = tk.Tk()                           # Menu frame
window.title('SSURGO Data Picker - By Areasymbol')          # Title bar for menu
window.geometry('500x600')                 # Menu size
var = tk.StringVar()                       # Not sure how this is being used, but doesn't work without it

# assortment of colors for backgrounds
gray = "#C0C0C0"

window.grid_rowconfigure(0, weight=10)      # entries frame
window.grid_rowconfigure(1, weight=2)      # button frame
window.grid_rowconfigure(2, weight=20)     # listbox and status messages

window.grid_columnconfigure(0, weight=8)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)
window.grid_columnconfigure(3, weight=1)


# Create frame at the top (entry widgets go here)
# if not specified with rowconfigure, height of a row will match tallest grid cell
# if not specified with columnconfigure, width of a column will be max of widget widths
#
bgEntries = "cyan"
frmEntries = tk.Frame(master=window, width=150, height=150, relief=tk.RAISED, borderwidth=5, bg=gray)


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

frmEntries.grid_columnconfigure(0, weight=1)
frmEntries.grid_columnconfigure(1, weight=20)
frmEntries.grid_columnconfigure(2, weight=20)
frmEntries.grid_columnconfigure(3, weight=20)
frmEntries.grid_columnconfigure(4, weight=1)

frmEntries.grid(row=0, column=0, columnspan=4, sticky="ENW")



# Create single row frame across the middle (control buttons go here)
bgButtons = "gray1"
frmButtons = tk.Frame(master=window, width=150, height=40, relief=tk.RAISED, borderwidth=5, bg=gray)
frmButtons.grid_rowconfigure(1, weight=1)
frmButtons.grid_columnconfigure(0, weight=1)
frmButtons.grid_columnconfigure(1, weight=1)
frmButtons.grid_columnconfigure(2, weight=1)
frmButtons.grid_columnconfigure(3, weight=1)
frmButtons.grid_columnconfigure(4, weight=1)

frmButtons.grid(row=1,column=0, sticky="ENW")




# Create frame at the bottom (listbox goes here)
# 2 rows (height=1, 8), 2 columns(width=1, 3)
bgBottom = "#C0C0C0"
frmBottom = tk.Frame(master=window, width=100, relief=tk.RAISED, borderwidth=5, bg=gray)
frmBottom.grid(row=2, column=0, sticky="WSE", columnspan=4)
#frmBottom.grid(row=2, column=1)
#frmBottom.grid(row=0, column=2)

frmBottom.grid_rowconfigure(0, weight=1)
frmBottom.grid_rowconfigure(1, weight=8)
frmBottom.grid_columnconfigure(0, weight=1)
frmBottom.grid_columnconfigure(1, weight=3)
                   

# Starting coordinates for top row buttons in top frame
row1X = 5
btnX = 1
row1Y = 1
row2Y = 60
row3Y = 150

# ******************************************************************
# Top Frame Widgets
# ******************************************************************

# Entry for areasymbol filter
entFilter = tk.Entry(master=frmEntries, width = 30)
entFilter.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="NW")
entFilter.bind("<FocusOut>", ValidateFilter)

# Label for areasymbol filter
lblFilter = tk.Label(master=frmEntries, text="Enter areasymbol filter or asterik (*) for no filter")
lblFilter.grid(row=0, column=2, rowspan=2, columnspan=3, sticky="W")

# Label for input folder box
lblFolder = tk.Label(master=frmEntries, text="Folder containing SSURGO downloads")
lblFolder.grid(row=2, column=0, columnspan=3, pady=1, sticky="W")

# Entry box for input folder
entFolder = tk.Entry(master=frmEntries, width = 40)
entFolder.grid(row=3, column=0, columnspan=4, sticky="EW")

# Button-Browser for input folder
iconFolder = tk.PhotoImage(file="folder_icon.png")
btnFolder = tk.Button(master=frmEntries, image=iconFolder, relief=tk.RAISED)
btnFolder.grid(row=3, column=3, sticky="E")
btnFolder.bind("<ButtonRelease-1>", GetFolder)

# Label for input database
lblDBinput = tk.Label(master=frmEntries, text="Input database")
lblDBinput.grid(row=4, column=0, columnspan=3, sticky="W")

# Entry box for input database
entDBinput = tk.Entry(master=frmEntries, width = 40)
entDBinput.grid(row=5, column=0, columnspan=4, sticky="EW")

# Button-Browser for input database
btnDBinput = tk.Button(master=frmEntries, image=iconFolder, relief=tk.RAISED)
btnDBinput.bind("<ButtonRelease-1>", GetFolder)
btnDBinput.grid(row=5, column=3, sticky="E")


# Label for output database
lblDBoutput = tk.Label(master=frmEntries, text="Output database")
lblDBoutput.grid(row=6, column=0, columnspan=3, sticky="W")

# Entry box for output database
entDBoutput = tk.Entry(master=frmEntries, width = 40)
entDBoutput.grid(row=7, column=0, columnspan=4, sticky="EW")

# Button-Browser for output database
btnDBoutput = tk.Button(master=frmEntries, image=iconFolder, relief=tk.RAISED)
btnDBoutput.bind("<ButtonRelease-1>", GetFolder)
btnDBoutput.grid(row=7, column=3, sticky="E")

# Checkbox for overwrite existing data
cbxOverwrite = tk.Checkbutton(master=frmEntries, text="Overwrite existing data?")
cbxOverwrite.grid(row=8, column=0, sticky="W")



# ******************************************************************
# Middle Frame Widgets (control buttons)
# ******************************************************************

# Button-Print. Prints selected values to console.
# frmButtons has 1 row, 5 columns
btnWidth = 5
btnOK = tk.Button(master=frmButtons, text="Print", height=1, width=btnWidth)
btnOK.grid(row=0, column=0)
btnOK.bind("<Button-1>", ShowSelected)

# Button-Select All. Select everything in listbox
btnWidth = 11
btnSelectAll = tk.Button(master=frmButtons, text="Select All", height=1, width=btnWidth)
btnSelectAll.grid(row=0, column=1)
btnSelectAll.bind("<Button-1>", SelectAll)

# Button-Clear Selection. Deselect everything in listbox.
btnWidth = 11
btnClearSelection = tk.Button(master=frmButtons, text="Clear Selection", height=1, width=btnWidth)
btnClearSelection.grid(row=0, column=2)
btnClearSelection.bind("<Button-1>", SelectClear)

# Button-Quit. Closes menu.
btnWidth = 5
btnExit = tk.Button(master=frmButtons, text="Quit", height=1, width=btnWidth)
btnExit.grid(row=0, column=3)
btnExit.bind("<Button-1>", Close)



# ******************************************************************
# Bottom Frame Widgets
# ******************************************************************
# 2 rows (height=1, 8), 2 columns(width=1, 3)
# Create the text label at the top of the second frame
# , font=("Helvetica", 12)
lblDownloads = tk.Label(master=frmBottom, text = "Select SSURGO Downloads to Import", padx=2, pady=2)
lblDownloads.grid(row=0, column=0, columnspan=2)

# Create listbox in the bottom frame
downloadList = tk.StringVar()
lbxDownloads = tk.Listbox(master=frmBottom, listvariable=downloadList, width=30, height=20, selectmode='multiple')
lbxDownloads.grid(row=1, column=0)
lbxDownloads.bind("<ButtonRelease-1>", ShowSelected)

# Label for selection count
lblCount = tk.Label(master=frmBottom, text="No survey areas selected", anchor="w", width=30)
lblCount.grid(row=2, column=1)

# Label for duplicate downloads (different folder names, same areasymbol)
lblDups = tk.Label(master=frmBottom, text="", anchor="w", width=40)
lblDups.grid(row=3, column=1)

window.mainloop() 
